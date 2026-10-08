import json
import os
import pytest
from autodiag.core.generator.capl_exporter import CAPLTestExporter
from autodiag.core.generator.matrix import TestMatrixGenerator
from autodiag.core.generator.python_exporter import PythonTestExporter
from autodiag.core.protocol.constants import NRC
from autodiag.core.rag.knowledge_base import DiagnosticKnowledgeBase
from autodiag.core.rag.parser import SpecParser
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport
from autodiag.core.simulator.virtual_ecu import VirtualECU


def test_full_pipeline_ingest_to_simulation():
    # 1. Ingest specification
    spec_path = "C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json"
    spec = SpecParser.parse_file(spec_path)
    assert spec.ecu_name == "Engine_Control_Unit"
    assert len(spec.dids) >= 5

    # 2. Build RAG & Query Knowledge Base
    kb = DiagnosticKnowledgeBase()
    kb.load_database(spec, source_file="engine_ecu_uds_spec.json")
    query_resp = kb.answer_query("How is VIN DID read in default session?")
    assert "F190" in query_resp.answer.upper() or len(query_resp.citations) > 0

    # 3. Generate Positive and Negative Test Matrix
    suite = TestMatrixGenerator.generate_suite(spec)
    assert len(suite) >= 10
    pos_count = sum(1 for t in suite if t.test_type == "POSITIVE")
    neg_count = sum(1 for t in suite if t.test_type == "NEGATIVE_NRC")
    assert pos_count > 0 and neg_count > 0

    # 4. Run Test Matrix against Virtual ECU Simulator
    bus = VirtualCANBus()
    ecu = VirtualECU(spec, bus)
    ecu.start()

    client = ISOTPTransport(bus, tx_id=spec.request_id_int, rx_id=spec.response_id_int)

    passed_tests = 0
    failed_tests = 0

    try:
        for tc in suite:
            # Handle Preconditions
            if tc.session == "EXTENDED":
                client.send(bytes.fromhex("1003"))
                client.receive(timeout_sec=0.1)
            elif tc.session == "PROGRAMMING":
                client.send(bytes.fromhex("1003"))
                client.receive(timeout_sec=0.1)
                client.send(bytes.fromhex("1002"))
                client.receive(timeout_sec=0.1)
            elif tc.session == "DEFAULT":
                ecu.session_fsm.reset_to_default()

            if tc.security_level > 0 and tc.test_type == "POSITIVE":
                client.send(bytes.fromhex("2701"))
                seed_resp = client.receive(timeout_sec=0.1)
                if seed_resp and len(seed_resp) >= 6:
                    seed = seed_resp[2:]
                    key = bytes([b ^ spec.security_seed_key_mask for b in seed])
                    client.send(bytes.fromhex("2702") + key)
                    client.receive(timeout_sec=0.1)

            # Send Test Request
            client.send(bytes.fromhex(tc.request_hex))
            resp = client.receive(timeout_sec=0.4)

            actual_hex = resp.hex().upper() if resp else ""
            test_passed = False

            if tc.expected_response_hex is not None:
                test_passed = actual_hex.startswith(tc.expected_response_hex)
            elif tc.expected_nrc is not None:
                if resp and len(resp) >= 3 and resp[0] == 0x7F:
                    actual_nrc = f"0x{resp[2]:02X}"
                    test_passed = (actual_nrc.upper() == tc.expected_nrc.upper())
            else:
                # SuppressPosResponse expected
                test_passed = (resp is None)

            if test_passed:
                passed_tests += 1
            else:
                failed_tests += 1
    finally:
        ecu.stop()
        client.close()

    assert passed_tests == len(suite), f"Expected all {len(suite)} tests to pass, but {failed_tests} failed."

    # 5. Export Code Scripts
    py_code = PythonTestExporter.export(suite, spec)
    assert len(py_code) > 200
    assert "import pytest" in py_code

    capl_code = CAPLTestExporter.export(suite, spec)
    assert len(capl_code) > 200
    assert "Vector CANoe CAPL" in capl_code
