"""Automated Positive and Negative UDS Test Matrix Generator."""

from typing import List
from autodiag.api.schemas import DiagnosticDatabase, TestCaseModel
from autodiag.core.protocol.constants import NRC, SID


class TestMatrixGenerator:
    """Synthesizes comprehensive positive and negative test case matrices for an ECU."""

    @staticmethod
    def generate_suite(spec: DiagnosticDatabase) -> List[TestCaseModel]:
        test_cases: List[TestCaseModel] = []
        tc_counter = 1

        # -------------------------------------------------------------
        # 1. DiagnosticSessionControl ($10) Tests
        # -------------------------------------------------------------
        # Positive: Extended Session
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.DIAGNOSTIC_SESSION_CONTROL,
            name="SessionControl_Extended_Positive",
            description="Verify switching to Extended Diagnostic Session returns positive response (0x50 0x03)",
            test_type="POSITIVE",
            session="DEFAULT",
            security_level=0,
            request_hex="1003",
            expected_response_hex="5003",
            expected_nrc=None,
            preconditions=["ECU initialized in Default Session"],
            pass_criteria="ECU responds with 0x50 0x03 and session timing parameters"
        ))
        tc_counter += 1

        # Negative: Invalid Subfunction (e.g. 0x99) -> NRC 0x12
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.DIAGNOSTIC_SESSION_CONTROL,
            name="SessionControl_InvalidSubFunction_NRC12",
            description="Verify requesting unassigned session subfunction 0x99 yields NRC 0x12",
            test_type="NEGATIVE_NRC",
            session="DEFAULT",
            security_level=0,
            request_hex="1099",
            expected_response_hex=None,
            expected_nrc="0x12",
            preconditions=["ECU in Default Session"],
            pass_criteria="ECU rejects request with NRC 0x12 (subFunctionNotSupported)"
        ))
        tc_counter += 1

        # Positive: Suppress Positive Response bit handling ($10 $83)
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.DIAGNOSTIC_SESSION_CONTROL,
            name="SessionControl_SuppressPosRsp_Positive",
            description="Verify session transition with SuppressPosRsp bit set (0x10 0x83) transitions without response frame",
            test_type="POSITIVE",
            session="DEFAULT",
            security_level=0,
            request_hex="1083",
            expected_response_hex=None,
            expected_nrc=None,
            preconditions=["ECU in Default Session"],
            pass_criteria="ECU transitions to Extended session with NO response frame"
        ))
        tc_counter += 1

        # -------------------------------------------------------------
        # 2. SecurityAccess ($27) Tests
        # -------------------------------------------------------------
        # Positive: Request Seed Level 1 in Extended session
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.SECURITY_ACCESS,
            name="SecurityAccess_RequestSeed_L1_Positive",
            description="Verify requesting Level 1 Seed (0x27 0x01) in Extended session returns 4-byte seed",
            test_type="SECURITY_ACCESS",
            session="EXTENDED",
            security_level=0,
            request_hex="2701",
            expected_response_hex="6701",
            expected_nrc=None,
            preconditions=["ECU in Extended Session (10 03)"],
            pass_criteria="ECU returns positive response 0x67 0x01 with 4 seed bytes"
        ))
        tc_counter += 1

        # Negative: Send wrong key -> NRC 0x35 (invalidKey)
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.SECURITY_ACCESS,
            name="SecurityAccess_InvalidKey_NRC35",
            description="Verify sending invalid key after seed request returns NRC 0x35",
            test_type="NEGATIVE_NRC",
            session="EXTENDED",
            security_level=0,
            request_hex="270200000000",
            expected_response_hex=None,
            expected_nrc="0x35",
            preconditions=["ECU in Extended Session", "Seed requested via 27 01"],
            pass_criteria="ECU rejects with NRC 0x35 (invalidKey)"
        ))
        tc_counter += 1

        # -------------------------------------------------------------
        # 3. ReadDataByIdentifier ($22) Tests for all DIDs
        # -------------------------------------------------------------
        for did in spec.dids:
            clean_did_hex = did.did_hex.replace("0x", "").replace("0X", "").upper()
            # Positive Read
            test_cases.append(TestCaseModel(
                test_id=f"TC_UDS_{tc_counter:03d}",
                service_id=SID.READ_DATA_BY_IDENTIFIER,
                name=f"ReadDID_{did.name}_Positive",
                description=f"Verify reading {did.name} ({did.did_hex}) returns positive response (0x62 {clean_did_hex}) and {did.length_bytes} bytes",
                test_type="POSITIVE",
                session=did.allowed_sessions[0] if did.allowed_sessions else "DEFAULT",
                security_level=did.security_level,
                request_hex=f"22{clean_did_hex}",
                expected_response_hex=f"62{clean_did_hex}",
                expected_nrc=None,
                preconditions=[f"ECU in {did.allowed_sessions[0]} session"],
                pass_criteria=f"ECU returns positive response starting with 62 {clean_did_hex}"
            ))
            tc_counter += 1

        # Negative: Read Undefined DID (0xFFFF) -> NRC 0x31 (requestOutOfRange)
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.READ_DATA_BY_IDENTIFIER,
            name="ReadDID_UndefinedDID_NRC31",
            description="Verify reading non-existent DID 0xFFFF yields NRC 0x31",
            test_type="NEGATIVE_NRC",
            session="DEFAULT",
            security_level=0,
            request_hex="22FFFF",
            expected_response_hex=None,
            expected_nrc="0x31",
            preconditions=["ECU in Default Session"],
            pass_criteria="ECU rejects request with NRC 0x31 (requestOutOfRange)"
        ))
        tc_counter += 1

        # Negative: Truncated Read DID request (1 byte instead of 2) -> NRC 0x13
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=SID.READ_DATA_BY_IDENTIFIER,
            name="ReadDID_TruncatedLength_NRC13",
            description="Verify malformed 1-byte DID request (0x22 0xF1) yields NRC 0x13",
            test_type="NEGATIVE_NRC",
            session="DEFAULT",
            security_level=0,
            request_hex="22F1",
            expected_response_hex=None,
            expected_nrc="0x13",
            preconditions=["ECU in Default Session"],
            pass_criteria="ECU rejects request with NRC 0x13 (incorrectMessageLengthOrInvalidFormat)"
        ))
        tc_counter += 1

        # -------------------------------------------------------------
        # 4. WriteDataByIdentifier ($2E) Tests
        # -------------------------------------------------------------
        writeable_dids = [d for d in spec.dids if d.access in ("WRITE_ONLY", "READ_WRITE")]
        for did in writeable_dids:
            clean_did_hex = did.did_hex.replace("0x", "").replace("0X", "").upper()
            dummy_payload = ("AA" * did.length_bytes)

            # Negative: Write in Default session without security -> NRC 0x7F or 0x33
            test_cases.append(TestCaseModel(
                test_id=f"TC_UDS_{tc_counter:03d}",
                service_id=SID.WRITE_DATA_BY_IDENTIFIER,
                name=f"WriteDID_{did.name}_WrongSession_NRC7F",
                description=f"Verify writing {did.name} in Default session fails with NRC 0x7F",
                test_type="NEGATIVE_NRC",
                session="DEFAULT",
                security_level=0,
                request_hex=f"2E{clean_did_hex}{dummy_payload}",
                expected_response_hex=None,
                expected_nrc="0x7F",
                preconditions=["ECU in Default Session"],
                pass_criteria="ECU rejects write with NRC 0x7F (serviceNotSupportedInActiveSession)"
            ))
            tc_counter += 1

            # Positive: Write in Extended session + Unlocked state
            test_cases.append(TestCaseModel(
                test_id=f"TC_UDS_{tc_counter:03d}",
                service_id=SID.WRITE_DATA_BY_IDENTIFIER,
                name=f"WriteDID_{did.name}_Positive",
                description=f"Verify writing {did.name} in Extended Session with Level {did.security_level} unlocked succeeds",
                test_type="POSITIVE",
                session="EXTENDED",
                security_level=did.security_level,
                request_hex=f"2E{clean_did_hex}{dummy_payload}",
                expected_response_hex=f"6E{clean_did_hex}",
                expected_nrc=None,
                preconditions=["ECU in Extended session", f"Security Level {did.security_level} unlocked"],
                pass_criteria=f"ECU confirms write with 6E {clean_did_hex}"
            ))
            tc_counter += 1

        # -------------------------------------------------------------
        # 5. RoutineControl ($31) Tests
        # -------------------------------------------------------------
        for r in spec.routines:
            clean_rid_hex = r.routine_id.replace("0x", "").replace("0X", "").upper()
            start_payload = "00000000" if r.start_payload_length > 0 else ""

            # Positive: Start Routine in authorized session
            test_cases.append(TestCaseModel(
                test_id=f"TC_UDS_{tc_counter:03d}",
                service_id=SID.ROUTINE_CONTROL,
                name=f"RoutineControl_Start_{r.name}_Positive",
                description=f"Verify starting routine {r.name} ({r.routine_id}) returns positive response (0x71 0x01 {clean_rid_hex})",
                test_type="POSITIVE",
                session=r.allowed_sessions[0] if r.allowed_sessions else "EXTENDED",
                security_level=r.security_level if r.requires_security else 0,
                request_hex=f"3101{clean_rid_hex}{start_payload}",
                expected_response_hex=f"7101{clean_rid_hex}",
                expected_nrc=None,
                preconditions=[f"ECU in {r.allowed_sessions[0]} session", f"Security Level {r.security_level} unlocked"],
                pass_criteria=f"ECU returns positive response 71 01 {clean_rid_hex}"
            ))
            tc_counter += 1

        # -------------------------------------------------------------
        # 6. Unimplemented Service -> NRC 0x11
        # -------------------------------------------------------------
        test_cases.append(TestCaseModel(
            test_id=f"TC_UDS_{tc_counter:03d}",
            service_id=0x99,
            name="General_UnknownService_NRC11",
            description="Verify sending unassigned service 0x99 yields NRC 0x11",
            test_type="NEGATIVE_NRC",
            session="DEFAULT",
            security_level=0,
            request_hex="9900",
            expected_response_hex=None,
            expected_nrc="0x11",
            preconditions=["ECU in Default Session"],
            pass_criteria="ECU rejects with NRC 0x11 (serviceNotSupported)"
        ))

        return test_cases
