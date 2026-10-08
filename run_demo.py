"""AutoDiag-AI: Interactive Demonstration Launcher and CLI Test Bench Runner."""

import argparse
import os
import sys
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from autodiag.core.generator.capl_exporter import CAPLTestExporter
from autodiag.core.generator.matrix import TestMatrixGenerator
from autodiag.core.generator.python_exporter import PythonTestExporter
from autodiag.core.rag.knowledge_base import DiagnosticKnowledgeBase
from autodiag.core.rag.parser import SpecParser
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport
from autodiag.core.simulator.virtual_ecu import VirtualECU


def run_cli_demo():
    print("=" * 78)
    print(" 🚗 AutoDiag-AI: Automotive UDS Diagnostics & Automated Test Generator")
    print(" Standard: ISO 14229 (UDS) | Transport: ISO 15765-2 (DoCAN / ISO-TP)")
    print("=" * 78)

    sample_spec_path = os.path.join(os.path.dirname(__file__), "sample_specs", "engine_ecu_uds_spec.json")
    print(f"\n[1] Ingesting Diagnostic Specification: {sample_spec_path}...")
    spec = SpecParser.parse_file(sample_spec_path)
    print(f"    ECU Name:         {spec.ecu_name}")
    print(f"    Physical CAN ID:  Request={spec.can_request_id} | Response={spec.can_response_id}")
    print(f"    Services Loaded:  {len(spec.services)} services ($10, $11, $22, $27, $2E, $31, $14, $19, $3E)")
    print(f"    DIDs Loaded:      {len(spec.dids)} parameters (VIN, PartNo, SW Version, RPM, Temp, etc.)")

    print("\n[2] Initializing RAG Diagnostic Knowledge Base...")
    kb = DiagnosticKnowledgeBase()
    kb.load_database(spec)
    print("    Local semantic indexing completed.")

    # Sample query
    test_q = "What are the security and session prerequisites for writing DID 0x0200?"
    print(f"\n[3] Testing Natural Language AI Query: '{test_q}'")
    ans = kb.answer_query(test_q)
    print(f"    Answer:\n    {ans.answer[:280]}...")
    if ans.citations:
        print(f"    Citation: [{ans.citations[0].section}] in {ans.citations[0].source_file}")

    print("\n[4] Generating Positive & Negative Diagnostic Test Matrix...")
    suite = TestMatrixGenerator.generate_suite(spec)
    print(f"    Synthesized {len(suite)} total test cases:")
    pos_cnt = sum(1 for t in suite if t.test_type == "POSITIVE")
    neg_cnt = sum(1 for t in suite if t.test_type == "NEGATIVE_NRC")
    sec_cnt = sum(1 for t in suite if t.test_type == "SECURITY_ACCESS")
    print(f"    - Positive Functional Tests:   {pos_cnt}")
    print(f"    - Negative Robustness (NRCs):  {neg_cnt}")
    print(f"    - Security Seed-Key Tests:     {sec_cnt}")

    print("\n[5] Executing Test Suite against In-Memory Virtual ECU Simulator...")
    bus = VirtualCANBus()
    ecu = VirtualECU(spec, bus)
    ecu.start()

    client = ISOTPTransport(bus, tx_id=spec.request_id_int, rx_id=spec.response_id_int)
    passed = 0

    print("    " + "-" * 70)
    print(f"    {'Test ID':<12} {'Type':<15} {'Request':<10} {'Outcome':<18} {'Status'}")
    print("    " + "-" * 70)

    try:
        for tc in suite:
            # Preconditions
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

            # Send request
            client.send(bytes.fromhex(tc.request_hex))
            resp = client.receive(timeout_sec=0.3)

            actual_hex = resp.hex().upper() if resp else ""
            tc_pass = False

            if tc.expected_response_hex is not None:
                tc_pass = actual_hex.startswith(tc.expected_response_hex)
                outcome = f"Resp 0x{actual_hex[:6]}..."
            elif tc.expected_nrc is not None:
                if resp and len(resp) >= 3 and resp[0] == 0x7F:
                    nrc_hex = f"0x{resp[2]:02X}"
                    tc_pass = (nrc_hex.upper() == tc.expected_nrc.upper())
                    outcome = f"NRC {nrc_hex}"
                else:
                    outcome = "Wrong format"
            else:
                tc_pass = (resp is None)
                outcome = "Suppressed"

            status_str = "✅ PASS" if tc_pass else "❌ FAIL"
            if tc_pass:
                passed += 1

            print(f"    {tc.test_id:<12} {tc.test_type:<15} {tc.request_hex:<10} {outcome:<18} {status_str}")
    finally:
        ecu.stop()
        client.close()

    print("    " + "-" * 70)
    print(f"\n[6] Simulation Complete: {passed}/{len(suite)} Tests Passed ({round(passed/len(suite)*100, 1)}% Pass Rate)")

    print("\n[7] Exporting Multi-Target Automated Test Scripts...")
    py_code = PythonTestExporter.export(suite, spec)
    capl_code = CAPLTestExporter.export(suite, spec)

    py_out = "test_engine_ecu_uds_generated.py"
    capl_out = "engine_ecu_uds_tests_generated.can"

    with open(py_out, "w", encoding="utf-8") as f:
        f.write(py_code)
    with open(capl_out, "w", encoding="utf-8") as f:
        f.write(capl_code)

    print(f"    -> Exported PyTest Suite:       {py_out} ({len(py_code)} bytes)")
    print(f"    -> Exported Vector CAPL Script: {capl_out} ({len(capl_code)} bytes)")

    print("\n" + "=" * 78)
    print(" 🎉 DEMONSTRATION COMPLETE - Ready for Evaluation & Testing!")
    print(" To launch Web Dashboard:   python run_demo.py --server")
    print(" To launch Streamlit UI:    python run_demo.py --streamlit")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="AutoDiag-AI Platform Launcher")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI Web Dashboard & REST Server")
    parser.add_argument("--streamlit", action="store_true", help="Launch Streamlit Interactive Workbench")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()

    if args.server:
        import uvicorn
        from autodiag.api.server import create_app
        print(f"🚀 Starting AutoDiag-AI FastAPI Server on http://localhost:{args.port}...")
        uvicorn.run(create_app(), host="127.0.0.1", port=args.port)
    elif args.streamlit:
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), "autodiag", "ui", "streamlit_app.py")
        print("🚀 Starting AutoDiag-AI Streamlit Workbench...")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, "-m", "streamlit", "run", script_path], env=env)
    else:
        run_cli_demo()


if __name__ == "__main__":
    main()
