# Design Specification: UDS Diagnostics & Automated Test Generation Assistant (AutoDiag-AI)

**Document Reference:** `docs/superpowers/specs/2026-10-04-uds-diagnostic-ai-assistant-design.md`  
**Standard Compliance:** ISO 14229 (UDS), ISO 15765-2 (DoCAN / ISO-TP), ISO 13400 (DoIP), ISO 26262  
**Status:** Approved  
**Version:** 1.0.0  

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
In modern automotive systems (ECUs, domain controllers, zonal gateways), diagnostic validation under **ISO 14229 (Unified Diagnostic Services - UDS)** is mission-critical for vehicle maintenance, flashing/bootloaders, safety-critical calibration, and end-of-line verification. 

Automotive validation teams face several major bottlenecks:
1. **Manual Interpretation of Complex Specifications:** Hundreds of pages of unstructured OEM diagnostic sheets, ODX-D XML files, and ISO standards must be manually converted into test procedures.
2. **Error-Prone Test Authoring:** High rates of errors in byte-level payload construction, parameter length mismatches, and missed Negative Response Code (NRC) scenarios.
3. **Flaws in Pure-LLM Solutions:** Standard generative AI models suffer from 40–60% hallucination rates on hex byte lengths, security seed-key sequence rules, and state-machine transitions.
4. **Toolchain Lock-in:** Expensive proprietary testing environments (such as Vector CANoe/vTESTstudio) lack open, automated, CI/CD-friendly test synthesis.

### 1.2 The AutoDiag-AI Solution
**AutoDiag-AI** is a **Deterministic-Guarded Hybrid AI Platform** that bridges the gap between natural language semantic understanding and deterministic automotive protocol execution. It ingests diagnostic specifications, builds an indexed local vector & structured knowledge store, executes deterministic ISO 14229 state-machine checks, auto-generates 100% syntactically valid positive and negative test matrices, provides an interactive virtual ECU execution testbench with live CAN sniffer, and exports production-ready Python (`pytest` + `python-can`) and Vector CAPL scripts.

---

## 2. High-Level System Architecture

The platform follows a **Dual-Surface Modular Architecture** composed of five decoupled layers:

```
+---------------------------------------------------------------------------------------------------+
|                                        PRESENTATION LAYER                                         |
|  +----------------------------------------------------+  +-------------------------------------+  |
|  |     Streamlit Interactive Workbench (Engineer UI)  |  |    FastAPI Swagger UI & Web Portal  |  |
|  |   - Spec Ingestion & Vector Explorer               |  |   - REST API Endpoints              |  |
|  |   - FSM Visualizer & Matrix Generator              |  |   - WebSocket CAN Bus Live Stream   |  |
|  |   - Live Virtual ECU Test Bench & Hex Sniffer      |  |   - Headless CI/CD Integration      |  |
|  +----------------------------------------------------+  +-------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
                                                  │ REST / WS
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                      APPLICATION & API LAYER                                      |
|  +---------------------------------------------------------------------------------------------+  |
|  |                                  FastAPI Application Core                                   |  |
|  |  - Auth & RBAC               - Project Workspace Manager     - Diagnostic Job Dispatcher    |  |
|  |  - Schema Validation (Pydantic) - Audit Logger & Export Service                             |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                  INTELLIGENCE & PROTOCOL CORE                                     |
|  +-------------------------------+  +-------------------------------+  +-----------------------+  |
|  |    Local Semantic & RAG Core  |  |  Deterministic UDS FSM Engine |  | Automated Test Gen    |  |
|  | - PDF/ODX/JSON Extractor      |  | - ISO 14229 Protocol Validator|  | - Positive Matrix     |  |
|  | - Sentence-Transformers (BGE) |  | - Session State Machine (FSM) |  | - Negative Matrix     |  |
|  | - Local ChromaDB Vector Store |  | - Security State Machine (FSM)|  | - Dual Target Code    |  |
|  | - Grounded Citation Generator |  | - NRC Decision Matrix         |  |   (Python & CAPL)     |  |
|  +-------------------------------+  +-------------------------------+  +-----------------------+  |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                  EXECUTION & SIMULATION LAYER                                     |
|  +---------------------------------------------------------------------------------------------+  |
|  |                            In-Memory Virtual ECU & CAN Simulator                            |  |
|  |  - ISO-TP (ISO 15765-2) Multi-Frame Segmenter / Reassembler                                 |  |
|  |  - Configurable DIDs ($22/$2E), Security ($27), Sessions ($10), Routine Control ($31)       |  |
|  |  - Virtual CAN Loopback Bus with Real-Time Frame Sniffing & Latency Simulation               |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Component Specifications

### 3.1 Component 1: Deterministic UDS Protocol & State Machine Engine (`autodiag.core.protocol`)

#### 3.1.1 Supported ISO 14229 Services
1. **Diagnostic & Communication Management:**
   * `0x10` (*DiagnosticSessionControl*): `0x01` (Default), `0x02` (Programming), `0x03` (Extended), `0x04` (SafetySystem).
   * `0x11` (*ECUReset*): `0x01` (Hard), `0x02` (KeyOffOn), `0x03` (Soft).
   * `0x27` (*SecurityAccess*): Odd sub-functions (`0x01, 0x03, 0x11`) Request Seed; Even sub-functions (`0x02, 0x04, 0x12`) Send Key.
   * `0x28` (*CommunicationControl*): Enable/Disable RX/TX for Normal/NetworkManagement messages.
   * `0x3E` (*TesterPresent*): `0x00` (Standard) & `0x80` (Suppress Positive Response).
   * `0x85` (*ControlDTCSetting*): `0x01` (ON), `0x02` (OFF).
2. **Data Transmission:**
   * `0x22` (*ReadDataByIdentifier*): Single and multi-DID read support with 2-byte DIDs.
   * `0x2E` (*WriteDataByIdentifier*): DID + payload write with length enforcement.
3. **Stored Data & Routine Control:**
   * `0x14` (*ClearDiagnosticInformation*): 3-byte Group/DTC mask.
   * `0x19` (*ReadDTCInformation*): `0x01` (ReportNumberOfDTCs), `0x02` (ReportDTCByStatusMask), `0x0A` (ReportSupportedDTCs).
   * `0x31` (*RoutineControl*): `0x01` (StartRoutine), `0x02` (StopRoutine), `0x03` (RequestRoutineResults); 2-byte RIDs.
4. **Upload & Download:**
   * `0x34` (*RequestDownload*), `0x36` (*TransferData*), `0x37` (*RequestTransferExit*).

#### 3.1.2 Finite State Machines (FSM)
* **Session FSM:** Enforces valid transitions (`DEFAULT` $\to$ `EXTENDED` $\to$ `PROGRAMMING`). Reverts to `DEFAULT` on S3 timeout ($5000\text{ ms}$) or Hard Reset.
* **Security Access FSM:** Enforces `LOCKED` $\to$ `SEED_GENERATED` $\to$ `UNLOCKED`. Rejection on wrong key, attempt limit ($3$ attempts), and penalty timer ($10\text{ seconds}$).

#### 3.1.3 Negative Response Code (NRC) Engine
Generates and validates exact ISO 14229 error codes:
* `0x11` (ServiceNotSupported), `0x12` (SubFunctionNotSupported), `0x13` (IncorrectMessageLengthOrInvalidFormat), `0x22` (ConditionsNotCorrect), `0x24` (RequestSequenceError), `0x31` (RequestOutOfRange), `0x33` (SecurityAccessDenied), `0x35` (InvalidKey), `0x36` (ExceedNumberOfAttempts), `0x37` (RequiredTimeDelayNotExpired), `0x7E` (SubFunctionNotSupportedInActiveSession), `0x7F` (ServiceNotSupportedInActiveSession), `0x78` (ResponsePending).

---

### 3.2 Component 2: Specification Ingestion & Local RAG (`autodiag.core.rag`)

#### 3.2.1 Multi-Format Ingestion
* **PDF Parser:** Uses `pdfplumber` for table extraction (DIDs, Services, Parameters) and text flow analysis.
* **ODX-D / XML Parser:** Parses standard Open Diagnostic Data Exchange XML definitions into normalized Pydantic models.
* **JSON / YAML Schema Loader:** Direct import of structured OEM diagnostic definition files.

#### 3.2.2 Local Vector Database & Grounded Embeddings
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (fast, lightweight, runs locally on CPU).
* **Vector Store:** `ChromaDB` (persistent local directory per project workspace).
* **Metadata Tagging:** Every chunk is tagged with `service_id`, `did`, `session`, `security_level`, `source_file`, and `page_number`.
* **Citation Generation:** Output includes exact document and section citations to ensure audit compliance.

---

### 3.3 Component 3: Automated Test Matrix & Code Exporter (`autodiag.core.generator`)

#### 3.3.1 Test Generation Engine
* **Positive Scenarios:** Valid requests across authorized sessions and security levels, verifying expected payload data, byte lengths, and response SIDs ($SID + 0x40$).
* **Negative Scenarios (Automated Robustness Matrix):**
  1. *Wrong Session:* Requesting restricted service in `DEFAULT` session $\implies$ Expect NRC `0x7F` / `0x7E`.
  2. *Security Violation:* Writing secure DID without authentication $\implies$ Expect NRC `0x33`.
  3. *Invalid Length:* Payload with missing or extra bytes $\implies$ Expect NRC `0x13`.
  4. *Out of Range:* Requesting undefined DID or routine $\implies$ Expect NRC `0x31`.
  5. *Brute Force Key Injection:* Sending wrong key 3 times $\implies$ Expect NRC `0x35` $\to$ `0x36` $\to$ `0x37`.
  6. *Suppress Positive Response:* Verifying that setting MSB bit ($0x80$) suppresses the positive response frame.

#### 3.3.2 Dual-Target Code Generator
* **Python Target:** Generates standard `pytest` test suites utilizing `python-can` and `can-isotp`. Includes setup, teardown, frame transmission, ISO-TP reassembly, and strict assertion checking.
* **Vector CAPL Target:** Generates `.can` / `.capl` source code ready for compilation in Vector CANoe / CANalyzer with `testcase` definitions, `diagSendRequest`, `testWaitForMessage`, and pass/fail logging.

---

### 3.4 Component 4: In-Memory Virtual ECU & CAN Bus Simulator (`autodiag.core.simulator`)

* **Virtual CAN Bus:** In-memory queue-based CAN channel (CAN ID `0x7E0` for Physical Request, `0x7E8` for Physical Response, `0x7DF` for Functional Broadcast).
* **ISO-TP Layer (ISO 15765-2):**
  * Single Frame (SF, up to 7 data bytes).
  * First Frame (FF) & Consecutive Frames (CF) with Flow Control (FC, CTS, BlockSize, STmin).
* **Simulated ECU State Storage:**
  * Persistent DID memory (e.g., VIN `0xF190` = `"WVWZZZ3CZWE123456"`, Part No `0xF187` = `"ECU-990-2026"`).
  * Configurable Routine Handlers (Memory Erase, Flash Calibration).
  * Real-time frame latency and optional NRC `0x78` (Response Pending) simulation.

---

### 3.5 Component 5: Application Service & User Interfaces (`autodiag.api` & `autodiag.ui`)

* **FastAPI Backend (`autodiag/api`):**
  * `POST /api/v1/specs/upload`: Ingest diagnostic files.
  * `POST /api/v1/query`: RAG semantic Q&A with source citations.
  * `POST /api/v1/tests/generate`: Synthesize positive and negative test cases for given DIDs/Services.
  * `POST /api/v1/tests/execute`: Run generated test suite against the in-memory Virtual ECU.
  * `GET /api/v1/export/{format}`: Export test artifacts (`.py`, `.capl`, `.json`, `.csv`).
  * `WebSocket /ws/can`: Real-time CAN frame sniffer stream.
* **Streamlit Workbench (`autodiag/ui/streamlit_app.py`):**
  * Tab 1: **Specification Ingestion & Vector Explorer** (Upload and explore DIDs/Services).
  * Tab 2: **AI Diagnostic Knowledge Assistant** (Grounded Q&A with citations).
  * Tab 3: **Automated Test Case Generator** (Matrix selector, FSM visualizer, positive & negative test builder).
  * Tab 4: **Live Virtual ECU Test Bench & Hex Sniffer** (Real-time live execution and frame inspector).
  * Tab 5: **Code & Report Export Center** (Download PyTest suites, CAPL scripts, and summary reports).

---

## 4. Directory & Module Structure

```
AutoDiag-AI/
├── autodiag/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── protocol/
│   │   │   ├── __init__.py
│   │   │   ├── constants.py          # ISO 14229 SIDs, NRCs, Session types
│   │   │   ├── frame.py              # UDS Request/Response frame parser & builder
│   │   │   ├── fsm.py                # Session & Security Finite State Machines
│   │   │   └── validator.py          # Deterministic message length & rule validator
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py             # PDF & ODX/JSON specification parser
│   │   │   ├── knowledge_base.py     # Schema extractor & DiagnosticDatabase model
│   │   │   └── vector_store.py       # ChromaDB + SentenceTransformers RAG engine
│   │   ├── generator/
│   │   │   ├── __init__.py
│   │   │   ├── matrix.py             # Positive & Negative test matrix builder
│   │   │   ├── python_exporter.py    # PyTest / python-can test script compiler
│   │   │   └── capl_exporter.py      # Vector CANoe CAPL test script compiler
│   │   └── simulator/
│   │       ├── __init__.py
│   │       ├── isotp.py              # ISO 15765-2 transport protocol handler
│   │       ├── virtual_ecu.py        # In-memory simulated ECU with full UDS handler
│   │       └── bus.py                # Virtual CAN bus with real-time frame event bus
│   ├── api/
│   │   ├── __init__.py
│   │   ├── schemas.py                # Pydantic models for requests and responses
│   │   ├── routes.py                 # FastAPI endpoints
│   │   └── server.py                 # FastAPI application & WebSocket manager
│   └── ui/
│       ├── __init__.py
│       ├── streamlit_app.py          # Multi-tab Streamlit Engineering Workbench
│       └── web_dashboard.html        # Embedded modern HTML/JS Web Dashboard
├── tests/
│   ├── test_protocol.py              # Unit tests for UDS protocol & FSM
│   ├── test_simulator.py             # Unit tests for Virtual ECU & ISO-TP
│   ├── test_generator.py             # Unit tests for Test Matrix & Exporters
│   └── test_rag.py                   # Unit tests for Ingestion & Vector Search
├── sample_specs/
│   ├── engine_ecu_uds_spec.json      # Comprehensive sample OEM ECU spec
│   └── sample_spec.pdf               # Sample diagnostic specification document
├── requirements.txt                  # Dependencies
├── Dockerfile                        # Containerized deployment
└── README.md                         # Documentation & Interview Presentation Guide
```

---

## 5. Verification & Testing Strategy

1. **Unit Test Coverage:** Complete unit tests for:
   * UDS byte framing, SID validation, and sub-function handling.
   * Session transition state machine and S3 timeout rules.
   * Security seed-key validation and lock penalty counters.
   * Virtual ECU execution for all supported services ($10, $11, $22, $27, $2E, $31, $14, $19, $3E$).
   * Python and CAPL code export syntax and formatting.
2. **Integration Verification:**
   * Automated test execution pipeline: Ingest sample spec $\to$ Generate test matrix $\to$ Execute against Virtual ECU $\to$ Assert 100% pass rate for positive tests and expected NRC captures for negative tests.
3. **Benchmarking & Placement Readiness:**
   * Zero hallucination rate due to deterministic protocol guardrails.
   * Sub-second test generation and live virtual bus simulation.

---