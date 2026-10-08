import pytest
from autodiag.core.llm.schema import TestIR, TestStepIR, TestPreconditionsIR, TestExpectedIR
from autodiag.core.llm.client import MockLLM, OpenAICompatibleLLM
from autodiag.core.llm.pipeline import RequirementToTestIRPipeline
from autodiag.core.rag.knowledge_base import DiagnosticKnowledgeBase
from autodiag.core.rag.parser import SpecParser

def test_test_ir_pydantic_schema():
    ir = TestIR(
        requirement_id="REQ_UDS_001",
        preconditions=TestPreconditionsIR(session="EXTENDED", security_level=1, ecu_state="ENGINE_STOPPED"),
        steps=[
            TestStepIR(service="ReadDataByIdentifier", sub_function=None, did_or_rid="0xF190", data=None, timing_ms=50)
        ],
        expected=TestExpectedIR(positive_response_bytes="62F190575657", nrc=None),
        pass_fail_criteria="ECU responds with 0x62 F190 VIN data",
        source_citations=["chunk_001"]
    )
    assert ir.requirement_id == "REQ_UDS_001"
    assert ir.steps[0].did_or_rid == "0xF190"
    assert ir.expected.positive_response_bytes == "62F190575657"

def test_mock_llm_client():
    mock_json = """{
        "requirement_id": "REQ_001",
        "preconditions": {"session": "DEFAULT", "security_level": 0, "ecu_state": "ANY"},
        "steps": [{"service": "ReadDataByIdentifier", "sub_function": null, "did_or_rid": "0xF190", "data": null, "timing_ms": 50}],
        "expected": {"positive_response_bytes": "62F190", "nrc": null},
        "pass_fail_criteria": "Pass if 0x62 response",
        "source_citations": ["chunk_1"]
    }"""
    client = MockLLM(default_response=mock_json)
    resp = client.generate(prompt="Generate test for VIN", system_prompt="JSON only")
    assert "REQ_001" in resp

def test_requirement_to_test_ir_pipeline():
    mock_json = """{
        "requirement_id": "REQ_UDS_VIN",
        "preconditions": {"session": "DEFAULT", "security_level": 0, "ecu_state": "IDLE"},
        "steps": [{"service": "ReadDataByIdentifier", "sub_function": null, "did_or_rid": "0xF190", "data": null, "timing_ms": 50}],
        "expected": {"positive_response_bytes": "62F190575657", "nrc": null},
        "pass_fail_criteria": "ECU responds with VIN",
        "source_citations": ["chunk_vin"]
    }"""
    client = MockLLM(default_response=mock_json)

    spec = SpecParser.parse_file("sample_specs/01_engine_ecu_pcm.json")
    kb = DiagnosticKnowledgeBase()
    kb.load_database(spec)

    pipeline = RequirementToTestIRPipeline(llm_client=client, knowledge_base=kb)
    test_ir = pipeline.process_requirement("Read VIN in Default Session")

    assert test_ir.requirement_id == "REQ_UDS_VIN"
    assert test_ir.steps[0].service == "ReadDataByIdentifier"
