"""Pydantic Test Intermediate Representation (TestIR) schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestPreconditionsIR(BaseModel):
    session: str = Field(default="DEFAULT", description="DEFAULT, EXTENDED, PROGRAMMING, SAFETY_SYSTEM")
    security_level: int = Field(default=0, description="0 = Unlocked, 1 = Level 1, etc.")
    ecu_state: str = Field(default="ANY", description="IDLE, ENGINE_STOPPED, ENGINE_RUNNING, etc.")


class TestStepIR(BaseModel):
    service: str = Field(..., description="Service name, e.g. 'ReadDataByIdentifier', 'DiagnosticSessionControl'")
    sub_function: Optional[int] = Field(None, description="Sub-function byte or None")
    did_or_rid: Optional[str] = Field(None, description="DID or RID hex, e.g. '0xF190'")
    data: Optional[str] = Field(None, description="Write data payload hex string or None")
    timing_ms: int = Field(default=50, description="Expected response timeout in ms")


class TestExpectedIR(BaseModel):
    positive_response_bytes: Optional[str] = Field(None, description="Expected response hex string, e.g. '62F190...'")
    nrc: Optional[str] = Field(None, description="Expected NRC in hex string, e.g. '0x31', '0x7E'")


class TestIR(BaseModel):
    """Structured Intermediate Representation (IR) for UDS Diagnostic Test Cases."""
    requirement_id: str = Field(..., description="Unique Requirement ID, e.g. 'REQ_UDS_001'")
    preconditions: TestPreconditionsIR = Field(default_factory=TestPreconditionsIR)
    steps: List[TestStepIR] = Field(default_factory=list)
    expected: TestExpectedIR = Field(default_factory=TestExpectedIR)
    pass_fail_criteria: str = Field(default="ECU returns expected response or NRC")
    source_citations: List[str] = Field(default_factory=list, description="Spec chunk IDs or section titles cited")
