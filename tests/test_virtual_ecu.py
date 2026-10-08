import json
import pytest
from autodiag.api.schemas import DiagnosticDatabase
from autodiag.core.protocol.constants import NRC
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport
from autodiag.core.simulator.virtual_ecu import VirtualECU

@pytest.fixture
def sample_spec():
    with open("C:/Users/Pritam/Downloads/AutoDiag-AI/sample_specs/engine_ecu_uds_spec.json", "r") as f:
        return DiagnosticDatabase(**json.load(f))

@pytest.fixture
def test_setup(sample_spec):
    bus = VirtualCANBus()
    ecu = VirtualECU(sample_spec, bus, request_id=0x7E0, response_id=0x7E8)
    ecu.start()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    yield ecu, client
    ecu.stop()
    client.close()

def test_read_vin_positive(test_setup):
    ecu, client = test_setup
    client.send(bytes.fromhex("22F190")) # Read VIN
    resp = client.receive(timeout_sec=0.5)
    assert resp is not None
    assert resp.startswith(bytes.fromhex("62F190"))
    # Check ASCII content matches default VIN
    vin_bytes = resp[3:]
    assert vin_bytes.decode("ascii") == "WVWZZZ3CZWE123456"

def test_session_transition_and_write_did(test_setup):
    ecu, client = test_setup
    # In Default session, writing $0200 (Target Idle Speed) should fail with NRC 0x7F (ServiceNotSupportedInActiveSession)
    client.send(bytes.fromhex("2E020003E8"))
    resp = client.receive(timeout_sec=0.5)
    assert resp == bytes([0x7F, 0x2E, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION])

    # Step 1: Switch to Extended Session (10 03)
    client.send(bytes.fromhex("1003"))
    resp = client.receive(timeout_sec=0.5)
    assert resp.startswith(bytes.fromhex("5003"))

    # Step 2: In Extended session without Security Access, write DID should fail with NRC 0x33 (SecurityAccessDenied)
    client.send(bytes.fromhex("2E020003E8"))
    resp = client.receive(timeout_sec=0.5)
    assert resp == bytes([0x7F, 0x2E, NRC.SECURITY_ACCESS_DENIED])

    # Step 3: Security Access (27 01 -> Request Seed)
    client.send(bytes.fromhex("2701"))
    resp = client.receive(timeout_sec=0.5)
    assert resp.startswith(bytes.fromhex("6701"))
    seed = resp[2:]

    # Step 4: Calculate Key (seed XOR 0xAA) and Send Key (27 02)
    key = bytes([b ^ 0xAA for b in seed])
    client.send(bytes.fromhex("2702") + key)
    resp = client.receive(timeout_sec=0.5)
    assert resp.startswith(bytes.fromhex("6702"))

    # Step 5: Now Write DID in Extended Session + Unlocked State succeeds
    client.send(bytes.fromhex("2E020003E8")) # 1000 RPM (0x03E8)
    resp = client.receive(timeout_sec=0.5)
    assert resp == bytes.fromhex("6E0200")

    # Verify write took effect
    client.send(bytes.fromhex("220200"))
    resp = client.receive(timeout_sec=0.5)
    assert resp == bytes.fromhex("62020003E8")

def test_tester_present_suppress_positive_response(test_setup):
    ecu, client = test_setup
    # 3E 80 -> Suppress Positive Response
    client.send(bytes.fromhex("3E80"))
    resp = client.receive(timeout_sec=0.2)
    assert resp is None  # Suppressed!
