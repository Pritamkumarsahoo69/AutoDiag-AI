import pytest
from autodiag.api.schemas import (
    DIDSpec,
    DiagnosticDatabase,
    DiagnosticServiceSpec,
    RoutineSpec,
    TestCaseModel,
    TestExecutionResult,
    UDSMessage,
)

def test_did_spec_validation():
    did = DIDSpec(
        did_hex="0xF190",
        name="VIN",
        length_bytes=17,
        data_type="ASCII",
        access="READ_ONLY",
        description="Vehicle Identification Number",
        default_value="WVWZZZ3CZWE123456",
        security_level=0,
        allowed_sessions=["DEFAULT", "EXTENDED"]
    )
    assert did.did_hex == "0xF190"
    assert did.length_bytes == 17
    assert did.name == "VIN"
    assert did.data_type == "ASCII"

def test_uds_message_hex_payload():
    msg = UDSMessage(service_id=0x22, sub_function=None, payload=bytes.fromhex("F190"))
    assert msg.raw_bytes() == bytes.fromhex("22F190")

def test_uds_message_with_subfunction():
    msg = UDSMessage(service_id=0x10, sub_function=0x03, payload=b"")
    assert msg.raw_bytes() == bytes.fromhex("1003")

def test_diagnostic_database_validation():
    db = DiagnosticDatabase(
        ecu_name="Engine_Control_Unit",
        can_request_id="0x7E0",
        can_response_id="0x7E8",
        services=[
            DiagnosticServiceSpec(
                service_id=0x10,
                name="DiagnosticSessionControl",
                supported_subfunctions=[0x01, 0x02, 0x03],
                allowed_sessions=["DEFAULT", "EXTENDED", "PROGRAMMING"],
                requires_security=False
            ),
            DiagnosticServiceSpec(
                service_id=0x22,
                name="ReadDataByIdentifier",
                supported_subfunctions=[],
                allowed_sessions=["DEFAULT", "EXTENDED"],
                requires_security=False
            )
        ],
        dids=[
            DIDSpec(
                did_hex="0xF190",
                name="VIN",
                length_bytes=17,
                data_type="ASCII",
                access="READ_ONLY"
            )
        ],
        routines=[
            RoutineSpec(
                routine_id="0x0201",
                name="EraseMemory",
                supported_subfunctions=[0x01, 0x03],
                allowed_sessions=["PROGRAMMING"],
                requires_security=True,
                security_level=1
            )
        ]
    )
    assert db.ecu_name == "Engine_Control_Unit"
    assert len(db.services) == 2
    assert len(db.dids) == 1
    assert len(db.routines) == 1

def test_test_case_model():
    tc = TestCaseModel(
        test_id="TC_UDS_001",
        service_id=0x22,
        name="Read VIN Positive Test",
        description="Verify reading VIN returns 17-byte ASCII string",
        test_type="POSITIVE",
        session="DEFAULT",
        security_level=0,
        request_hex="22F190",
        expected_response_hex="62F1905756575A5A5A33435A5745313233343536",
        expected_nrc=None,
        preconditions=["ECU in Default Session"]
    )
    assert tc.test_id == "TC_UDS_001"
    assert tc.test_type == "POSITIVE"
