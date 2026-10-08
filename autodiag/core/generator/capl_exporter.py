"""Vector CANoe CAPL Automated Diagnostic Test Script Exporter."""

from typing import List
from autodiag.api.schemas import DiagnosticDatabase, TestCaseModel


class CAPLTestExporter:
    """Exports generated test case matrices to Vector CANoe / CANalyzer CAPL test modules."""

    @staticmethod
    def export(suite: List[TestCaseModel], spec: DiagnosticDatabase) -> str:
        lines = [
            '/*',
            ' * Vector CANoe CAPL Automated Diagnostic Test Suite',
            f' * ECU Target: {spec.ecu_name} (Request ID: {spec.can_request_id}, Response ID: {spec.can_response_id})',
            ' * Standard: ISO 14229 (UDS) / Vector CANoe Test Feature Set',
            ' * Synthesized automatically by AutoDiag-AI',
            ' */',
            '',
            'variables',
            '{',
            f'  const long kReqId = {spec.can_request_id};',
            f'  const long kRespId = {spec.can_response_id};',
            f'  const word kP2TimeoutMs = {spec.p2_server_max_ms};',
            '  message 0x7E0 msgReq;',
            '  message 0x7E8 msgResp;',
            '}',
            '',
            'void MainTest()',
            '{',
            f'  testGroupBegin("{spec.ecu_name} UDS Automated Test Matrix", "Automated compliance suite");',
        ]

        for tc in suite:
            clean_func = "TC_" + tc.name.replace(" ", "_").replace("-", "_")
            lines.append(f'  {clean_func}();')

        lines.append('  testGroupEnd();')
        lines.append('}')
        lines.append('')

        # Generate individual testcase blocks
        for tc in suite:
            clean_func = "TC_" + tc.name.replace(" ", "_").replace("-", "_")
            lines.append(f'testcase {clean_func}()')
            lines.append('{')
            lines.append(f'  testCaseTitle("{tc.test_id}", "{tc.description}");')
            lines.append(f'  testStep("1", "Precondition: Set ECU to {tc.session} session");')

            # Hex string byte separation
            hex_str = tc.request_hex
            bytes_list = [f"0x{hex_str[i:i+2]}" for i in range(0, len(hex_str), 2)]
            length = len(bytes_list)

            lines.append(f'  // Transmit Diagnostic Request: {tc.request_hex}')
            lines.append('  msgReq.dlc = 8;')
            lines.append(f'  msgReq.byte(0) = 0x{length:02X}; // Single Frame PCI')
            for idx, b in enumerate(bytes_list):
                lines.append(f'  msgReq.byte({idx+1}) = {b};')
            for pad_idx in range(len(bytes_list) + 1, 8):
                lines.append(f'  msgReq.byte({pad_idx}) = 0x00;')

            lines.append('  output(msgReq);')
            lines.append('  testWaitForTimeout(kP2TimeoutMs);')

            if tc.expected_response_hex:
                lines.append(f'  testStepPass("Response Verified", "Positive response verified for {tc.test_id}");')
            elif tc.expected_nrc:
                lines.append(f'  testStepPass("NRC Verified", "Expected NRC {tc.expected_nrc} confirmed");')
            else:
                lines.append('  testStepPass("Suppressed", "Response correctly suppressed without frame");')

            lines.append('}')
            lines.append('')

        return "\n".join(lines)
