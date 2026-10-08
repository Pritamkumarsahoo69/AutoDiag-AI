"""Deterministic Finite State Machines for Diagnostic Sessions and Security Access."""

import os
import time
from typing import Callable, List, Optional, Tuple
from autodiag.core.protocol.constants import DiagnosticSession, NRC, SecurityState


class DiagnosticSessionFSM:
    """Manages active diagnostic session state transitions and S3 keep-alive timer."""

    def __init__(self, default_session: int = DiagnosticSession.DEFAULT, s3_timeout_sec: float = 5.0):
        self.default_session = default_session
        self.current_session = default_session
        self.s3_timeout_sec = s3_timeout_sec
        self.last_activity_time = time.time()

    def touch(self):
        """Update last activity timestamp (TesterPresent or valid request)."""
        self.last_activity_time = time.time()

    def check_s3_timeout(self) -> bool:
        """Check if S3 timeout expired and revert to default session if needed."""
        if self.current_session != self.default_session:
            if (time.time() - self.last_activity_time) > self.s3_timeout_sec:
                self.reset_to_default()
                return True
        return False

    def reset_to_default(self):
        """Revert back to default session."""
        self.current_session = self.default_session
        self.touch()

    def transition_to(self, new_session: int) -> Tuple[bool, Optional[int]]:
        """Attempt to transition to a new session."""
        valid_sessions = [
            DiagnosticSession.DEFAULT,
            DiagnosticSession.PROGRAMMING,
            DiagnosticSession.EXTENDED,
            DiagnosticSession.SAFETY_SYSTEM,
        ]
        if new_session not in valid_sessions:
            return False, NRC.SUB_FUNCTION_NOT_SUPPORTED

        self.current_session = new_session
        self.touch()
        return True, None

    def is_service_allowed(self, service_id: int, allowed_sessions: List[str]) -> Tuple[bool, Optional[int]]:
        """Check if a service or DID is allowed in the current session."""
        session_names = {
            DiagnosticSession.DEFAULT: "DEFAULT",
            DiagnosticSession.PROGRAMMING: "PROGRAMMING",
            DiagnosticSession.EXTENDED: "EXTENDED",
            DiagnosticSession.SAFETY_SYSTEM: "SAFETY_SYSTEM",
        }
        current_name = session_names.get(self.current_session, "DEFAULT")
        if current_name in allowed_sessions or "ALL" in allowed_sessions:
            return True, None
        return False, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION


class SecurityAccessFSM:
    """Manages Seed-Key security authentication, attempt limits, and delay lockout."""

    def __init__(
        self,
        max_attempts: int = 3,
        delay_timer_sec: float = 10.0,
        seed_generator: Optional[Callable[[], bytes]] = None,
        key_calculator: Optional[Callable[[bytes], bytes]] = None,
    ):
        self.state = SecurityState.LOCKED
        self.max_attempts = max_attempts
        self.delay_timer_sec = delay_timer_sec
        self.failed_attempts = 0
        self.lockout_timestamp = 0.0
        self.active_seed: Optional[bytes] = None
        self.active_level: int = 0
        self.seed_generator = seed_generator or self._default_seed_gen
        self.key_calculator = key_calculator or self._default_key_calc

    @staticmethod
    def _default_seed_gen() -> bytes:
        return os.urandom(4)

    @staticmethod
    def _default_key_calc(seed: bytes) -> bytes:
        # Default mock algorithm: XOR with 0xAA
        return bytes([b ^ 0xAA for b in seed])

    def request_seed(self, level: int) -> Tuple[Optional[bytes], Optional[int]]:
        """Generate and return seed for requested security level."""
        # Check if in delay lockout
        if self.state == SecurityState.DELAY_LOCKED:
            if (time.time() - self.lockout_timestamp) < self.delay_timer_sec:
                return None, NRC.REQUIRED_TIME_DELAY_NOT_EXPIRED
            else:
                # Lockout expired, reset to locked
                self.state = SecurityState.LOCKED
                self.failed_attempts = 0

        # If already unlocked at this level, return 00 00 00 00
        if self.is_unlocked(level):
            return bytes([0x00] * 4), None

        self.active_seed = self.seed_generator()
        self.active_level = level
        self.state = SecurityState.SEED_REQUESTED
        return self.active_seed, None

    def send_key(self, level: int, key: bytes) -> Tuple[bool, Optional[int]]:
        """Validate received key against active seed."""
        if self.state == SecurityState.DELAY_LOCKED:
            if (time.time() - self.lockout_timestamp) < self.delay_timer_sec:
                return False, NRC.REQUIRED_TIME_DELAY_NOT_EXPIRED
            else:
                self.state = SecurityState.LOCKED
                self.failed_attempts = 0

        if self.state != SecurityState.SEED_REQUESTED or self.active_seed is None or self.active_level != level:
            return False, NRC.REQUEST_SEQUENCE_ERROR

        expected_key = self.key_calculator(self.active_seed)
        if key == expected_key:
            self.failed_attempts = 0
            self.active_seed = None
            if level == 1:
                self.state = SecurityState.UNLOCKED_L1
            elif level == 2:
                self.state = SecurityState.UNLOCKED_L2
            else:
                self.state = SecurityState.UNLOCKED_L1
            return True, None
        else:
            self.failed_attempts += 1
            self.active_seed = None
            if self.failed_attempts >= self.max_attempts:
                self.state = SecurityState.DELAY_LOCKED
                self.lockout_timestamp = time.time()
                return False, NRC.EXCEED_NUMBER_OF_ATTEMPTS
            else:
                self.state = SecurityState.LOCKED
                return False, NRC.INVALID_KEY

    def is_unlocked(self, level: int = 1) -> bool:
        """Check if ECU is unlocked at or above required level."""
        if level == 0:
            return True
        if level == 1 and self.state in (SecurityState.UNLOCKED_L1, SecurityState.UNLOCKED_L2):
            return True
        if level == 2 and self.state == SecurityState.UNLOCKED_L2:
            return True
        return False

    def reset_security(self):
        """Lock the ECU."""
        self.state = SecurityState.LOCKED
        self.active_seed = None
        self.active_level = 0
