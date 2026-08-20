import os
import json
from typing import TypedDict, Optional, List, Any
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END

from db import ReadOnlyDatabaseManager

load_dotenv()

class AgentState(TypedDict):
    user_query: str
    schema_info: str
    generated_sql: Optional[str]
    query_result: Optional[List[dict]]
    error_message: Optional[str]
    retry_count: int
    final_answer: Optional[str]
    messages: List[BaseMessage]

MAX_RETRIES = 3

def get_llm():
    """Initializes LLM provider (OpenAI or Google GenAI/Vertex AI)."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("your_"):
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model_name, temperature=0.0)
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-dcb3c6d873b1")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        return ChatGoogleGenerativeAI(
            model=model_name,
            project=project_id,
            location=location,
            temperature=0.0
        )

# --- Graph Nodes ---

def inspect_schema_node(state: AgentState) -> dict:
    """Inject database schema into graph state."""
    schema = ReadOnlyDatabaseManager.get_schema()
    return {"schema_info": schema}

def generate_sql_node(state: AgentState) -> dict:
    """Generate SQL statement based on user question and database schema."""
    llm = get_llm()

    error_context = ""
    if state.get("error_message"):
        error_context = f"\n\nPrevious attempt failed with error:\n{state['error_message']}\nPlease correct the SQL query."

    prompt = f"""You are an expert SQL Data Analyst working with a SQLite Purchase Order database.
Your job is to generate a single, valid, optimized, read-only SQL SELECT query to answer the user's question.

CRITICAL RULES:
1. Output ONLY the raw SQL statement. Do not wrap in markdown code blocks like ```sql ... ```.
2. Only use SELECT or WITH clauses. No modification queries allowed.
3. Handle dates properly (dates stored as 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD').

Database Schema:
{state['schema_info']}

User Question: {state['user_query']}
{error_context}

SQL Query:"""

    response = llm.invoke([HumanMessage(content=prompt)])
    sql = str(response.content).strip()

    # Strip markdown code blocks if generated
    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    return {"generated_sql": sql}

def validate_and_execute_node(state: AgentState) -> dict:
    """Validates read-only policy and executes SQL query."""
    sql = state.get("generated_sql", "")
    retry_count = state.get("retry_count", 0)

    try:
        # Step 1: Guardrail Check
        if not ReadOnlyDatabaseManager.validate_read_only(sql):
            return {
                "error_message": "Guardrail Error: Generated query violated read-only restriction.",
                "retry_count": retry_count + 1
            }

        # Step 2: Query Execution
        results = ReadOnlyDatabaseManager.execute_query(sql)
        return {
            "query_result": results,
            "error_message": None
        }
    except Exception as e:
        return {
            "error_message": f"Execution Error: {str(e)}",
            "retry_count": retry_count + 1
        }

def synthesize_answer_node(state: AgentState) -> dict:
    """Synthesize database query results into clear, analytical insight."""
    llm = get_llm()

    results = state.get("query_result", [])
    result_str = json.dumps(results[:100], indent=2) # limit sample size for prompt context
    total_rows = len(results)

    prompt = f"""You are a Lead Purchasing & Procurement Analyst.
Analyze the following query results and provide a clear, business-focused answer to the user's question.

User Question: {state['user_query']}
SQL Query Used: {state['generated_sql']}
Total Rows Returned: {total_rows}

Data Sample (first 100 rows):
{result_str}

Provide a comprehensive, concise explanation with key figures, tables, or metrics where appropriate."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": str(response.content)}

# --- Conditional Edge Routing ---

def should_retry_or_finish(state: AgentState) -> str:
    """Determines whether to retry SQL generation or proceed to synthesis."""
    if state.get("error_message"):
        if state.get("retry_count", 0) >= MAX_RETRIES:
            return "max_retries_exceeded"
        return "retry_sql"
    return "synthesize"

def max_retries_exceeded_node(state: AgentState) -> dict:
    """Fallback node if SQL generation repeatedly fails."""
    return {
        "final_answer": f"Unable to fulfill request after multiple retries due to error: {state.get('error_message')}"
    }

# --- Compile State Graph (LangGraph 0.2+) ---

def build_po_agent_graph():
    builder = StateGraph(AgentState)

    # 1. Register Nodes
    builder.add_node("inspect_schema", inspect_schema_node)
    builder.add_node("generate_sql", generate_sql_node)
    builder.add_node("validate_and_execute", validate_and_execute_node)
    builder.add_node("synthesize_answer", synthesize_answer_node)
    builder.add_node("max_retries_exceeded", max_retries_exceeded_node)

    # 2. Register Edges with START and END
    builder.add_edge(START, "inspect_schema")
    builder.add_edge("inspect_schema", "generate_sql")
    builder.add_edge("generate_sql", "validate_and_execute")

    # 3. Conditional Edge for Self-Correction Loop
    builder.add_conditional_edges(
        "validate_and_execute",
        should_retry_or_finish,
        {
            "synthesize": "synthesize_answer",
            "retry_sql": "generate_sql",
            "max_retries_exceeded": "max_retries_exceeded"
        }
    )

    builder.add_edge("synthesize_answer", END)
    builder.add_edge("max_retries_exceeded", END)

    return builder.compile()
