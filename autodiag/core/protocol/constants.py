"""ISO 14229 UDS Protocol Constants, SIDs, and Negative Response Codes (NRCs)."""

from enum import IntEnum, Enum


class SID(IntEnum):
    """ISO 14229 Service Identifiers."""
    # Diagnostic and Communication Management
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28
    AUTHENTICATION = 0x29
    TESTER_PRESENT = 0x3E
    ACCESS_TIMING_PARAMETER = 0x83
    SECURED_DATA_TRANSMISSION = 0x84
    CONTROL_DTC_SETTING = 0x85
    RESPONSE_ON_EVENT = 0x86
    LINK_CONTROL = 0x87

    # Data Transmission
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_MEMORY_BY_ADDRESS = 0x23
    READ_SCALING_DATA_BY_IDENTIFIER = 0x24
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    WRITE_MEMORY_BY_ADDRESS = 0x3D

    # Stored Data Transmission
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14
    READ_DTC_INFORMATION = 0x19

    # Input / Output Control
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F

    # Remote Activation of Routine
    ROUTINE_CONTROL = 0x31

    # Upload / Download
    REQUEST_DOWNLOAD = 0x34
    REQUEST_UPLOAD = 0x35
    TRANSFER_DATA = 0x36
    REQUEST_TRANSFER_EXIT = 0x37
    REQUEST_FILE_TRANSFER = 0x38

    # Negative Response SID
    NEGATIVE_RESPONSE = 0x7F


class NRC(IntEnum):
    """ISO 14229 Negative Response Codes."""
    POSITIVE_RESPONSE = 0x00
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    RESPONSE_TOO_LONG = 0x14
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION = 0x26
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    INVALID_KEY = 0x35
    EXCEED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F
    RPM_TOO_HIGH = 0x81
    RPM_TOO_LOW = 0x82
    ENGINE_IS_RUNNING = 0x83
    ENGINE_IS_NOT_RUNNING = 0x84
    RESPONSE_PENDING = 0x78


class DiagnosticSession(IntEnum):
    """Standard UDS Diagnostic Sessions (Service $10)."""
    DEFAULT = 0x01
    PROGRAMMING = 0x02
    EXTENDED = 0x03
    SAFETY_SYSTEM = 0x04


class SecurityState(str, Enum):
    """ECU Security State Machine States (Service $27)."""
    LOCKED = "LOCKED"
    SEED_REQUESTED = "SEED_REQUESTED"
    UNLOCKED_L1 = "UNLOCKED_L1"
    UNLOCKED_L2 = "UNLOCKED_L2"
    DELAY_LOCKED = "DELAY_LOCKED"


SERVICE_NAMES = {
    0x10: "DiagnosticSessionControl",
    0x11: "ECUReset",
    0x14: "ClearDiagnosticInformation",
    0x19: "ReadDTCInformation",
    0x22: "ReadDataByIdentifier",
    0x23: "ReadMemoryByAddress",
    0x27: "SecurityAccess",
    0x28: "CommunicationControl",
    0x2E: "WriteDataByIdentifier",
    0x2F: "InputOutputControlByIdentifier",
    0x31: "RoutineControl",
    0x34: "RequestDownload",
    0x35: "RequestUpload",
    0x36: "TransferData",
    0x37: "RequestTransferExit",
    0x3E: "TesterPresent",
    0x85: "ControlDTCSetting",
    0x7F: "NegativeResponse",
}

NRC_DESCRIPTIONS = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooLong",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceedNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x78: "requestCorrectlyReceived-ResponsePending",
    0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
}


def get_service_name(sid: int) -> str:
    """Retrieve service name by SID."""
    return SERVICE_NAMES.get(sid, f"UnknownService(0x{sid:02X})")


def get_nrc_description(nrc: int) -> str:
    """Retrieve human readable NRC description."""
    return NRC_DESCRIPTIONS.get(nrc, f"UnknownNRC(0x{nrc:02X})")
