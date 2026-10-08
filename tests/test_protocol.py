import pytest
from autodiag.core.protocol.constants import (
    NRC,
    SID,
    DiagnosticSession,
    SecurityState,
    get_nrc_description,
    get_service_name,
)
from autodiag.core.protocol.frame import UDSFrameBuilder, UDSFrameParser
from autodiag.core.protocol.validator import UDSProtocolValidator

def test_parse_read_did_request():
    msg = UDSFrameParser.parse(bytes.fromhex("22F190"))
    assert msg.service_id == SID.READ_DATA_BY_IDENTIFIER
    assert msg.sub_function is None
    assert msg.payload == bytes.fromhex("F190")

def test_parse_diagnostic_session_request():
    msg = UDSFrameParser.parse(bytes.fromhex("1003"))
    assert msg.service_id == SID.DIAGNOSTIC_SESSION_CONTROL
    assert msg.sub_function == 0x03
    assert msg.payload == b""

def test_parse_security_access_request():
    msg = UDSFrameParser.parse(bytes.fromhex("2701"))
    assert msg.service_id == SID.SECURITY_ACCESS
    assert msg.sub_function == 0x01

    msg_key = UDSFrameParser.parse(bytes.fromhex("270211223344"))
    assert msg_key.service_id == SID.SECURITY_ACCESS
    assert msg_key.sub_function == 0x02
    assert msg_key.payload == bytes.fromhex("11223344")

def test_build_positive_response():
    resp = UDSFrameBuilder.build_positive_response(SID.READ_DATA_BY_IDENTIFIER, bytes.fromhex("F190414243"))
    assert resp == bytes.fromhex("62F190414243")

def test_build_negative_response():
    resp = UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)
    assert resp == bytes.fromhex("7F2231")

def test_validate_length_mismatch():
    valid, nrc = UDSProtocolValidator.validate_request_length(SID.READ_DATA_BY_IDENTIFIER, payload=bytes.fromhex("F1"))
    assert not valid
    assert nrc == NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT

    valid_ok, nrc_ok = UDSProtocolValidator.validate_request_length(SID.READ_DATA_BY_IDENTIFIER, payload=bytes.fromhex("F190"))
    assert valid_ok
    assert nrc_ok is None

def test_helper_descriptions():
    assert "ReadDataByIdentifier" in get_service_name(0x22)
    assert "requestOutOfRange" in get_nrc_description(0x31)
