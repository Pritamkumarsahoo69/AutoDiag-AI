"""UDS Request and Response frame encoders and decoders."""

from typing import Optional
from autodiag.api.schemas import UDSMessage
from autodiag.core.protocol.constants import SID, NRC


# SIDs that require a sub-function byte as the second byte in the request
SERVICES_WITH_SUBFUNCTION = {
    SID.DIAGNOSTIC_SESSION_CONTROL,   # 0x10
    SID.ECU_RESET,                    # 0x11
    SID.SECURITY_ACCESS,              # 0x27
    SID.COMMUNICATION_CONTROL,        # 0x28
    SID.TESTER_PRESENT,               # 0x3E
    SID.CONTROL_DTC_SETTING,          # 0x85
    SID.ROUTINE_CONTROL,              # 0x31
    SID.READ_DTC_INFORMATION,         # 0x19
    SID.ACCESS_TIMING_PARAMETER,      # 0x83
}


class UDSFrameParser:
    """Parses raw UDS byte payloads into structured UDSMessage objects."""

    @staticmethod
    def parse(data: bytes) -> UDSMessage:
        if not data:
            raise ValueError("Cannot parse empty UDS byte frame")

        service_id = data[0]

        # Check if service takes a subfunction
        if service_id in SERVICES_WITH_SUBFUNCTION and len(data) >= 2:
            sub_function = data[1]
            payload = data[2:]
        else:
            sub_function = None
            payload = data[1:]

        return UDSMessage(
            service_id=service_id,
            sub_function=sub_function,
            payload=payload
        )


class UDSFrameBuilder:
    """Builds raw byte frames for UDS positive and negative responses."""

    @staticmethod
    def build_positive_response(service_id: int, payload: bytes = b"", sub_function: Optional[int] = None) -> bytes:
        """Construct positive response: SID + 0x40, optional subfunction, payload."""
        response_sid = (service_id + 0x40) & 0xFF
        buf = bytearray([response_sid])
        if sub_function is not None:
            buf.append(sub_function)
        buf.extend(payload)
        return bytes(buf)

    @staticmethod
    def build_negative_response(service_id: int, nrc: int) -> bytes:
        """Construct standard 3-byte Negative Response: 0x7F <Requested_SID> <NRC>."""
        return bytes([SID.NEGATIVE_RESPONSE, service_id & 0xFF, nrc & 0xFF])
