import pytest
import time
from autodiag.core.protocol.fsm import DiagnosticSessionFSM, SecurityAccessFSM
from autodiag.core.protocol.constants import DiagnosticSession, NRC, SecurityState
from autodiag.core.simulator.isotp import ISOTPTransport
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.rag.parser import SpecParser
from autodiag.core.simulator.virtual_ecu import VirtualECU
import json
from autodiag.api.schemas import DiagnosticDatabase

def test_s3_timeout():
    fsm = DiagnosticSessionFSM(s3_timeout_sec=0.1)
    fsm.transition_to(DiagnosticSession.EXTENDED)
    assert fsm.current_session == DiagnosticSession.EXTENDED

    # Wait for S3 to expire
    time.sleep(0.2)
    fsm.check_s3_timeout()

    assert fsm.current_session == DiagnosticSession.DEFAULT

def test_security_delay_timer_0x37():
    sec_fsm = SecurityAccessFSM(
        max_attempts=1,
        delay_timer_sec=0.2,
        seed_generator=lambda: bytes.fromhex("11223344"),
        key_calculator=lambda s: bytes.fromhex("99999999")
    )

    # Attempt 1 -> Lockout
    sec_fsm.request_seed(1)
    success, nrc = sec_fsm.send_key(1, bytes.fromhex("00000000"))
    assert not success
    assert nrc == NRC.EXCEED_NUMBER_OF_ATTEMPTS

    # Immediately request seed -> should fail with 0x37
    seed, nrc = sec_fsm.request_seed(1)
    assert seed is None
    assert nrc == NRC.REQUIRED_TIME_DELAY_NOT_EXPIRED

    # Wait for delay timer
    time.sleep(0.3)
    seed, nrc = sec_fsm.request_seed(1)
    assert seed is not None
    assert nrc is None

def test_nrc_precedence(tmp_path):
    # NRC Precedence rule check:
    # 1. 0x11 ServiceNotSupported
    # 2. 0x7F ServiceNotSupportedInActiveSession
    # 3. 0x13 IncorrectMessageLength
    db = DiagnosticDatabase(ecu_name="Test")

    # Need to simulate the ECU processing a request
    bus = VirtualCANBus()
    ecu = VirtualECU(db, bus)

    # 0x99 is not supported at all. Should return 0x11, not 0x13 for length
    resp = ecu.process_request(bytes.fromhex("99"))
    assert resp == bytes([0x7F, 0x99, NRC.SERVICE_NOT_SUPPORTED])

def test_isotp_flow_control_timeouts():
    bus = VirtualCANBus()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)

    # Send First Frame but never receive CFs.
    # Or expect a timeout when receiving
    resp = client.receive(timeout_sec=0.1)
    assert resp is None

def test_malformed_spec_table(tmp_path):
    bad_spec = tmp_path / "bad.txt"
    bad_spec.write_text("Just some random text with Service 0x22 and DID 0xF190 but no valid formatting")

    # Should not crash, should extract what it can or use defaults
    db = SpecParser.parse_raw_text(bad_spec.read_text(), "bad.txt")
    assert db.ecu_name == "bad"
    assert len(db.services) > 0
