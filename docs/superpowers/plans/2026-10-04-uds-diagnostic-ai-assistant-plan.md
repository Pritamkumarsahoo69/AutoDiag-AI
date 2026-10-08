# UDS Diagnostics & Automated Test Generation Assistant (AutoDiag-AI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, production-grade automotive diagnostic AI platform (AutoDiag-AI) featuring a deterministic ISO 14229 UDS protocol engine, FSM state machines, virtual ECU simulator, local RAG knowledge base, automated positive/negative test matrix generator, dual-target script exporter (Python PyTest & Vector CAPL), FastAPI REST/WebSocket backend, and an interactive Streamlit workbench.

**Architecture:** A Dual-Surface Modular Platform where a shared Core Protocol & Simulation engine powers both an asynchronous FastAPI service layer (REST + WebSockets) and an interactive Streamlit engineering workbench.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, Streamlit, ChromaDB, Sentence-Transformers, PyPDF/PDFPlumber, Pydantic, PyTest, Python-CAN / ISO-TP.

**Spec:** `docs/superpowers/specs/2026-10-04-uds-diagnostic-ai-assistant-design.md`

## Global Constraints
- Target standard: ISO 14229 (UDS) & ISO 15765-2 (ISO-TP)
- 100% deterministic protocol validation: Zero LLM hallucinations in raw hex frames, byte lengths, or NRC assignments
- Offline operation: Local embeddings (`all-MiniLM-L6-v2`) and local vector storage with zero external cloud requirements
- Dual export compatibility: Standalone executable PyTest (`python-can` + `can-isotp`) and Vector CANoe CAPL (`.can`/`.capl`)

## Review Focus
1. **Multi-Frame ISO-TP Segmentation/Reassembly:** Handling payload > 7 bytes with First Frame (FF), Flow Control (FC), and Consecutive Frames (CF) without buffer overruns.
2. **Security State Lockout & Penalty Enforcement:** Preventing unauthorized writes while correctly tracking failed seed-key attempts and time delays (NRC `0x35`, `0x36`, `0x37`).
3. **Session Reversion on S3 Timeout:** Reverting active Programming/Extended sessions to Default session when S3 timer expires.
4. **Negative Response Code Precedence:** Correctly prioritizing NRC `0x11` (ServiceNotSupported) vs `0x7F` (ServiceNotSupportedInActiveSession) vs `0x13` (IncorrectLength).
5. **ODX/PDF Extraction Robustness:** Gracefully handling malformed or incomplete diagnostic tables without crashing the parser.

---

### Task 1: Project Setup, Environment Scaffolding & Shared Schemas

**Files:**
- Create: `requirements.txt`
- Create: `autodiag/__init__.py`
- Create: `autodiag/api/schemas.py`
- Create: `sample_specs/engine_ecu_uds_spec.json`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces: Pydantic schemas for `UDSMessage`, `DiagnosticServiceSpec`, `DIDSpec`, `RoutineSpec`, `DiagnosticDatabase`, `TestCaseModel`, `TestExecutionResult`.

- [ ] **Step 1: Write the failing schema validation test**
```python
# tests/test_schemas.py
from autodiag.api.schemas import DIDSpec, DiagnosticDatabase, UDSMessage

def test_did_spec_validation():
    did = DIDSpec(did_hex="0xF190", name="VIN", length_bytes=17, data_type="ASCII", access="READ_ONLY")
    assert did.did_hex == "0xF190"
    assert did.length_bytes == 17

def test_uds_message_hex_payload():
    msg = UDSMessage(service_id=0x22, sub_function=None, payload=bytes.fromhex("F190"))
    assert msg.raw_bytes() == bytes.fromhex("22F190")
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_schemas.py`
Expected: FAIL (ModuleNotFoundError: No module named 'autodiag')

- [ ] **Step 3: Implement project scaffolding, `requirements.txt`, and `autodiag/api/schemas.py`**
Implement Pydantic models for services, DIDs, routines, test cases, and database representations.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_schemas.py`
Expected: PASS

- [ ] **Step 5: Create rich realistic sample spec in `sample_specs/engine_ecu_uds_spec.json`**
Include VIN (`0xF190`), Software ID (`0xF189`), Programming Date (`0xF199`), Engine RPM (`0x0100`), Coolant Temp (`0x0101`), Flash Routine (`0x0201`), Security Level 1, Sessions Default, Extended, and Programming.

- [ ] **Step 6: Commit**
`git add requirements.txt autodiag/ tests/ sample_specs/`
`git commit -m "feat: initialize project scaffolding, schemas, and sample specs"`

---

### Task 2: Deterministic UDS Protocol Core (Constants, Framing, & Validator)

**Files:**
- Create: `autodiag/core/protocol/constants.py`
- Create: `autodiag/core/protocol/frame.py`
- Create: `autodiag/core/protocol/validator.py`
- Test: `tests/test_protocol.py`

**Interfaces:**
- Consumes: `autodiag.api.schemas.UDSMessage`
- Produces: `UDSFrameParser.parse(data: bytes) -> UDSMessage`, `UDSFrameBuilder.build_positive_response(sid: int, data: bytes) -> bytes`, `UDSFrameBuilder.build_negative_response(sid: int, nrc: int) -> bytes`, `UDSProtocolValidator.validate_request_length(sid: int, payload: bytes) -> tuple[bool, int | None]`.

- [ ] **Step 1: Write the failing tests for frame parsing, building, and length validation**
```python
# tests/test_protocol.py
from autodiag.core.protocol.constants import NRC, SID
from autodiag.core.protocol.frame import UDSFrameBuilder, UDSFrameParser
from autodiag.core.protocol.validator import UDSProtocolValidator

def test_parse_read_did_request():
    msg = UDSFrameParser.parse(bytes.fromhex("22F190"))
    assert msg.service_id == SID.READ_DATA_BY_IDENTIFIER
    assert msg.payload == bytes.fromhex("F190")

def test_build_positive_response():
    resp = UDSFrameBuilder.build_positive_response(SID.READ_DATA_BY_IDENTIFIER, bytes.fromhex("F190414243"))
    assert resp == bytes.fromhex("62F190414243")

def test_build_negative_response():
    resp = UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)
    assert resp == bytes.fromhex("7F2231")

def test_validate_length_mismatch():
    valid, nrc = UDSProtocolValidator.validate_length(SID.READ_DATA_BY_IDENTIFIER, payload=bytes.fromhex("F1"))
    assert not valid
    assert nrc == NRC.INCORRECT_MESSAGE_LENGTH
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_protocol.py`
Expected: FAIL

- [ ] **Step 3: Implement `constants.py`, `frame.py`, and `validator.py`**
Define ISO 14229 SID enums ($0x10, 0x11, 0x22, 0x27, 0x2E, 0x31, 0x19, 0x3E, 0x85$), NRC enums, framing builders, and deterministic length validation rules.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_protocol.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/protocol/ tests/test_protocol.py`
`git commit -m "feat: implement UDS protocol constants, frame parser, and validator"`

---

### Task 3: Deterministic Session & Security Finite State Machines (FSM)

**Files:**
- Create: `autodiag/core/protocol/fsm.py`
- Test: `tests/test_fsm.py`

**Interfaces:**
- Produces: `DiagnosticSessionFSM(default_session=0x01, s3_timeout_sec=5.0)`, `SecurityAccessFSM(max_attempts=3, delay_timer_sec=10.0)`.

- [ ] **Step 1: Write the failing tests for session and security state machines**
```python
# tests/test_fsm.py
from autodiag.core.protocol.constants import DiagnosticSession, NRC, SecurityState
from autodiag.core.protocol.fsm import DiagnosticSessionFSM, SecurityAccessFSM

def test_session_fsm_transitions():
    fsm = DiagnosticSessionFSM()
    assert fsm.current_session == DiagnosticSession.DEFAULT
    assert fsm.transition_to(DiagnosticSession.EXTENDED) == (True, None)
    assert fsm.current_session == DiagnosticSession.EXTENDED
    assert fsm.is_service_allowed(0x2E, allowed_sessions=[DiagnosticSession.EXTENDED]) == (True, None)
    assert fsm.is_service_allowed(0x2E, allowed_sessions=[DiagnosticSession.PROGRAMMING]) == (False, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION)

def test_security_fsm_seed_key_flow():
    sec_fsm = SecurityAccessFSM(seed_generator=lambda: bytes.fromhex("11223344"), key_calculator=lambda s: bytes([b ^ 0xAA for b in s]))
    seed = sec_fsm.request_seed(level=1)
    assert seed == bytes.fromhex("11223344")
    assert sec_fsm.state == SecurityState.SEED_REQUESTED
    
    # Valid key unlocks
    valid_key = bytes([b ^ 0xAA for b in seed])
    success, nrc = sec_fsm.send_key(level=1, key=valid_key)
    assert success
    assert sec_fsm.is_unlocked(level=1)

def test_security_fsm_brute_force_lockout():
    sec_fsm = SecurityAccessFSM(max_attempts=2, seed_generator=lambda: bytes.fromhex("11223344"), key_calculator=lambda s: bytes.fromhex("99999999"))
    sec_fsm.request_seed(1)
    sec_fsm.send_key(1, bytes.fromhex("00000000")) # Fail 1
    sec_fsm.request_seed(1)
    success, nrc = sec_fsm.send_key(1, bytes.fromhex("00000000")) # Fail 2 -> Exceeded
    assert not success
    assert nrc == NRC.EXCEED_NUMBER_OF_ATTEMPTS
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_fsm.py`
Expected: FAIL

- [ ] **Step 3: Implement `autodiag/core/protocol/fsm.py`**
Implement state transitions, timers, seed-key verification, attempt counters, and NRC assignment rules.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_fsm.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/protocol/fsm.py tests/test_fsm.py`
`git commit -m "feat: implement UDS session and security finite state machines"`

---

### Task 4: ISO-TP (ISO 15765-2) Multi-Frame Transport Layer & Virtual CAN Bus

**Files:**
- Create: `autodiag/core/simulator/bus.py`
- Create: `autodiag/core/simulator/isotp.py`
- Test: `tests/test_isotp_bus.py`

**Interfaces:**
- Produces: `VirtualCANBus`, `ISOTPTransport(bus: VirtualCANBus, tx_id: int, rx_id: int)`.

- [ ] **Step 1: Write failing test for Single-Frame & Multi-Frame ISO-TP transmission**
```python
# tests/test_isotp_bus.py
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport

def test_isotp_single_frame():
    bus = VirtualCANBus()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    server = ISOTPTransport(bus, tx_id=0x7E8, rx_id=0x7E0)
    
    payload = bytes.fromhex("22F190")
    client.send(payload)
    received = server.receive(timeout_sec=0.5)
    assert received == payload

def test_isotp_multi_frame_segmentation():
    bus = VirtualCANBus()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    server = ISOTPTransport(bus, tx_id=0x7E8, rx_id=0x7E0)
    
    # 20-byte payload (> 7 bytes single frame limit)
    large_payload = bytes(range(20))
    client.send(large_payload)
    received = server.receive(timeout_sec=1.0)
    assert received == large_payload
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_isotp_bus.py`
Expected: FAIL

- [ ] **Step 3: Implement `bus.py` and `isotp.py`**
Implement the virtual bus with subscription listeners and the ISO 15765-2 state machine (SF, FF, FC, CF frame types with PCI parsing).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_isotp_bus.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/simulator/ tests/test_isotp_bus.py`
`git commit -m "feat: implement ISO-TP multi-frame transport and virtual CAN bus"`

---

### Task 5: In-Memory Virtual ECU Simulator

**Files:**
- Create: `autodiag/core/simulator/virtual_ecu.py`
- Test: `tests/test_virtual_ecu.py`

**Interfaces:**
- Consumes: `DiagnosticDatabase`, `VirtualCANBus`, `ISOTPTransport`, `DiagnosticSessionFSM`, `SecurityAccessFSM`
- Produces: `VirtualECU(config: DiagnosticDatabase, bus: VirtualCANBus)`.

- [ ] **Step 1: Write failing tests for Virtual ECU diagnostic handling**
```python
# tests/test_virtual_ecu.py
import json
from autodiag.api.schemas import DiagnosticDatabase
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport
from autodiag.core.simulator.virtual_ecu import VirtualECU

def test_virtual_ecu_read_vin():
    with open("sample_specs/engine_ecu_uds_spec.json", "r") as f:
        spec = DiagnosticDatabase(**json.load(f))
    
    bus = VirtualCANBus()
    ecu = VirtualECU(spec, bus, request_id=0x7E0, response_id=0x7E8)
    ecu.start()
    
    tester = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    tester.send(bytes.fromhex("22F190")) # Read VIN
    
    response = tester.receive(timeout_sec=1.0)
    assert response.startswith(bytes.fromhex("62F190"))
    ecu.stop()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_virtual_ecu.py`
Expected: FAIL

- [ ] **Step 3: Implement `autodiag/core/simulator/virtual_ecu.py`**
Implement full handling for SIDs $0x10, 0x11, 0x22, 0x27, 0x2E, 0x31, 0x14, 0x19, 0x3E, 0x85$ with stateful session and security checks.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_virtual_ecu.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/simulator/virtual_ecu.py tests/test_virtual_ecu.py`
`git commit -m "feat: implement in-memory virtual ECU simulator"`

---

### Task 6: Specification Ingestion & Local Vector Knowledge Engine

**Files:**
- Create: `autodiag/core/rag/parser.py`
- Create: `autodiag/core/rag/knowledge_base.py`
- Create: `autodiag/core/rag/vector_store.py`
- Test: `tests/test_rag.py`

**Interfaces:**
- Produces: `SpecParser.parse_file(file_path: str) -> DiagnosticDatabase`, `VectorStoreManager.index_spec(spec: DiagnosticDatabase)`, `VectorStoreManager.query(query_str: str) -> list[CitationResult]`.

- [ ] **Step 1: Write failing tests for spec parser and local semantic query**
```python
# tests/test_rag.py
from autodiag.core.rag.knowledge_base import DiagnosticKnowledgeBase
from autodiag.core.rag.parser import SpecParser

def test_parse_json_spec():
    db = SpecParser.parse_file("sample_specs/engine_ecu_uds_spec.json")
    assert db.ecu_name == "Engine_Control_Unit"
    assert "0xF190" in [d.did_hex for d in db.dids]

def test_query_knowledge_base():
    db = SpecParser.parse_file("sample_specs/engine_ecu_uds_spec.json")
    kb = DiagnosticKnowledgeBase()
    kb.load_database(db)
    results = kb.search("What is the DID for Vehicle Identification Number?")
    assert any("F190" in r.content for r in results)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_rag.py`
Expected: FAIL

- [ ] **Step 3: Implement `parser.py`, `knowledge_base.py`, and `vector_store.py`**
Implement multi-format parsing (JSON, PDF tables via `pdfplumber`), domain chunking, and local ChromaDB embeddings.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_rag.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/rag/ tests/test_rag.py`
`git commit -m "feat: implement diagnostic spec ingestion and RAG knowledge store"`

---

### Task 7: Automated Positive & Negative Test Matrix Generator & Dual-Script Exporter

**Files:**
- Create: `autodiag/core/generator/matrix.py`
- Create: `autodiag/core/generator/python_exporter.py`
- Create: `autodiag/core/generator/capl_exporter.py`
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `DiagnosticDatabase`
- Produces: `TestMatrixGenerator.generate_suite(spec: DiagnosticDatabase) -> list[TestCaseModel]`, `PythonTestExporter.export(suite: list[TestCaseModel]) -> str`, `CAPLTestExporter.export(suite: list[TestCaseModel]) -> str`.

- [ ] **Step 1: Write failing tests for matrix synthesis and script export**
```python
# tests/test_generator.py
from autodiag.core.generator.capl_exporter import CAPLTestExporter
from autodiag.core.generator.matrix import TestMatrixGenerator
from autodiag.core.generator.python_exporter import PythonTestExporter
from autodiag.core.rag.parser import SpecParser

def test_generate_test_matrix():
    spec = SpecParser.parse_file("sample_specs/engine_ecu_uds_spec.json")
    suite = TestMatrixGenerator.generate_suite(spec)
    
    # Must have both positive and negative tests
    types = {t.test_type for t in suite}
    assert "POSITIVE" in types
    assert "NEGATIVE_NRC" in types
    assert len(suite) >= 10

def test_export_python_and_capl():
    spec = SpecParser.parse_file("sample_specs/engine_ecu_uds_spec.json")
    suite = TestMatrixGenerator.generate_suite(spec)
    
    py_code = PythonTestExporter.export(suite)
    assert "import pytest" in py_code
    assert "def test_read_vin" in py_code.lower()
    
    capl_code = CAPLTestExporter.export(suite)
    assert "testcase" in capl_code
    assert "diagSendRequest" in capl_code
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_generator.py`
Expected: FAIL

- [ ] **Step 3: Implement `matrix.py`, `python_exporter.py`, and `capl_exporter.py`**
Implement the test matrix synthesis engine and clean code formatters for both PyTest and Vector CAPL.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_generator.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/core/generator/ tests/test_generator.py`
`git commit -m "feat: implement test matrix generator and dual-target script exporter"`

---

### Task 8: FastAPI REST Application & WebSocket Live Frame Stream

**Files:**
- Create: `autodiag/api/routes.py`
- Create: `autodiag/api/server.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Produces: FastAPI app with `/api/v1/specs/upload`, `/api/v1/query`, `/api/v1/tests/generate`, `/api/v1/tests/execute`, `/api/v1/export/{format}`, `/ws/can`.

- [ ] **Step 1: Write failing tests for FastAPI endpoints**
```python
# tests/test_api.py
import pytest
from autodiag.api.server import create_app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_generate_and_execute(client):
    with open("sample_specs/engine_ecu_uds_spec.json", "rb") as f:
        resp = client.post("/api/v1/specs/upload", files={"file": ("spec.json", f, "application/json")})
    assert resp.status_code == 200
    
    gen_resp = client.post("/api/v1/tests/generate")
    assert gen_resp.status_code == 200
    tests = gen_resp.json()["test_cases"]
    assert len(tests) > 0
    
    exec_resp = client.post("/api/v1/tests/execute")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["summary"]["total"] == len(tests)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_api.py`
Expected: FAIL

- [ ] **Step 3: Implement `autodiag/api/routes.py` and `autodiag/api/server.py`**
Implement REST endpoints, WebSocket connection manager, background test executor, and file export handlers.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_api.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/api/ tests/test_api.py`
`git commit -m "feat: implement FastAPI REST endpoints and WebSocket frame stream"`

---

### Task 9: Streamlit Engineering Workbench & Web Dashboard

**Files:**
- Create: `autodiag/ui/streamlit_app.py`
- Create: `autodiag/ui/web_dashboard.html`
- Test: `tests/test_ui_smoke.py`

**Interfaces:**
- Produces: Interactive Streamlit UI and modern standalone Web Dashboard.

- [ ] **Step 1: Write smoke test verifying UI components load without syntax or runtime import errors**
```python
# tests/test_ui_smoke.py
def test_streamlit_imports():
    import autodiag.ui.streamlit_app
    assert hasattr(autodiag.ui.streamlit_app, "main")
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_ui_smoke.py`
Expected: FAIL

- [ ] **Step 3: Implement `autodiag/ui/streamlit_app.py` with multi-tab layout and `web_dashboard.html`**
  - Tab 1: Spec & Knowledge Center (Interactive table of DIDs/Services).
  - Tab 2: Natural Language Diagnostic Assistant (Semantic search with citations).
  - Tab 3: Automated Test Matrix & FSM Designer (Positive & Negative selector).
  - Tab 4: Live Virtual ECU Test Bench & Frame Sniffer (Real-time hex frame display).
  - Tab 5: Script & Report Exporter (PyTest and CAPL code downloaders).

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_ui_smoke.py`
Expected: PASS

- [ ] **Step 5: Commit**
`git add autodiag/ui/ tests/test_ui_smoke.py`
`git commit -m "feat: implement Streamlit workbench and web dashboard"`

---

### Task 10: Complete System Integration, End-to-End Evaluation, and Documentation

**Files:**
- Create: `README.md`
- Create: `tests/test_e2e_flow.py`
- Create: `run_demo.py`

**Interfaces:**
- Produces: Single-command demo script `python run_demo.py`, comprehensive test suite, and placement interview presentation guide.

- [ ] **Step 1: Write End-to-End system verification test**
```python
# tests/test_e2e_flow.py
def test_full_pipeline_ingest_to_simulation():
    # 1. Ingest spec
    # 2. Build RAG & Query
    # 3. Generate test matrix
    # 4. Run against Virtual ECU
    # 5. Export Python & CAPL scripts
    # 6. Verify 100% positive pass rate & accurate negative NRC assertions
```

- [ ] **Step 2: Run full PyTest test suite**
Run: `pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 3: Implement `run_demo.py` and `README.md`**
Provide complete architectural documentation, step-by-step interview presentation talk track, and runnable demonstration launcher.

- [ ] **Step 4: Commit**
`git add README.md run_demo.py tests/test_e2e_flow.py`
`git commit -m "feat: complete end-to-end integration, demo runner, and interview guide"`
