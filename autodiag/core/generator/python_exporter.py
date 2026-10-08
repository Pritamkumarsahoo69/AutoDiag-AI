"""Python PyTest / python-can Automated Diagnostic Test Script Exporter."""

from typing import List
from autodiag.api.schemas import DiagnosticDatabase, TestCaseModel


class PythonTestExporter:
    """Exports generated test case matrices to executable Python PyTest test suites."""

    @staticmethod
    def export(suite: List[TestCaseModel], spec: DiagnosticDatabase) -> str:
        code_lines = [
            '"""',
            f'Automated UDS PyTest Suite for {spec.ecu_name}',
            'Standard: ISO 14229 (UDS) / ISO 15765-2 (ISO-TP)',
            'Generated automatically by AutoDiag-AI',
            '"""',
            '',
            'import pytest',
            'import time',
            'from autodiag.core.simulator.bus import VirtualCANBus',
            'from autodiag.core.simulator.isotp import ISOTPTransport',
            'from autodiag.core.simulator.virtual_ecu import VirtualECU',
            'from autodiag.core.rag.parser import SpecParser',
            'from autodiag.core.protocol.constants import NRC, SID',
            '',
            '@pytest.fixture(scope="module")',
            'def ecu_fixture():',
            f'    spec = SpecParser.parse_file("sample_specs/engine_ecu_uds_spec.json")',
            '    bus = VirtualCANBus()',
            f'    ecu = VirtualECU(spec, bus, request_id={spec.can_request_id}, response_id={spec.can_response_id})',
            '    ecu.start()',
            f'    client = ISOTPTransport(bus, tx_id={spec.can_request_id}, rx_id={spec.can_response_id})',
            '    yield ecu, client',
            '    ecu.stop()',
            '    client.close()',
            '',
        ]

        for tc in suite:
            clean_func_name = "test_" + tc.name.lower().replace(" ", "_").replace("-", "_")
            code_lines.append(f'def {clean_func_name}(ecu_fixture):')
            code_lines.append(f'    """{tc.test_id}: {tc.description}"""')
            code_lines.append('    ecu, client = ecu_fixture')
            code_lines.append('')

            # Handle session setup
            if tc.session == "EXTENDED":
                code_lines.append('    # Ensure Extended Session')
                code_lines.append('    client.send(bytes.fromhex("1003"))')
                code_lines.append('    client.receive(timeout_sec=0.2)')
            elif tc.session == "PROGRAMMING":
                code_lines.append('    # Ensure Programming Session')
                code_lines.append('    client.send(bytes.fromhex("1003"))')
                code_lines.append('    client.receive(timeout_sec=0.2)')
                code_lines.append('    client.send(bytes.fromhex("1002"))')
                code_lines.append('    client.receive(timeout_sec=0.2)')
            elif tc.session == "DEFAULT":
                code_lines.append('    # Ensure Default Session')
                code_lines.append('    ecu.session_fsm.reset_to_default()')

            # Handle security setup
            if tc.security_level > 0 and tc.test_type == "POSITIVE":
                code_lines.append('    # Unlock Security Level 1')
                code_lines.append('    client.send(bytes.fromhex("2701"))')
                code_lines.append('    seed_resp = client.receive(timeout_sec=0.2)')
                code_lines.append('    if seed_resp and len(seed_resp) >= 6:')
                code_lines.append('        seed = seed_resp[2:]')
                code_lines.append(f'        key = bytes([b ^ {spec.security_seed_key_mask} for b in seed])')
                code_lines.append('        client.send(bytes.fromhex("2702") + key)')
                code_lines.append('        client.receive(timeout_sec=0.2)')

            # Send main test request
            code_lines.append(f'    # Send Test Request: {tc.request_hex}')
            code_lines.append(f'    client.send(bytes.fromhex("{tc.request_hex}"))')
            code_lines.append('    resp = client.receive(timeout_sec=0.5)')
            code_lines.append('')

            # Assertions
            if tc.expected_response_hex is not None:
                code_lines.append('    assert resp is not None, "ECU timed out without responding"')
                code_lines.append(f'    assert resp.startswith(bytes.fromhex("{tc.expected_response_hex}")), f"Expected response starting with {tc.expected_response_hex}, got {{resp.hex().upper()}}"')
            elif tc.expected_nrc is not None:
                nrc_int = int(tc.expected_nrc, 16)
                code_lines.append('    assert resp is not None, "ECU timed out without sending negative response"')
                code_lines.append(f'    assert resp[0] == 0x7F, f"Expected Negative Response (0x7F), got {{resp.hex().upper()}}"')
                code_lines.append(f'    assert resp[2] == {nrc_int}, f"Expected NRC {tc.expected_nrc}, got 0x{{resp[2]:02X}}"')
            else:
                # SuppressPosResponse check
                code_lines.append('    assert resp is None, "Expected response suppression (no frame), but received frame"')

            code_lines.append('')
            code_lines.append('')

        return "\n".join(code_lines)
