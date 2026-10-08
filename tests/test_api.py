import pytest
from fastapi.testclient import TestClient
from autodiag.api.server import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_upload_spec_and_query(client):
    with open("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json", "rb") as f:
        resp = client.post(
            "/api/v1/specs/upload",
            files={"file": ("engine_ecu_uds_spec.json", f, "application/json")}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ecu_name"] == "Engine_Control_Unit"

    # Query
    q_resp = client.post("/api/v1/query", json={"query": "VIN", "top_k": 3})
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert len(q_data["citations"]) > 0

def test_api_generate_and_execute(client):
    with open("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json", "rb") as f:
        client.post(
            "/api/v1/specs/upload",
            files={"file": ("engine_ecu_uds_spec.json", f, "application/json")}
        )

    # Generate
    gen_resp = client.post("/api/v1/tests/generate")
    assert gen_resp.status_code == 200
    test_cases = gen_resp.json()["test_cases"]
    assert len(test_cases) >= 10

    # Execute
    exec_resp = client.post("/api/v1/tests/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["summary"]["total"] == len(test_cases)
    assert exec_data["summary"]["passed"] > 0

def test_api_export_scripts(client):
    with open("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json", "rb") as f:
        client.post(
            "/api/v1/specs/upload",
            files={"file": ("engine_ecu_uds_spec.json", f, "application/json")}
        )
    client.post("/api/v1/tests/generate")

    # Export Python
    py_resp = client.get("/api/v1/export/python")
    assert py_resp.status_code == 200
    assert "import pytest" in py_resp.text

    # Export CAPL
    capl_resp = client.get("/api/v1/export/capl")
    assert capl_resp.status_code == 200
    assert "Vector CANoe CAPL" in capl_resp.text

def test_api_benchmark_data(client):
    resp = client.get("/api/v1/benchmark/data")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "ecus" in data
    assert data["summary"]["total_ecus"] == 10
    assert data["summary"]["total_autodiag_tests"] >= 140
