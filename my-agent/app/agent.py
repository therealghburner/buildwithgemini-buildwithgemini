# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


MODEL = "gemini-2.5-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


from app.firestore_backend import (
    get_user_profile,
    update_user_profile,
    list_user_profiles,
)
import os
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

AGENT_ENGINE_RESOURCE = os.getenv(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/603917225018/locations/us-central1/reasoningEngines/7226229561522913280"
)

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE
)

from app.db import ReadOnlyDatabaseManager
try:
    db_schema = ReadOnlyDatabaseManager.get_schema()
except Exception:
    db_schema = "(Schema not available locally)"

def query_purchase_orders(query_sql: str) -> list[dict]:
    """Executes a read-only SQL query against the SQLite Purchase Order database and returns the results.
    
    Use this to retrieve list of purchase orders, count purchase orders, group spending by department,
    or look up purchase order details. Only read-only SELECT/WITH queries are allowed.
    
    Args:
        query_sql: The raw, read-only SQL SELECT or WITH query to run.
        
    Returns:
        A list of dictionaries representing the query results.
    """
    from app.db import ReadOnlyDatabaseManager
    return ReadOnlyDatabaseManager.execute_query(query_sql)


from app.tools import (
    get_vendor_risk_score,
    flag_po_for_audit,
    export_po_report_csv,
)
from app.rag_tool import search_procurement_policies

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Lead Purchasing, Procurement & Compliance Analytics Agent. "
        "Your primary job is to answer user questions about corporate purchase orders, spend analytics, "
        "and vendor compliance using the SQLite Purchase Order database and the procurement policies RAG corpus. "
        "Always use the `query_purchase_orders` tool to count, filter, aggregate, and lookup purchase orders. "
        "For example, to find how many POs exist, run 'SELECT COUNT(*) FROM purchase_orders'. "
        "The database includes granular line item quantity tracking in `po_items` (`quantity`, `received_quantity`, `shipped_quantity`, `transit_quantity`) to support queries about order delivery ratios, partial receipts, and shipments. "
        "Do NOT assume or make up numbers; always query the real database. "
        "Database Schema:\n"
        f"{db_schema}\n\n"
        "You also have a procurement policy RAG search tool (`search_procurement_policies`) to lookup official rules, approval threshold tiers, "
        "and vendor SLAs. "
        "For vendor performance and risk analytics, call `get_vendor_risk_score`. "
        "To flag suspicious or high-value purchase orders for compliance auditing, call `flag_po_for_audit`. "
        "To export SQL queries as a downloadable report, call `export_po_report_csv`. "
        "CRITICAL SAFETY & PERSONALIZATION INSTRUCTION: "
        "Always remember, track, and strictly observe all stated user allergies (food, drug, environmental), "
        "dietary restrictions, and health preferences from memory across conversations. "
        "Before recommending food, recipes, dining locations, or medications, verify against "
        "all remembered user allergies to ensure full safety. "
        "Use the Firestore tools (get_user_profile, update_user_profile, list_user_profiles) "
        "to manage user profile data, health records, allergies, and preferences. "
        "You also have a secure Python code execution sandbox to perform calculations or run Python code."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        PreloadMemoryTool(),
        get_user_profile,
        update_user_profile,
        list_user_profiles,
        query_purchase_orders,
        get_vendor_risk_score,
        flag_po_for_audit,
        export_po_report_csv,
        search_procurement_policies,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


