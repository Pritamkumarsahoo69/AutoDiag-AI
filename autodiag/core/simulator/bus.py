"""In-memory Virtual CAN Bus supporting frame broadcast and listener registration."""

import threading
import time
from typing import Callable, List
from autodiag.api.schemas import CANFrameModel


class VirtualCANBus:
    """Thread-safe virtual CAN bus connecting testers and ECUs with frame sniffing."""

    def __init__(self, max_history: int = 1000):
        self.listeners: List[Callable[[CANFrameModel], None]] = []
        self.history: List[CANFrameModel] = []
        self.max_history = max_history
        self._lock = threading.Lock()

    def add_listener(self, callback: Callable[[CANFrameModel], None]):
        """Register a callback invoked whenever a frame is transmitted."""
        with self._lock:
            self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[CANFrameModel], None]):
        """Unregister a frame callback."""
        with self._lock:
            if callback in self.listeners:
                self.listeners.remove(callback)

    def send_frame(
        self,
        can_id: int,
        data: bytes,
        direction: str = "TX",
        decoded_uds: str = "",
        status: str = "INFO"
    ) -> CANFrameModel:
        """Transmit an 8-byte CAN frame on the virtual bus."""
        padded_data = (data + bytes([0x00] * 8))[:8]
        frame = CANFrameModel(
            timestamp=time.time(),
            can_id=f"0x{can_id:03X}",
            direction=direction,
            dlc=len(padded_data),
            data_hex=padded_data.hex().upper(),
            decoded_uds=decoded_uds,
            status=status
        )

        with self._lock:
            self.history.append(frame)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            callbacks = list(self.listeners)

        for cb in callbacks:
            try:
                cb(frame)
            except Exception:
                pass

        return frame

    def clear_history(self):
        """Clear recorded sniffer frames."""
        with self._lock:
            self.history.clear()
