"""In-memory Virtual ECU Simulator with stateful ISO 14229 UDS diagnostic handlers."""

import threading
import time
from typing import Dict, Optional
from autodiag.api.schemas import DiagnosticDatabase
from autodiag.core.protocol.constants import (
    DiagnosticSession,
    NRC,
    SID,
    SecurityState,
)
from autodiag.core.protocol.frame import UDSFrameBuilder, UDSFrameParser
from autodiag.core.protocol.fsm import DiagnosticSessionFSM, SecurityAccessFSM
from autodiag.core.protocol.validator import UDSProtocolValidator
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport


class VirtualECU:
    """Stateful simulated ECU processing UDS requests over virtual ISO-TP CAN channel."""

    def __init__(
        self,
        config: DiagnosticDatabase,
        bus: VirtualCANBus,
        request_id: Optional[int] = None,
        response_id: Optional[int] = None,
    ):
        self.config = config
        self.bus = bus
        self.request_id = request_id or config.request_id_int
        self.response_id = response_id or config.response_id_int

        # Initialize State Machines
        self.session_fsm = DiagnosticSessionFSM(
            default_session=DiagnosticSession.DEFAULT,
            s3_timeout_sec=config.s3_server_timeout_ms / 1000.0
        )
        self.security_fsm = SecurityAccessFSM(
            max_attempts=3,
            delay_timer_sec=10.0,
            key_calculator=lambda s: bytes([b ^ config.security_seed_key_mask for b in s])
        )

        # Internal Data Store for DIDs (keyed by integer DID)
        self.did_store: Dict[int, bytes] = {}
        self._init_did_store()

        # Stored DTCs
        self.dtcs = ["P010001", "P020002"]
        self.dtc_setting_on = True

        # Active Routines state (keyed by integer RID)
        self.routine_states: Dict[int, str] = {}

        # Transport & Threading
        self.transport = ISOTPTransport(bus, tx_id=self.response_id, rx_id=self.request_id)
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

    def _init_did_store(self):
        """Populate initial DID memory store from specification."""
        for did in self.config.dids:
            did_int = int(did.did_hex, 16)
            if did.data_type == "ASCII":
                val = did.default_value.encode("ascii")
            elif did.data_type == "HEX" or did.data_type == "BCD":
                try:
                    val = bytes.fromhex(did.default_value)
                except ValueError:
                    val = bytes([0x00] * did.length_bytes)
            elif did.data_type == "UINT16":
                try:
                    val = bytes.fromhex(did.default_value)
                except ValueError:
                    val = bytes([0x00, 0x00])
            elif did.data_type == "UINT8":
                try:
                    val = bytes.fromhex(did.default_value)
                except ValueError:
                    val = bytes([0x00])
            else:
                val = bytes([0x00] * did.length_bytes)

            # Pad or truncate to specified length
            val = (val + bytes([0x00] * did.length_bytes))[:did.length_bytes]
            self.did_store[did_int] = val

    def start(self):
        """Start background worker listening for UDS requests."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Stop background worker."""
        self._running = False
        self.transport.close()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def _run_loop(self):
        """Continuous request receive and dispatch loop."""
        while self._running:
            # Check S3 session timeout
            self.session_fsm.check_s3_timeout()

            req_bytes = self.transport.receive(timeout_sec=0.1)
            if not req_bytes:
                continue

            response = self.process_request(req_bytes)
            if response is not None:
                self.transport.send(response)

    def process_request(self, req_bytes: bytes) -> Optional[bytes]:
        """Dispatch raw UDS request through state machines and service handlers."""
        if not req_bytes:
            return None

        try:
            msg = UDSFrameParser.parse(req_bytes)
        except Exception:
            return UDSFrameBuilder.build_negative_response(req_bytes[0], NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        sid = msg.service_id
        self.session_fsm.touch()

        # 1. Find service specification
        srv_spec = next((s for s in self.config.services if s.service_id == sid), None)
        if not srv_spec:
            return UDSFrameBuilder.build_negative_response(sid, NRC.SERVICE_NOT_SUPPORTED)

        # 2. Check Session allowance
        allowed_session, nrc_session = self.session_fsm.is_service_allowed(sid, srv_spec.allowed_sessions)
        if not allowed_session:
            return UDSFrameBuilder.build_negative_response(sid, nrc_session or NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION)

        # 3. Check Security Requirement for entire service if configured
        if srv_spec.requires_security and not self.security_fsm.is_unlocked(srv_spec.security_level):
            return UDSFrameBuilder.build_negative_response(sid, NRC.SECURITY_ACCESS_DENIED)

        # 4. Validate payload length
        valid_len, nrc_len = UDSProtocolValidator.validate_request_length(sid, msg.payload)
        if not valid_len:
            return UDSFrameBuilder.build_negative_response(sid, nrc_len or NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        # 5. Service-specific handlers
        if sid == SID.DIAGNOSTIC_SESSION_CONTROL:
            return self._handle_session_control(msg)
        elif sid == SID.ECU_RESET:
            return self._handle_ecu_reset(msg)
        elif sid == SID.SECURITY_ACCESS:
            return self._handle_security_access(msg)
        elif sid == SID.TESTER_PRESENT:
            return self._handle_tester_present(msg)
        elif sid == SID.READ_DATA_BY_IDENTIFIER:
            return self._handle_read_did(msg)
        elif sid == SID.WRITE_DATA_BY_IDENTIFIER:
            return self._handle_write_did(msg)
        elif sid == SID.ROUTINE_CONTROL:
            return self._handle_routine_control(msg)
        elif sid == SID.CLEAR_DIAGNOSTIC_INFORMATION:
            return self._handle_clear_dtc(msg)
        elif sid == SID.READ_DTC_INFORMATION:
            return self._handle_read_dtc(msg)
        elif sid == SID.CONTROL_DTC_SETTING:
            return self._handle_control_dtc_setting(msg)

        return UDSFrameBuilder.build_negative_response(sid, NRC.SERVICE_NOT_SUPPORTED)

    def _handle_session_control(self, msg) -> bytes:
        sub_fn = msg.sub_function
        suppress_pos_rsp = bool(sub_fn & 0x80)
        target_session = sub_fn & 0x7F

        success, nrc = self.session_fsm.transition_to(target_session)
        if not success:
            return UDSFrameBuilder.build_negative_response(SID.DIAGNOSTIC_SESSION_CONTROL, nrc or NRC.SUB_FUNCTION_NOT_SUPPORTED)

        # If transitioning out of security-active session, relock
        if target_session == DiagnosticSession.DEFAULT:
            self.security_fsm.reset_security()

        if suppress_pos_rsp:
            return None

        # Return P2 and P2* session timing parameters (P2 = 50ms, P2* = 5000ms)
        p2_high, p2_low = (self.config.p2_server_max_ms >> 8) & 0xFF, self.config.p2_server_max_ms & 0xFF
        p2_star_high = (self.config.p2_star_server_max_ms // 10 >> 8) & 0xFF
        p2_star_low = (self.config.p2_star_server_max_ms // 10) & 0xFF
        payload = bytes([p2_high, p2_low, p2_star_high, p2_star_low])
        return UDSFrameBuilder.build_positive_response(SID.DIAGNOSTIC_SESSION_CONTROL, payload=payload, sub_function=target_session)

    def _handle_ecu_reset(self, msg) -> bytes:
        sub_fn = msg.sub_function
        suppress_pos_rsp = bool(sub_fn & 0x80)
        reset_type = sub_fn & 0x7F

        if reset_type not in (0x01, 0x02, 0x03):
            return UDSFrameBuilder.build_negative_response(SID.ECU_RESET, NRC.SUB_FUNCTION_NOT_SUPPORTED)

        self.session_fsm.reset_to_default()
        self.security_fsm.reset_security()

        if suppress_pos_rsp:
            return None
        return UDSFrameBuilder.build_positive_response(SID.ECU_RESET, sub_function=reset_type)

    def _handle_security_access(self, msg) -> bytes:
        sub_fn = msg.sub_function
        if sub_fn is None:
            return UDSFrameBuilder.build_negative_response(SID.SECURITY_ACCESS, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        # Odd subfunction = Request Seed (0x01, 0x03)
        if sub_fn % 2 == 1:
            level = (sub_fn + 1) // 2
            seed, nrc = self.security_fsm.request_seed(level)
            if nrc is not None:
                return UDSFrameBuilder.build_negative_response(SID.SECURITY_ACCESS, nrc)
            return UDSFrameBuilder.build_positive_response(SID.SECURITY_ACCESS, payload=seed, sub_function=sub_fn)

        # Even subfunction = Send Key (0x02, 0x04)
        else:
            level = sub_fn // 2
            key = msg.payload
            if not key:
                return UDSFrameBuilder.build_negative_response(SID.SECURITY_ACCESS, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

            success, nrc = self.security_fsm.send_key(level, key)
            if not success:
                return UDSFrameBuilder.build_negative_response(SID.SECURITY_ACCESS, nrc or NRC.INVALID_KEY)
            return UDSFrameBuilder.build_positive_response(SID.SECURITY_ACCESS, sub_function=sub_fn)

    def _handle_tester_present(self, msg) -> Optional[bytes]:
        sub_fn = msg.sub_function or 0x00
        suppress_pos_rsp = bool(sub_fn & 0x80)
        self.session_fsm.touch()

        if suppress_pos_rsp:
            return None
        return UDSFrameBuilder.build_positive_response(SID.TESTER_PRESENT, sub_function=0x00)

    def _handle_read_did(self, msg) -> bytes:
        payload = msg.payload
        if len(payload) < 2 or len(payload) % 2 != 0:
            return UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        did_int = (payload[0] << 8) | payload[1]

        did_spec = next((d for d in self.config.dids if int(d.did_hex, 16) == did_int), None)
        if not did_spec:
            return UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)

        # Check session
        allowed, nrc = self.session_fsm.is_service_allowed(SID.READ_DATA_BY_IDENTIFIER, did_spec.allowed_sessions)
        if not allowed:
            return UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION)

        # Check security
        if did_spec.security_level > 0 and not self.security_fsm.is_unlocked(did_spec.security_level):
            return UDSFrameBuilder.build_negative_response(SID.READ_DATA_BY_IDENTIFIER, NRC.SECURITY_ACCESS_DENIED)

        did_bytes = self.did_store.get(did_int, bytes([0x00] * did_spec.length_bytes))
        resp_payload = bytes([payload[0], payload[1]]) + did_bytes
        return UDSFrameBuilder.build_positive_response(SID.READ_DATA_BY_IDENTIFIER, payload=resp_payload)

    def _handle_write_did(self, msg) -> bytes:
        payload = msg.payload
        if len(payload) < 3:
            return UDSFrameBuilder.build_negative_response(SID.WRITE_DATA_BY_IDENTIFIER, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        did_int = (payload[0] << 8) | payload[1]
        write_val = payload[2:]

        did_spec = next((d for d in self.config.dids if int(d.did_hex, 16) == did_int), None)
        if not did_spec or did_spec.access == "READ_ONLY":
            return UDSFrameBuilder.build_negative_response(SID.WRITE_DATA_BY_IDENTIFIER, NRC.REQUEST_OUT_OF_RANGE)

        # Check session
        allowed, nrc = self.session_fsm.is_service_allowed(SID.WRITE_DATA_BY_IDENTIFIER, did_spec.allowed_sessions)
        if not allowed:
            return UDSFrameBuilder.build_negative_response(SID.WRITE_DATA_BY_IDENTIFIER, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION)

        # Check security
        if did_spec.security_level > 0 and not self.security_fsm.is_unlocked(did_spec.security_level):
            return UDSFrameBuilder.build_negative_response(SID.WRITE_DATA_BY_IDENTIFIER, NRC.SECURITY_ACCESS_DENIED)

        # Check write length
        if len(write_val) != did_spec.length_bytes:
            return UDSFrameBuilder.build_negative_response(SID.WRITE_DATA_BY_IDENTIFIER, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        # Store write value
        self.did_store[did_int] = write_val
        return UDSFrameBuilder.build_positive_response(SID.WRITE_DATA_BY_IDENTIFIER, payload=bytes([payload[0], payload[1]]))

    def _handle_routine_control(self, msg) -> bytes:
        sub_fn = msg.sub_function
        payload = msg.payload
        if sub_fn not in (0x01, 0x02, 0x03) or len(payload) < 2:
            return UDSFrameBuilder.build_negative_response(SID.ROUTINE_CONTROL, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)

        rid_int = (payload[0] << 8) | payload[1]

        routine_spec = next((r for r in self.config.routines if int(r.routine_id, 16) == rid_int), None)
        if not routine_spec:
            return UDSFrameBuilder.build_negative_response(SID.ROUTINE_CONTROL, NRC.REQUEST_OUT_OF_RANGE)

        allowed, nrc = self.session_fsm.is_service_allowed(SID.ROUTINE_CONTROL, routine_spec.allowed_sessions)
        if not allowed:
            return UDSFrameBuilder.build_negative_response(SID.ROUTINE_CONTROL, NRC.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION)

        if routine_spec.requires_security and not self.security_fsm.is_unlocked(routine_spec.security_level):
            return UDSFrameBuilder.build_negative_response(SID.ROUTINE_CONTROL, NRC.SECURITY_ACCESS_DENIED)

        # Update state
        if sub_fn == 0x01:
            self.routine_states[rid_int] = "RUNNING"
            status_byte = 0x00  # Routine active
        elif sub_fn == 0x02:
            self.routine_states[rid_int] = "STOPPED"
            status_byte = 0x01
        else:
            status_byte = 0x02  # Completed results

        resp_payload = bytes([payload[0], payload[1], status_byte])
        return UDSFrameBuilder.build_positive_response(SID.ROUTINE_CONTROL, payload=resp_payload, sub_function=sub_fn)

        resp_payload = bytes([payload[0], payload[1], status_byte])
        return UDSFrameBuilder.build_positive_response(SID.ROUTINE_CONTROL, payload=resp_payload, sub_function=sub_fn)

    def _handle_clear_dtc(self, msg) -> bytes:
        if len(msg.payload) != 3:
            return UDSFrameBuilder.build_negative_response(SID.CLEAR_DIAGNOSTIC_INFORMATION, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
        self.dtcs.clear()
        return UDSFrameBuilder.build_positive_response(SID.CLEAR_DIAGNOSTIC_INFORMATION)

    def _handle_read_dtc(self, msg) -> bytes:
        sub_fn = msg.sub_function
        if sub_fn not in (0x01, 0x02, 0x0A):
            return UDSFrameBuilder.build_negative_response(SID.READ_DTC_INFORMATION, NRC.SUB_FUNCTION_NOT_SUPPORTED)

        # Report number of DTCs
        if sub_fn == 0x01:
            count = len(self.dtcs)
            payload = bytes([0x08, 0x00, count & 0xFF])  # Status availability mask + count
            return UDSFrameBuilder.build_positive_response(SID.READ_DTC_INFORMATION, payload=payload, sub_function=sub_fn)

        return UDSFrameBuilder.build_positive_response(SID.READ_DTC_INFORMATION, payload=bytes([0x08]), sub_function=sub_fn)

    def _handle_control_dtc_setting(self, msg) -> bytes:
        sub_fn = msg.sub_function
        if sub_fn not in (0x01, 0x02):
            return UDSFrameBuilder.build_negative_response(SID.CONTROL_DTC_SETTING, NRC.SUB_FUNCTION_NOT_SUPPORTED)

        self.dtc_setting_on = (sub_fn == 0x01)
        return UDSFrameBuilder.build_positive_response(SID.CONTROL_DTC_SETTING, sub_function=sub_fn)
