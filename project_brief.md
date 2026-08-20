# Project Brief: Purchase Order Procurement & Compliance Analytics Agent

Welcome to the **Purchase Order (PO) Procurement & Compliance Analytics Agent** repository. This enterprise-grade AI system is designed for procurement teams, financial controllers, and procurement auditors to query purchase order data, audit compliance thresholds, analyze vendor risk, and search corporate procurement policies in real time.

---

## 🎯 System Capabilities

1. **Analytical Database Queries**: Directly translates natural language questions into secure, read-only SQL queries executed over a **10,000-row SQLite database (`purchase_orders.db`)** with built-in AST-based query safety guardrails (only SELECT/WITH statements are allowed).
2. **Policy RAG Grounding**: Powered by **Vertex AI Serverless RAG Engine** to search, retrieve, and ground agent decisions against official corporate procurement policies (e.g. approval thresholds, payment terms, vendor SLA guidelines).
3. **Compliance Auditing & Risk Scoring**: Includes specialized analytical action tools to calculate real-time vendor risk scores based on order volume and cancellation rates, and flag high-value or suspicious POs for human compliance reviews.
4. **Visual A2UI Cards**: Implements the **A2A protocol** and standard **A2UI Schema Manager (v0.8)** with a basic component catalog to return beautifully formatted structured visual layouts (cards, columns, and rows) directly in the chat window.
5. **Cross-Session Long-Term Memory**: Integrates a managed **Vertex AI Memory Bank** to dynamically remember, persist, and strictly enforce safety constraints (such as user-stated dietary or safety preferences) across separate user sessions.
6. **Firestore Profile Sync**: Connected to Google Cloud Native **Firestore** to manage user roles and procurement department profiles.

---

## 🏗️ System Architecture

The following diagram illustrates the complete, production-ready system architecture, illustrating how the client web interface talks to the FastAPI authentication proxy and routes messages to the Vertex AI Agent Runtime and its associated enterprise services:

```mermaid
graph TD
    %% Styling Definitions
    classDef client fill:#e8f0fe,stroke:#4285f4,stroke-width:2px,color:#1a73e8;
    classDef proxy fill:#fef7e0,stroke:#f4b400,stroke-width:2px,color:#b06000;
    classDef runtime fill:#e6f4ea,stroke:#0f9d58,stroke-width:2px,color:#137333;
    classDef gcp fill:#fce8e6,stroke:#db4437,stroke-width:2px,color:#c5221f;

    %% Components
    subgraph Browser Client [Client Layer]
        UI["Plain HTML/CSS Chat UI<br/>(frontend/static/index.html)"]
        UI_A2UI["A2UI Visual Renderer<br/>(Direct JSON v0.8)"]
    end

    subgraph API Gateway [Authentication & Proxy Layer]
        Proxy["FastAPI Proxy Service<br/>(frontend/main.py on Port 8080)"]
    end

    subgraph Agent Runtime [Reasoning Engine Layer]
        ADK_Agent["ADK Reasoning Engine Agent<br/>(my-agent/app/agent.py)"]
        A2UI_Callback["after_model_callback<br/>(app/a2ui_utils.py)"]
        Memory_Callback["after_agent_callback<br/>(Memory Generator)"]
    end

    subgraph Enterprise Services [Google Cloud & Data Layer]
        SQLite_DB[("SQLite PO Database<br/>(purchase_orders.db - 10k rows)")]
        RAG_Engine["Vertex AI RAG Engine<br/>(procurement_policy.md)"]
        Memory_Bank["Vertex AI Memory Bank<br/>(Cross-Session Memory)"]
        Firestore_DB[("Native Firestore DB<br/>(user_profiles collection)")]
        Sandbox["Agent Engine Sandbox<br/>(Secure Python Execution)"]
    end

    %% Routing Flows
    UI -->|1. User Message (Plain Chat)| Proxy
    Proxy -->|2. A2A Protocol (with ADC Credentials)| ADK_Agent
    
    ADK_Agent -->|Query & Read| SQLite_DB
    ADK_Agent -->|Policy Search| RAG_Engine
    ADK_Agent -->|Fetch/Sync Profiles| Firestore_DB
    ADK_Agent -->|Execute Python| Sandbox
    
    ADK_Agent --> A2UI_Callback
    A2UI_Callback -->|3. Structured A2UI JSON payload| Proxy
    Proxy -->|4. A2A stream payload| UI
    UI -->|Natively Render Card Layouts| UI_A2UI

    ADK_Agent --> Memory_Callback
    Memory_Callback -->|Persist facts| Memory_Bank

    %% Apply Classes
    class Browser Client,UI,UI_A2UI client;
    class API Gateway,Proxy proxy;
    class Agent Runtime,ADK_Agent,A2UI_Callback,Memory_Callback runtime;
    class Enterprise Services,SQLite_DB,RAG_Engine,Memory_Bank,Firestore_DB,Sandbox gcp;
```

---

## 📂 Repository Structure

The repository is structured logically across frontend services and backend reasoning engine components:

```
├── frontend/                        # Web chat interface and proxy
│   ├── main.py                      # FastAPI authentication proxy communicating over A2A
│   └── static/
│       └── index.html               # Plain HTML UI containing native A2UI visual card renderer
├── my-agent/                        # Deployed ADK Reasoning Engine Agent
│   ├── app/
│   │   ├── agent.py                 # Core agent declaration, system prompts, and tool registrations
│   │   ├── a2ui_utils.py            # A2UI Direct JSON formatter after_model_callback
│   │   ├── db.py                    # SQLite database safety guardrails & connection manager
│   │   ├── tools.py                 # Procurement tools (Vendor Risk, Flag Audit, CSV Export)
│   │   ├── rag_tool.py              # Vertex AI RAG policy retrieval tool
│   │   ├── rag_config.txt           # Active RAG Corpus ID configuration
│   │   └── firestore_backend.py     # Firestore User Profiles database operations
│   ├── purchase_orders.db           # 10,000 row SQLite database file packaged with container
│   ├── pyproject.toml               # Python packaging metadata and dependencies (google-adk, etc.)
│   └── agents-cli-manifest.yaml     # reasoningEngine deployment manifest
└── project_brief.md                 # System overview, capabilities, and Mermaid diagram (this file)
```
