# 🚀 Getting Started & Recovery Guide: Procurement & Compliance Analytics Agent

Welcome to the **Procurement & Compliance Analytics Agent** setup and recovery manual. This document serves as your complete "memory footprint" and step-by-step runbook. Whether you are continuing development, cloning this repository to a completely new machine, or recovering from a system reset, follow these exact instructions to get up and running without struggling.

---

## 🛠️ Table of Contents
1. [📋 Prerequisites & System Requirements](#1-prerequisites)
2. [🔑 Google Cloud Authentication & Credentials](#2-authentication)
3. [📂 Repository Layout](#3-repository-layout)
4. [⚡ Local Development Quickstart (Start in 60 seconds)](#4-local-development)
5. [📦 Database Schema & Real-Time Quantity Tracking](#5-database-schema)
6. [☁️ Deploying Agent Updates to Vertex AI (Agent Platform)](#6-cloud-deployments)
7. [🩺 Common Troubleshooting Checklist](#7-troubleshooting)

---

<a name="1-prerequisites"></a>
## 1. 📋 Prerequisites
Ensure your local system or development environment has the following components installed:
* **Python 3.10 to Python 3.13** (Recommended: Python 3.11/3.12)
* **[uv](https://github.com/astral-sh/uv)** (or standard `pip` for Python dependency management)
* **[Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install)**
* **[`agents-cli`](https://google.github.io/agents-cli/guide/getting-started/)** (Google ADK CLI)
  ```bash
  npm install -g @google/agents-cli
  ```

---

<a name="2-authentication"></a>
## 2. 🔑 Google Cloud Authentication
To query the live Agent Runtime on Vertex AI or interact with RAG Engine and Firestore, your local terminal **must** be authenticated with the correct Google Cloud Project credentials.

Run these two commands in your terminal and complete the browser device flow:
```bash
# 1. Log in to your Google Account
gcloud auth login

# 2. Establish Application Default Credentials (ADC) for the local FastAPI proxy
gcloud auth application-default login
```

Set your active Google Cloud project ID (replace with your active Qwiklabs or personal project ID):
```bash
gcloud config set project qwiklabs-gcp-03-dcb3c6d873b1
```

### 👥 Collaborator Handoff: Sharing vs. Brand New GCP Projects
If you are handing this repository over to a collaborator or a new developer, their setup details will depend on which Google Cloud Project they intend to target:

#### Scenario A: Sharing Your Active Google Cloud Project (Easiest)
If they are authorized to work in the **same Google Cloud Project** as you:
1. They authenticate their terminal using `gcloud auth login` and `gcloud auth application-default login`.
2. They set their active project: `gcloud config set project qwiklabs-gcp-03-dcb3c6d873b1`.
3. They follow the local Quickstart. **Everything will work out-of-the-box instantly!**

#### Scenario B: Deploying in a Brand New Google Cloud Project
If they want to run the agent in a **completely separate, brand new Google Cloud Project**, they must configure their own project-level bindings:
1. **Firestore**: Enable Firestore on their new project (collection seeding is fully automatic on their first chat message).
2. **Memory Bank**: Deploy a managed Memory Bank using the pre-configured instructions in `.agents/skills/setup-memory-bank/` and export their own `MEMORY_BANK_ID` env variable in their terminal session.
3. **RAG Engine Corpus**: Create a Serverless RAG corpus using instructions in `.agents/skills/build-rag/` and update the RAG Corpus ID inside `my-agent/app/rag_tool.py`.
4. Run `agents-cli deploy` once from `my-agent/` to instantiate their own isolated reasoning engine container under their project.

---

<a name="3-repository-layout"></a>
## 3. 📂 Repository Layout
Here is the core directory layout of the application you cloned:

```text
buildwithgemini/
├── my-agent/                  # 🤖 ADK Agent Package
│   ├── app/
│   │   ├── agent.py           # Core agent prompt instructions and tool registrations
│   │   ├── db.py              # SQLite Read-Only database driver & SQL AST safety validator
│   │   ├── tools.py           # Analytical tools (vendor risk, po flags, csv export)
│   │   ├── rag_tool.py        # Vertex AI Serverless RAG Engine policy search
│   │   ├── firestore_backend.py # Syncs user profiles with Firestore DB
│   │   ├── a2ui_utils.py      # Lifecycle callback converting Python objects to A2UI Cards
│   │   └── purchase_orders.db # 10k purchase orders (now correctly bundled inside app package!)
│   └── pyproject.toml         # Python environment packaging
│
├── frontend/                  # 🎨 FastAPI Chat Proxy Web Application
│   ├── main.py                # FastAPI endpoints, A2A streaming client, and nested A2UI card parser
│   ├── requirements.txt       # Frontend dependencies
│   └── static/                # HTML5 presentation layers (Chat Interface, Custom Styles)
│
├── po_agent/                  # 📊 SQL Schema Generator & Seed DB Simulator
│   ├── generate_db.py         # Advanced schema builder (populates received & shipped quantities)
│   └── tools.py               # Local mock analytical tools
│
├── project_brief.md           # 🏗️ Full enterprise architecture and lifecycle flow diagrams
└── GETTING_STARTED.md         # 📖 Setup, launch, and disaster recovery guide (This document!)
```

---

<a name="4-local-development"></a>
## 4. ⚡ Local Development Quickstart (Start in 60 seconds)

### Step 1: Install Dependencies
Open your terminal and run the setup steps:

1. **Configure the agent package**:
   ```bash
   cd my-agent
   uv pip install -e .
   uv pip install faker
   ```

2. **Configure the frontend proxy**:
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

### Step 2: Configure Environment Variables
You need to point the local web proxy server to your live Reasoning Engine (Agent Runtime) ID. Export these parameters in your terminal session:

```bash
# 1. Point to your live deployed agent resource name
export AGENT_ENGINE_RESOURCE_NAME="projects/603917225018/locations/us-east1/reasoningEngines/5056926655025512448"

# 2. Declare your agent directory
export AGENT_DIRECTORY="app"

# 3. Specify the local network port
export PORT=8080
```

### Step 3: Launch the Proxy Server
From the `frontend/` directory, start the FastAPI proxy application:
```bash
python3 main.py
```

### Step 4: Open Browser
Go to your web browser and open:
👉 **[http://localhost:8080](http://localhost:8080)**

Type your query in the chat window, e.g., *"Show me the first PO"* or *"How many POs are 50% received?"*, and watch the visual A2UI cards render instantly!

---

<a name="5-database-schema"></a>
## 5. 📦 Database Schema & Real-Time Quantity Tracking
To support partial receiving and order shipping analytics, the database contains three granular item-level tracking fields inside the `po_items` table.

### The Upgraded Schema:
* `quantity`: The total ordered volume.
* `received_quantity`: Quantity received at warehouse (0 to quantity).
* `shipped_quantity`: Quantity shipped from the vendor (0 to quantity).
* `transit_quantity`: Quantity currently in-transit (shipped - received).

### Regenerating or Editing the Database:
If you need to change data parameters, add vendors, or scale the record count:
1. Edit `/po_agent/generate_db.py` to change seeding logic or status weights.
2. Run the generator script:
   ```bash
   cd po_agent
   # Run using the python virtualenv containing faker
   python3 generate_db.py
   ```
3. Copy the updated database over to the agent package:
   ```bash
   cp purchase_orders.db ../my-agent/app/purchase_orders.db
   ```
4. Redeploy the agent to publish the new database (see Section 6).

---

<a name="6-cloud-deployments"></a>
## 6. ☁️ Deploying Agent Updates to Vertex AI (Agent Platform)
Whenever you make updates to prompt instructions, custom tools, or change the embedded database file, you must deploy the updated package to Google Cloud.

```bash
cd my-agent

# Execute the zero-friction agents-cli deployment command
agents-cli deploy --no-confirm-project
```

> [!NOTE]
> **Vertex AI Rolling Deploy Rollout Lag**: It takes approximately 1 to 2 minutes for Vertex AI to roll out container updates over older active container pools. When querying immediately post-deployment, you might temporarily hit an old pool replica. Give it up to 120 seconds to settle fully.

---

<a name="7-troubleshooting"></a>
## 7. 🩺 Common Troubleshooting Checklist

### 🔴 Error: `unable to open database file`
* **Why**: The database path was defined as a relative path outside the package directories, causing it to be excluded during `agents-cli deploy` bundling.
* **Fix**: Ensure the database file is placed inside the `app/` folder (`my-agent/app/purchase_orders.db`) and `my-agent/app/db.py` resolves it dynamically:
  ```python
  DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "purchase_orders.db"))
  ```

### 🔴 Error: Chat replies show up as raw text instead of rich A2UI Cards
* **Why**: The A2A stream payload wraps A2UI cards in a nested data envelope.
* **Fix**: Ensure your `frontend/main.py` is using the nested envelope parser inside `_extract_parts`:
  ```python
  elif getattr(root, "data", None) is not None:
      data_dict = root.data
      meta = {}
      if isinstance(data_dict, dict):
          meta = data_dict.get("metadata") or {}
      if not meta:
          meta = getattr(root, "metadata", None) or {}
      mime = meta.get("mimeType") if isinstance(meta, dict) else None
      if mime == "application/json+a2ui":
          inner_data = data_dict.get("data") if isinstance(data_dict, dict) else data_dict
          out.append({"kind": "a2ui", "data": inner_data})
  ```

### 🔴 Error: `403 Permission Denied` or `API not enabled`
* **Why**: Your local environment has active credentials, but is pointing to an incorrect GCP Project ID or your active user lacks IAM roles on Vertex AI (`roles/aiplatform.user`).
* **Fix**: Verify your project ID via `gcloud config list` and re-run:
  ```bash
  gcloud auth application-default login
  ```

---

🎉 **You are completely set up and ready to continue building! If you clone this repository to any other environment, simply refer to this recovery runbook for frictionless setup.**
