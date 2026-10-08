"""ISO 15765-2 (DoCAN / ISO-TP) Transport Layer implementation for CAN."""

import queue
import threading
import time
from typing import Optional
from autodiag.api.schemas import CANFrameModel
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.protocol.constants import get_nrc_description, get_service_name


# ISO-TP PCI Frame Types (High nibble of byte 0)
PCI_SINGLE_FRAME = 0x00
PCI_FIRST_FRAME = 0x10
PCI_CONSECUTIVE_FRAME = 0x20
PCI_FLOW_CONTROL = 0x30


class ISOTPTransport:
    """ISO 15765-2 Multi-Frame Protocol Adapter over VirtualCANBus."""

    def __init__(self, bus: VirtualCANBus, tx_id: int, rx_id: int):
        self.bus = bus
        self.tx_id = tx_id
        self.rx_id = rx_id
        self.rx_queue: queue.Queue[bytes] = queue.Queue()
        self._rx_buffer = bytearray()
        self._rx_expected_length = 0
        self._rx_sn = 1
        self._stop_event = threading.Event()

        self._frame_listener = self._on_can_frame
        self.bus.add_listener(self._frame_listener)

    def close(self):
        """Detach from bus."""
        self.bus.remove_listener(self._frame_listener)
        self._stop_event.set()

    def _decode_uds_summary(self, payload: bytes) -> tuple[str, str]:
        """Generate human-readable annotation for frame sniffer."""
        if not payload:
            return "", "INFO"
        sid = payload[0]
        if sid == 0x7F and len(payload) >= 3:
            req_sid = payload[1]
            nrc = payload[2]
            return f"NegativeResponse: {get_service_name(req_sid)} -> NRC 0x{nrc:02X} ({get_nrc_description(nrc)})", "NRC"
        elif sid > 0x40:
            orig_sid = sid - 0x40
            return f"PositiveResponse: {get_service_name(orig_sid)}", "OK"
        else:
            return f"Request: {get_service_name(sid)}", "INFO"

    def send(self, payload: bytes):
        """Send payload using ISO-TP Single-Frame or Multi-Frame segmentation."""
        length = len(payload)
        summary, status = self._decode_uds_summary(payload)

        # Single Frame (SF): length <= 7 bytes
        if length <= 7:
            sf_pci = (PCI_SINGLE_FRAME | length) & 0xFF
            frame_data = bytes([sf_pci]) + payload
            self.bus.send_frame(self.tx_id, frame_data, direction="TX", decoded_uds=summary, status=status)
            return

        # Multi-Frame: First Frame (FF)
        ff_pci_high = (PCI_FIRST_FRAME | ((length >> 8) & 0x0F)) & 0xFF
        ff_pci_low = length & 0xFF
        first_chunk = payload[:6]
        ff_data = bytes([ff_pci_high, ff_pci_low]) + first_chunk
        self.bus.send_frame(self.tx_id, ff_data, direction="TX", decoded_uds=f"{summary} [FF, Total {length}B]", status=status)

        # Transmit Consecutive Frames (CF)
        offset = 6
        sn = 1
        while offset < length:
            chunk = payload[offset:offset + 7]
            cf_pci = (PCI_CONSECUTIVE_FRAME | (sn & 0x0F)) & 0xFF
            cf_data = bytes([cf_pci]) + chunk
            self.bus.send_frame(self.tx_id, cf_data, direction="TX", decoded_uds=f"CF [SN {sn}]", status="INFO")
            offset += len(chunk)
            sn = (sn + 1) % 16

    def _on_can_frame(self, frame: CANFrameModel):
        """Handle incoming frame on virtual bus."""
        frame_can_id = int(frame.can_id, 16)
        if frame_can_id != self.rx_id:
            return

        data = bytes.fromhex(frame.data_hex)
        if not data:
            return

        pci_type = data[0] & 0xF0

        if pci_type == PCI_SINGLE_FRAME:
            sf_length = data[0] & 0x0F
            if 0 < sf_length <= 7:
                payload = data[1:1 + sf_length]
                self.rx_queue.put(payload)

        elif pci_type == PCI_FIRST_FRAME:
            self._rx_expected_length = ((data[0] & 0x0F) << 8) | data[1]
            self._rx_buffer = bytearray(data[2:8])
            self._rx_sn = 1
            # Send Flow Control CTS
            fc_frame = bytes([PCI_FLOW_CONTROL | 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.bus.send_frame(self.tx_id, fc_frame, direction="TX", decoded_uds="FlowControl [CTS]", status="INFO")

        elif pci_type == PCI_CONSECUTIVE_FRAME:
            sn = data[0] & 0x0F
            chunk = data[1:8]
            self._rx_buffer.extend(chunk)
            self._rx_sn = (self._rx_sn + 1) % 16

            if len(self._rx_buffer) >= self._rx_expected_length:
                final_payload = bytes(self._rx_buffer[:self._rx_expected_length])
                self.rx_queue.put(final_payload)
                self._rx_buffer = bytearray()
                self._rx_expected_length = 0

    def receive(self, timeout_sec: float = 1.0) -> Optional[bytes]:
        """Block and wait for completed UDS message."""
        try:
            return self.rx_queue.get(timeout=timeout_sec)
        except queue.Empty:
            return None
