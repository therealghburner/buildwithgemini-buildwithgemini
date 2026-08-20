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

## 🏗️ Detailed System Architecture Diagram

The multi-tier system architecture below shows the separation of concerns between Client-side presentation, Proxy-side authentication, Reasoning Engine orchestration, and Google Cloud Platform services:

```mermaid
graph TB
    %% Styling Definitions
    classDef client fill:#e8f0fe,stroke:#4285f4,stroke-width:2px,color:#1a73e8;
    classDef proxy fill:#fef7e0,stroke:#f4b400,stroke-width:2px,color:#b06000;
    classDef runtime fill:#e6f4ea,stroke:#0f9d58,stroke-width:2px,color:#137333;
    classDef gcp fill:#fce8e6,stroke:#db4437,stroke-width:2px,color:#c5221f;

    %% Client Presentation Layer
    subgraph Client_Layer ["1. Client Presentation Layer (Local Browser)"]
        UI["HTML5 Chat Window<br/>(frontend/static/index.html)"]
        A2UI_Render["A2UI Card Parser<br/>(Direct JSON v0.8 Renderer)"]
        UI_Log["State Logger<br/>(Visual Feedbacks & Error Catchers)"]
    end

    %% Auth & Middleware Proxy Layer
    subgraph Proxy_Layer ["2. FastAPI Routing & Auth Proxy Layer"]
        Proxy_App["FastAPI Proxy Web Server<br/>(frontend/main.py on Port 8080)"]
        ADC_Auth["ADC Authentication Handlers<br/>(Application Default Credentials)"]
        A2A_SDK["A2A Protocol Client<br/>(A2A Streaming Protocol Wrapper)"]
    end

    %% Core Orchestration & Reasoning Engine Layer
    subgraph Reasoning_Layer ["3. Reasoning Engine Layer (Agent Container)"]
        ADK_Agent["ADK Reasoning Agent<br/>(my-agent/app/agent.py)"]
        Gemini_LLM["Gemini Model Wrapper<br/>(gemini-2.5-flash / Enterprise)"]
        
        subgraph Callbacks ["Custom Lifecycle Event Callbacks"]
            A2UI_Call["after_model_callback<br/>(app/a2ui_utils.py)"]
            Memory_Call["after_agent_callback<br/>(Memory Bank Generator)"]
        end
    end

    %% Data & Specialized Enterprise Service Layer
    subgraph Enterprise_Layer ["4. Enterprise Data & Specialized Service Layer"]
        SQLite_DB[("Local SQLite PO DB<br/>(purchase_orders.db - 10k rows)")]
        RAG_Engine["Vertex AI RAG Engine<br/>(projects/.../ragCorpora/3183244492085919744)"]
        Memory_Bank["Vertex AI Memory Bank<br/>(Memory Engine ID: 1382809045009694720)"]
        Firestore_DB[("Native Google Firestore<br/>(user_profiles collection)")]
        Sandbox["Agent Engine Code Sandbox<br/>(AgentEngineSandboxCodeExecutor)"]
    end

    %% Network & Method Connections
    UI -->|HTTP Post /chat| Proxy_App
    A2UI_Render <-->|Natively Render Layouts| UI
    
    Proxy_App -->|Verify GCP Credentials| ADC_Auth
    Proxy_App -->|Stream Message Over A2A Protocol| A2A_SDK
    A2A_SDK -->|gRPC/HTTP Streaming Endpoint| ADK_Agent
    
    ADK_Agent -->|Text Prompt Orchestration| Gemini_LLM
    Gemini_LLM -->|Identify Schema & Format Visuals| A2UI_Call
    
    ADK_Agent -->|Safe Read-Only SQL Queries| SQLite_DB
    ADK_Agent -->|Retrieve Policy Passages| RAG_Engine
    ADK_Agent -->|Read & Update Client Profiles| Firestore_DB
    ADK_Agent -->|Execute Dynamic Calculations| Sandbox
    
    A2UI_Call -->|Emitted Visual Cards JSON Array| Proxy_App
    ADK_Agent -->|Identify Session Facts & Allergies| Memory_Call
    Memory_Call -->|Write facts asynchronously| Memory_Bank

    %% Apply CSS Classes
    class Client_Layer,UI,A2UI_Render,UI_Log client;
    class Proxy_Layer,Proxy_App,ADC_Auth,A2A_SDK proxy;
    class Reasoning_Layer,ADK_Agent,Gemini_LLM,A2UI_Call,Memory_Call,Callbacks runtime;
    class Enterprise_Layer,SQLite_DB,RAG_Engine,Memory_Bank,Firestore_DB,Sandbox gcp;
```

---

## 🔄 End-to-End System Workflow Diagram

The sequence diagram below shows the detailed step-by-step workflow of a single query lifecycle from the moment the user types a query (such as *"How many POs do we have?"*) to database translation, RAG lookup, layout generation, and memory storage:

```mermaid
sequenceDiagram
    autonumber
    actor User as Procurement User
    participant UI as static/index.html
    participant Proxy as main.py (Port 8080)
    participant Agent as app/agent.py (Runtime)
    participant DB as SQLite PO DB
    participant RAG as Vertex AI RAG Engine
    participant MB as Vertex AI Memory Bank
    participant Gemini as Gemini Model API

    %% 1. Input Phase
    User->>UI: Types query: "How many POs do we have?"
    UI->>Proxy: POST /chat {message: "How many POs do we have?"}
    
    %% 2. Initialization & Preload Phase
    Proxy->>Agent: Stream query via A2A-SDK client
    Note over Agent: Pre-execution lifecycle hook
    Agent->>MB: Retrieve past long-term user context & safety constraints
    MB-->>Agent: Returns facts (user profile roles, constraints)
    
    %% 3. Reasoning & SQL Execution Loop
    Agent->>Gemini: Pass user query + context + DB Schema definitions
    Note over Gemini: Analyzes schema and determines SQL intent
    Gemini-->>Agent: Suggests calling tool "query_purchase_orders(sql)"
    
    Agent->>DB: Execute query_purchase_orders("SELECT COUNT(*) FROM purchase_orders")
    Note over DB: Enforces strict AST check (Only SELECT or WITH is allowed)
    DB-->>Agent: Returns data: [{"COUNT(*)": 10000}]
    
    %% 4. Policy Grounding Check (If policy rules queried)
    opt Optional: Querying policy guidelines, SLA, or Approval Tiers
        Agent->>RAG: search_procurement_policies(query_text)
        RAG-->>Agent: Returns verified corporate procurement passages
    end

    %% 5. Layout Rendering and Synthesis Phase
    Agent->>Gemini: Provide DB outputs/RAG passages and request user-facing response
    Gemini-->>Agent: Synthesizes final text and raw visual A2UI cards
    
    Note over Agent: Post-model execution callback (after_model_callback)
    Agent->>Agent: a2ui_callback parses payload & builds Direct JSON cards
    
    %% 6. Return Streaming Stream
    Agent-->>Proxy: Streams response payload (Text + A2UI visuals metadata)
    Proxy-->>UI: Streams response chunks (Text + visual A2UI card arrays)
    
    %% 7. Local Memory Consolidation Phase (Asynchronous)
    Note over Agent: Post-agent execution callback (after_agent_callback)
    Agent->>Agent: Extract new user insights/constraints from conversation
    Agent->>MB: Commit updated facts to Memory Bank (Session Tracking)
    
    %% 8. Presentation Phase
    Note over UI: Receives stream completion
    UI->>UI: Renders visual Card layout with dynamic CSS details
    UI-->>User: Displays visual metrics + direct response card!
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
