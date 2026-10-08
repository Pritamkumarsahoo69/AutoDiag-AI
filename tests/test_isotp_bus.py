import pytest
import time
from autodiag.core.simulator.bus import VirtualCANBus
from autodiag.core.simulator.isotp import ISOTPTransport

def test_virtual_can_bus_broadcast_and_sniff():
    bus = VirtualCANBus()
    received_frames = []

    def on_frame(frame):
        received_frames.append(frame)

    bus.add_listener(on_frame)
    bus.send_frame(can_id=0x7E0, data=bytes.fromhex("0210010000000000"), direction="TX")

    assert len(received_frames) == 1
    assert received_frames[0].can_id == "0x7E0"
    assert received_frames[0].dlc == 8
    assert received_frames[0].data_hex == "0210010000000000"

def test_isotp_single_frame_transmission():
    bus = VirtualCANBus()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    server = ISOTPTransport(bus, tx_id=0x7E8, rx_id=0x7E0)

    payload = bytes.fromhex("22F190")
    client.send(payload)

    received = server.receive(timeout_sec=0.5)
    assert received == payload

def test_isotp_multi_frame_transmission():
    bus = VirtualCANBus()
    client = ISOTPTransport(bus, tx_id=0x7E0, rx_id=0x7E8)
    server = ISOTPTransport(bus, tx_id=0x7E8, rx_id=0x7E0)

    # 30-byte payload requiring FF, FC, and multiple CFs
    large_payload = bytes.fromhex("62F1905756575A5A5A33435A57453132333435363031303230333034")
    assert len(large_payload) > 7

    server.send(large_payload)
    received = client.receive(timeout_sec=1.0)
    assert received == large_payload
