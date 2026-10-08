"""Pydantic schemas and data models for AutoDiag-AI."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UDSMessage(BaseModel):
    """Represents a decoded or encoded UDS request or response frame."""
    service_id: int = Field(..., description="Service Identifier (SID) in hex/int, e.g. 0x22")
    sub_function: Optional[int] = Field(None, description="Sub-function byte if applicable, e.g. 0x01")
    payload: bytes = Field(default=b"", description="Payload bytes excluding SID and Subfunction")

    def raw_bytes(self) -> bytes:
        """Serialize into raw UDS byte stream."""
        data = bytearray([self.service_id])
        if self.sub_function is not None:
            data.append(self.sub_function)
        data.extend(self.payload)
        return bytes(data)

    def hex_str(self) -> str:
        """Return formatted hex string."""
        return self.raw_bytes().hex().upper()


class DIDSpec(BaseModel):
    """Specification for a Data Identifier (DID, Service $22 / $2E)."""
    did_hex: str = Field(..., description="2-byte DID in hex string, e.g. '0xF190'")
    name: str = Field(..., description="Human readable name, e.g. 'VIN'")
    length_bytes: int = Field(..., description="Length of data in bytes")
    data_type: str = Field(default="HEX", description="ASCII, HEX, UINT8, UINT16, UINT32, BCD")
    access: str = Field(default="READ_ONLY", description="READ_ONLY, WRITE_ONLY, READ_WRITE")
    description: str = Field(default="", description="Detailed description")
    default_value: str = Field(default="", description="Default simulated value (ASCII or hex)")
    security_level: int = Field(default=0, description="0 = No security required, 1 = Level 1, etc.")
    allowed_sessions: List[str] = Field(
        default_factory=lambda: ["DEFAULT", "EXTENDED"],
        description="Sessions where this DID is accessible"
    )

    @property
    def did_int(self) -> int:
        """Integer representation of DID hex."""
        return int(self.did_hex, 16)


class RoutineSpec(BaseModel):
    """Specification for a Routine Identifier (RID, Service $31)."""
    routine_id: str = Field(..., description="2-byte Routine ID in hex string, e.g. '0x0201'")
    name: str = Field(..., description="Routine Name, e.g. 'EraseMemory'")
    supported_subfunctions: List[int] = Field(
        default_factory=lambda: [0x01, 0x03],
        description="0x01: Start, 0x02: Stop, 0x03: RequestResults"
    )
    start_payload_length: int = Field(default=0, description="Required start routine parameter bytes")
    allowed_sessions: List[str] = Field(
        default_factory=lambda: ["EXTENDED", "PROGRAMMING"],
        description="Sessions where this routine is supported"
    )
    requires_security: bool = Field(default=False)
    security_level: int = Field(default=1)
    description: str = Field(default="")

    @property
    def routine_int(self) -> int:
        return int(self.routine_id, 16)


class DiagnosticServiceSpec(BaseModel):
    """Specification for an ISO 14229 Service supported by an ECU."""
    service_id: int = Field(..., description="UDS Service ID, e.g. 0x10, 0x22, 0x27")
    name: str = Field(..., description="Service Name, e.g. 'DiagnosticSessionControl'")
    supported_subfunctions: List[int] = Field(default_factory=list)
    allowed_sessions: List[str] = Field(default_factory=lambda: ["DEFAULT", "EXTENDED", "PROGRAMMING"])
    requires_security: bool = Field(default=False)
    security_level: int = Field(default=0)
    description: str = Field(default="")


class DiagnosticDatabase(BaseModel):
    """Normalized specification database for an ECU."""
    ecu_name: str = Field(default="Vehicle_ECU", description="Name of the ECU")
    can_request_id: str = Field(default="0x7E0", description="CAN Physical Request ID")
    can_response_id: str = Field(default="0x7E8", description="CAN Physical Response ID")
    can_functional_id: str = Field(default="0x7DF", description="CAN Functional Request ID")
    p2_server_max_ms: int = Field(default=50, description="P2 Server Max timeout in ms")
    p2_star_server_max_ms: int = Field(default=5000, description="P2* Server Max timeout in ms")
    s3_server_timeout_ms: int = Field(default=5000, description="S3 Server timeout in ms")
    services: List[DiagnosticServiceSpec] = Field(default_factory=list)
    dids: List[DIDSpec] = Field(default_factory=list)
    routines: List[RoutineSpec] = Field(default_factory=list)
    security_seed_key_mask: int = Field(default=0xAA, description="Mock security XOR mask")

    @property
    def request_id_int(self) -> int:
        return int(self.can_request_id, 16)

    @property
    def response_id_int(self) -> int:
        return int(self.can_response_id, 16)

    @property
    def functional_id_int(self) -> int:
        return int(self.can_functional_id, 16)


class TestCaseModel(BaseModel):
    """Represents a generated test case."""
    __test__ = False
    test_id: str = Field(..., description="Unique Test ID, e.g. 'TC_UDS_001'")
    service_id: int = Field(..., description="UDS Service ID tested")
    name: str = Field(..., description="Short descriptive test name")
    description: str = Field(default="")
    test_type: str = Field(..., description="POSITIVE, NEGATIVE_NRC, SESSION_TRANSITION, SECURITY_ACCESS, TIMING")
    session: str = Field(default="DEFAULT", description="Target session state for test")
    security_level: int = Field(default=0, description="Required security level")
    request_hex: str = Field(..., description="Hex string of request bytes, e.g. '22F190'")
    expected_response_hex: Optional[str] = Field(None, description="Expected positive response hex or None")
    expected_nrc: Optional[str] = Field(None, description="Expected NRC in hex string, e.g. '0x31', '0x7E', or None")
    preconditions: List[str] = Field(default_factory=list)
    pass_criteria: str = Field(default="ECU returns expected response frame or expected NRC")


class CANFrameModel(BaseModel):
    """Sniffed CAN frame for real-time telemetry."""
    timestamp: float
    can_id: str
    direction: str  # "TX" or "RX"
    dlc: int
    data_hex: str
    decoded_uds: str = ""
    status: str = "INFO"  # "OK", "NRC", "ERROR", "INFO"


class TestExecutionResult(BaseModel):
    """Result of running a single test case."""
    __test__ = False
    test_id: str
    name: str
    test_type: str
    passed: bool
    request_sent_hex: str
    actual_response_hex: str
    expected_response_hex: Optional[str] = None
    expected_nrc: Optional[str] = None
    actual_nrc: Optional[str] = None
    execution_time_ms: float
    error_message: Optional[str] = None
    frames_sniffed: List[CANFrameModel] = Field(default_factory=list)


class CitationResult(BaseModel):
    """Semantic search citation."""
    source_file: str
    section: str
    content: str
    confidence: float = 1.0


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationResult] = Field(default_factory=list)
