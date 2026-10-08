import pytest
from autodiag.core.generator.capl_exporter import CAPLTestExporter
from autodiag.core.generator.matrix import TestMatrixGenerator
from autodiag.core.generator.python_exporter import PythonTestExporter
from autodiag.core.rag.parser import SpecParser

@pytest.fixture
def sample_spec():
    return SpecParser.parse_file("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json")

def test_generate_test_matrix_diversity(sample_spec):
    suite = TestMatrixGenerator.generate_suite(sample_spec)

    types = {t.test_type for t in suite}
    assert "POSITIVE" in types
    assert "NEGATIVE_NRC" in types
    assert len(suite) >= 10

    # Verify at least one test covers each key service
    services_tested = {t.service_id for t in suite}
    assert 0x10 in services_tested  # Session Control
    assert 0x22 in services_tested  # Read DID
    assert 0x27 in services_tested  # Security Access
    assert 0x2E in services_tested  # Write DID
    assert 0x31 in services_tested  # Routine Control

def test_export_python_script(sample_spec):
    suite = TestMatrixGenerator.generate_suite(sample_spec)
    py_code = PythonTestExporter.export(suite, sample_spec)

    assert "import pytest" in py_code
    assert "ISOTPTransport" in py_code
    assert "def test_" in py_code
    assert "assert resp" in py_code

def test_export_capl_script(sample_spec):
    suite = TestMatrixGenerator.generate_suite(sample_spec)
    capl_code = CAPLTestExporter.export(suite, sample_spec)

    assert "Vector CANoe CAPL Automated Diagnostic Test Suite" in capl_code
    assert "variables" in capl_code
    assert "testcase" in capl_code
    assert "testStep" in capl_code or "diagSendRequest" in capl_code
