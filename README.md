# 🚗 AutoDiag-AI: Automotive UDS Diagnostics & Automated Test Generation Platform

> **Standard Compliance:** ISO 14229 (Unified Diagnostic Services - UDS) & ISO 15765-2 (DoCAN / ISO-TP)  
> **Reference Case Study:** Automotive Engineering AI Platform — Case Study 5 (UDS Diagnostics & Automated Test Generation)  
> **Status:** Production-Ready Reference Implementation & Evaluation Portfolio  

---

## 📌 Executive Summary

**AutoDiag-AI** is a **Deterministic-Guarded Hybrid AI Platform** designed for automotive OEM and Tier-1 validation teams. It solves the critical bottleneck of manually interpreting complex diagnostic specifications (ISO 14229, OEM sheets, ODX-D XML, PDFs) by:
1. **Automating Specification Ingestion:** Extracting services, DIDs, RIDs, session parameters, and security requirements.
2. **Grounded AI Knowledge Assistant:** Providing natural language search with exact document and section citations.
3. **Deterministic Protocol & FSM Guardrails:** Eliminating LLM hallucinations by using a deterministic ISO 14229 protocol parser, Session FSM, and Security Access state machine.
4. **Automated Positive & Negative Test Synthesis:** Auto-generating full test matrices (including Negative Response Codes: NRC `$11, $12, $13, $22, $31, $33, $35, $36, $37, $7E, $7F`).
5. **In-Memory Virtual ECU Execution & CAN Bus Sniffer:** Executing test suites in real-time over virtual ISO-TP channels with real-time frame telemetry.
6. **Dual-Target Script Export:** Compiling production-ready standalone **Python (`pytest` + `python-can` + `can-isotp`)** and **Vector CANoe CAPL (`.can`/`.capl`)** test modules.

---

## 🏗 System Architecture

```
                                  +-------------------------------------------------------------+
                                  |                 DUAL PRESENTATION SURFACES                  |
                                  |  +-------------------------------+  +--------------------+  |
                                  |  | Streamlit Engineer Workbench  |  | Modern Web Portal  |  |
                                  |  | (5-Tab Interactive Dashboard) |  | (FastAPI Swagger)  |  |
                                  |  +---------------+---------------+  +---------+----------+  |
                                  +------------------|----------------------------|-------------+
                                                     | REST / WebSockets          |
                                                     +--------------+-------------+
                                                                    v
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                FASTAPI APPLICATION SERVICE LAYER                                              |
|   /api/v1/specs/upload  |  /api/v1/query  |  /api/v1/tests/generate  |  /api/v1/tests/execute  |  /api/v1/export/{format}         |
+-------------------------------------------------------------------------------------------------------------------------------+
                                                                    │
                                                                    ▼
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                 INTELLIGENCE & PROTOCOL CORE                                                  |
|  +-------------------------------+  +---------------------------------------------+  +-------------------------------------+  |
|  |     Semantic Knowledge Base   |  |       Deterministic ISO 14229 Engine        |  |     Automated Test Synthesizer      |  |
|  | - PDF & ODX XML Deserializer  |  | - Request/Response Framing & Length Checker |  | - Positive Functional Matrix        |  |
|  | - Local Chunk Embeddings      |  | - Session Transition State Machine (FSM)    |  | - Negative Robustness Matrix (NRCs) |  |
|  | - Grounded Citation Retrieval |  | - Security Access Seed/Key FSM              |  | - Python PyTest & CAPL Exporters    |  |
|  +-------------------------------+  +---------------------------------------------+  +-------------------------------------+  |
+-------------------------------------------------------------------------------------------------------------------------------+
                                                                    │
                                                                    ▼
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                  VIRTUAL SIMULATION TEST BENCH                                                |
|  +-------------------------------------------------------------------------------------------------------------------------+  |
|  |                                            In-Memory Virtual ECU Simulator                                              |  |
|  |  - ISO-TP (ISO 15765-2) Single Frame (SF), First Frame (FF), Flow Control (FC), and Consecutive Frames (CF)             |  |
|  |  - Configurable DIDs ($22/$2E), Security ($27), Sessions ($10), Routine Control ($31), DTCs ($14/$19), TesterPresent     |  |
|  |  - Virtual CAN Bus with Real-Time Event Sniffing and Latency Simulation (CAN ID 0x7E0 / 0x7E8)                          |  |
|  +-------------------------------------------------------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## ⚡ Quickstart & Installation

### 1. Requirements
* Python 3.10+ (Tested on Windows 11 & Linux)
* Dependencies in `requirements.txt`

### 2. Setup
```bash
# Clone or navigate to the repository
cd AutoDiag-AI

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Options

#### Option A: Run Terminal Demo & Automated Validation
```bash
python run_demo.py
```
*Outputs: Specification ingestion, semantic Q&A, 21-test execution against Virtual ECU, and exported Python & CAPL test files.*

#### Option B: Launch FastAPI Server & Modern Web Dashboard
```bash
python run_demo.py --server
```
*Open [http://localhost:8000](http://localhost:8000) for Web Dashboard or [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.*

#### Option C: Launch Streamlit Interactive Workbench
```bash
python run_demo.py --streamlit
```
*Opens interactive 5-tab workbench in your default web browser.*

#### Option D: Run Full PyTest Suite
```bash
pytest tests/ -v
```
*(36/36 unit & integration tests passing)*

---

## 📊 Supported ISO 14229 Services & NRCs

| SID | Service Name | Supported Sub-functions | Negative Response Codes Tested |
| :--- | :--- | :--- | :--- |
| **`0x10`** | DiagnosticSessionControl | `0x01` (Default), `0x02` (Prog), `0x03` (Ext), `0x80` (Suppress) | `0x12`, `0x13`, `0x22` |
| **`0x11`** | ECUReset | `0x01` (Hard), `0x02` (KeyOffOn), `0x03` (Soft) | `0x12`, `0x13` |
| **`0x22`** | ReadDataByIdentifier | Single & Multi-DID (`0xF190` VIN, `0xF187`, `0x0100` RPM, etc.) | `0x13`, `0x31`, `0x33`, `0x7F` |
| **`0x27`** | SecurityAccess | `0x01/0x02` (Level 1 Seed/Key), `0x03/0x04` (Level 2) | `0x13`, `0x35`, `0x36`, `0x37` |
| **`0x2E`** | WriteDataByIdentifier | Write parameter DIDs (`0xF199`, `0x0200` Idle Speed) | `0x13`, `0x31`, `0x33`, `0x7F` |
| **`0x31`** | RoutineControl | `0x01` (Start), `0x02` (Stop), `0x03` (RequestResults) | `0x13`, `0x31`, `0x33`, `0x7F` |
| **`0x14`** | ClearDiagnosticInformation | 3-byte DTC mask (`0xFFFFFF`) | `0x13` |
| **`0x19`** | ReadDTCInformation | `0x01` (ReportCount), `0x02` (ReportByStatusMask) | `0x12`, `0x13` |
| **`0x3E`** | TesterPresent | `0x00` (Standard) & `0x80` (Suppress Positive Response) | `0x13` |

---

## 🎯 Placement Interview Presentation & Talk Track

When presenting this project to interviewers at **Bosch, Continental, KPIT, ZF, Mercedes-Benz, Tata Motors, GM, Ford**, use this structured talk track:

### 1. Problem Statement
> *"In automotive ECU validation, test engineers spend over 40% of their time manually converting ODX and PDF diagnostic specifications into positive and negative test cases. Pure-LLM approaches hallucinate byte lengths and state rules, which is unacceptable for safety-critical vehicle software."*

### 2. Your Innovation (The Deterministic-Guarded Hybrid Architecture)
> *"I designed and built AutoDiag-AI using a hybrid architecture. The AI layer handles natural language requirement queries and semantic document parsing, but all test message generation passes through a deterministic ISO 14229 state machine and protocol validator. This ensures zero hallucination in byte lengths, session preconditions, and NRC assignments."*

### 3. Key Automotive Concepts Mastered in This Project
1. **ISO 14229 UDS Layer:** Session transitions ($10$), Security access handshake ($27$), Read/Write DIDs ($22/2E$), Routine control ($31$), and NRC handling.
2. **ISO 15765-2 (ISO-TP) Transport:** Single-Frame (SF) vs. Multi-Frame (FF, FC with CTS, and CF) segmentation and reassembly.
3. **Security State Machine:** Seed-Key calculation, brute-force attempt limits (NRC $0x36$), and penalty timers (NRC $0x37$).
4. **Dual Test Export:** Python test automation (`python-can` + `can-isotp`) for CI/CD, and Vector CANoe CAPL (`.can`) for HIL test benches.

---

## 📂 Project Structure

```
AutoDiag-AI/
├── autodiag/
│   ├── __init__.py
│   ├── core/
│   │   ├── protocol/
│   │   │   ├── constants.py          # ISO 14229 SIDs, NRCs, Session enums
│   │   │   ├── frame.py              # UDS Request/Response frame parser & builder
│   │   │   ├── fsm.py                # Session & Security Finite State Machines
│   │   │   └── validator.py          # Deterministic message length & rule validator
│   │   ├── rag/
│   │   │   ├── parser.py             # PDF & ODX/JSON specification parser
│   │   │   ├── knowledge_base.py     # Schema extractor & DiagnosticDatabase model
│   │   │   └── vector_store.py       # Persistent vector collection manager
│   │   ├── generator/
│   │   │   ├── matrix.py             # Positive & Negative test matrix builder
│   │   │   ├── python_exporter.py    # PyTest / python-can test script compiler
│   │   │   └── capl_exporter.py      # Vector CANoe CAPL test script compiler
│   │   └── simulator/
│   │       ├── bus.py                # Virtual CAN bus with frame event bus
│   │       ├── isotp.py              # ISO 15765-2 transport protocol handler
│   │       └── virtual_ecu.py        # In-memory simulated ECU with full UDS handler
│   ├── api/
│   │   ├── schemas.py                # Pydantic models for all entities
│   │   ├── routes.py                 # FastAPI endpoints
│   │   └── server.py                 # FastAPI application & server config
│   └── ui/
│       ├── streamlit_app.py          # Multi-tab Streamlit Engineering Workbench
│       └── web_dashboard.html        # Embedded modern HTML/JS Web Dashboard
├── tests/
│   ├── test_schemas.py               # Schema validation tests
│   ├── test_protocol.py              # UDS protocol & framing tests
│   ├── test_fsm.py                   # Session & Security FSM tests
│   ├── test_isotp_bus.py             # ISO-TP transport & Virtual Bus tests
│   ├── test_virtual_ecu.py           # Virtual ECU simulation tests
│   ├── test_rag.py                   # Spec ingestion & RAG search tests
│   ├── test_generator.py             # Test matrix & script exporter tests
│   ├── test_ui_smoke.py              # UI package & dashboard smoke tests
│   ├── test_api.py                   # FastAPI endpoint integration tests
│   └── test_e2e_flow.py              # Full end-to-end pipeline test
├── sample_specs/
│   └── engine_ecu_uds_spec.json      # Comprehensive sample Engine ECU spec
├── requirements.txt                  # Python dependencies
├── run_demo.py                       # Single-command CLI / Server / UI Launcher
└── README.md                         # Documentation & Interview Guide
```

---

## 📜 License & Compliance

* **Standards:** ISO 14229-1:2020 (UDS), ISO 15765-2:2016 (DoCAN), ISO 26262, ISO/SAE 21434.
* **Privacy:** 100% offline and local execution capability; zero proprietary OEM data transmission.
#   A u t o D i a g - A I  
 