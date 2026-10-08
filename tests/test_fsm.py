import pytest
import time
from autodiag.core.protocol.constants import DiagnosticSession, NRC, SecurityState
from autodiag.core.protocol.fsm import DiagnosticSessionFSM, SecurityAccessFSM

def test_session_fsm_transitions():
    fsm = DiagnosticSessionFSM()
    assert fsm.current_session == DiagnosticSession.DEFAULT

    # Transition to Extended
    success, nrc = fsm.transition_to(DiagnosticSession.EXTENDED)
    assert success
    assert nrc is None
    assert fsm.current_session == DiagnosticSession.EXTENDED

    # Transition to Programming from Extended is valid
    success, nrc = fsm.transition_to(DiagnosticSession.PROGRAMMING)
    assert success
    assert fsm.current_session == DiagnosticSession.PROGRAMMING

    # Reset to default
    fsm.reset_to_default()
    assert fsm.current_session == DiagnosticSession.DEFAULT

def test_session_fsm_service_permission():
    fsm = DiagnosticSessionFSM()
    # Default session: allowed in DEFAULT and EXTENDED
    allowed, nrc = fsm.is_service_allowed(0x22, allowed_sessions=["DEFAULT", "EXTENDED"])
    assert allowed
    assert nrc is None

    # Not allowed in DEFAULT
    allowed, nrc = fsm.is_service_allowed(0x2E, allowed_sessions=["EXTENDED", "PROGRAMMING"])
    assert not allowed
    assert nrc == NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION

def test_security_fsm_seed_key_flow():
    sec_fsm = SecurityAccessFSM(
        seed_generator=lambda: bytes.fromhex("11223344"),
        key_calculator=lambda s: bytes([b ^ 0xAA for b in s])
    )
    assert sec_fsm.state == SecurityState.LOCKED

    # Step 1: Request Seed
    seed, nrc = sec_fsm.request_seed(level=1)
    assert seed == bytes.fromhex("11223344")
    assert nrc is None
    assert sec_fsm.state == SecurityState.SEED_REQUESTED

    # Step 2: Send valid key
    valid_key = bytes([b ^ 0xAA for b in seed])
    success, nrc = sec_fsm.send_key(level=1, key=valid_key)
    assert success
    assert nrc is None
    assert sec_fsm.is_unlocked(level=1)
    assert sec_fsm.state == SecurityState.UNLOCKED_L1

def test_security_fsm_invalid_key_and_attempts():
    sec_fsm = SecurityAccessFSM(
        max_attempts=2,
        seed_generator=lambda: bytes.fromhex("AABBCCDD"),
        key_calculator=lambda s: bytes([b ^ 0xAA for b in s])
    )
    # Attempt 1
    seed, _ = sec_fsm.request_seed(1)
    success, nrc = sec_fsm.send_key(1, bytes.fromhex("00000000"))
    assert not success
    assert nrc == NRC.INVALID_KEY
    assert sec_fsm.failed_attempts == 1

    # Attempt 2 -> Lockout
    seed, _ = sec_fsm.request_seed(1)
    success, nrc = sec_fsm.send_key(1, bytes.fromhex("00000000"))
    assert not success
    assert nrc == NRC.EXCEED_NUMBER_OF_ATTEMPTS
    assert sec_fsm.state == SecurityState.DELAY_LOCKED
