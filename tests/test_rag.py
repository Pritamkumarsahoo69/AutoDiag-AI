import pytest
from autodiag.core.rag.knowledge_base import DiagnosticKnowledgeBase
from autodiag.core.rag.parser import SpecParser

def test_parse_json_spec():
    db = SpecParser.parse_file("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json")
    assert db.ecu_name == "Engine_Control_Unit"
    assert any(d.did_int == 0xF190 for d in db.dids)
    assert any(s.service_id == 0x22 for s in db.services)

def test_query_knowledge_base():
    db = SpecParser.parse_file("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json")
    kb = DiagnosticKnowledgeBase()
    kb.load_database(db)

    results = kb.search("Vehicle Identification Number VIN")
    assert len(results) > 0
    assert any("F190" in r.content.upper() for r in results)
    assert results[0].source_file.endswith("engine_ecu_uds_spec.json") or results[0].section != ""

def test_rag_semantic_qa_answer():
    db = SpecParser.parse_file("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json")
    kb = DiagnosticKnowledgeBase()
    kb.load_database(db)

    answer_obj = kb.answer_query("What services are allowed in Programming session?")
    assert answer_obj.answer != ""
    assert len(answer_obj.citations) > 0
