"""Deterministic ISO 14229 UDS Protocol Length and Rule Validator."""

from typing import Optional, Tuple
from autodiag.core.protocol.constants import NRC, SID


class UDSProtocolValidator:
    """Deterministic protocol rule and length checker."""

    @staticmethod
    def validate_request_length(service_id: int, payload: bytes) -> Tuple[bool, Optional[int]]:
        """Validate request payload length against minimum/maximum bytes required for standard SIDs."""
        # SID 0x22: ReadDataByIdentifier requires at least 2 bytes per DID
        if service_id == SID.READ_DATA_BY_IDENTIFIER:
            if len(payload) < 2 or len(payload) % 2 != 0:
                return False, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT

        # SID 0x2E: WriteDataByIdentifier requires at least 2 bytes DID + 1 byte data
        elif service_id == SID.WRITE_DATA_BY_IDENTIFIER:
            if len(payload) < 3:
                return False, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT

        # SID 0x31: RoutineControl requires 2 bytes Routine ID
        elif service_id == SID.ROUTINE_CONTROL:
            if len(payload) < 2:
                return False, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT

        # SID 0x14: ClearDiagnosticInformation requires 3 bytes Group/DTC
        elif service_id == SID.CLEAR_DIAGNOSTIC_INFORMATION:
            if len(payload) != 3:
                return False, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT

        return True, None

    # Alias for API compatibility
    validate_length = validate_request_length
