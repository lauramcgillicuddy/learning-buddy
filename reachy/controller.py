"""Reachy Mini controller using the official reachy-mini SDK."""

import time
import threading
import numpy as np
from contextlib import contextmanager

import config

_reachy = None
_connected = False


def connect() -> bool:
    global _reachy, _connected
    try:
        from reachy_mini import ReachyMini
        _reachy = ReachyMini(host=config.REACHY_HOST)
        _connected = True
        print(f"[Reachy] Connected to {config.REACHY_HOST}")
        threading.Thread(target=startup_sequence, daemon=True).start()
        return True
    except Exception as e:
        print(f"[Reachy] Could not connect to {config.REACHY_HOST}: {e}")
        print("[Reachy] Running without robot — voice and UI still work.")
        _connected = False
        return False


def is_connected() -> bool:
    return _connected


def _safe(fn):
    if _connected and _reachy:
        try:
            fn()
        except Exception as e:
            print(f"[Reachy] Motion error: {e}")


# ── Movements ─────────────────────────────────────────────────────────────────

def startup_sequence() -> None:
    """Head lift + antenna wiggle + nod — signals the app is ready."""
    def _do():
        from reachy_mini.utils import create_head_pose
        time.sleep(0.5)
        # Gentle head raise
        _reachy.goto_target(head=create_head_pose(pitch=-5, degrees=True), duration=0.4)
        time.sleep(0.5)
        _reachy.goto_target(head=create_head_pose(pitch=0, degrees=True), duration=0.3)
        # Happy antenna wiggle
        for _ in range(3):
            _reachy.goto_target(antennas=np.deg2rad([30, -30]), duration=0.15)
            _reachy.goto_target(antennas=np.deg2rad([-30, 30]), duration=0.15)
        _reachy.goto_target(antennas=np.deg2rad([0, 0]), duration=0.2)
        time.sleep(0.2)
        # Single nod
        _reachy.goto_target(head=create_head_pose(pitch=8, degrees=True), duration=0.25)
        _reachy.goto_target(head=create_head_pose(pitch=0, degrees=True), duration=0.25)
    _safe(_do)


def thinking() -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        _reachy.goto_target(head=create_head_pose(roll=-5, degrees=True), duration=0.3)
    _safe(_do)


def speaking() -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        _reachy.goto_target(head=create_head_pose(pitch=0, roll=0, degrees=True), duration=0.3)
    _safe(_do)


def nod(count: int = 2) -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        for _ in range(count):
            _reachy.goto_target(head=create_head_pose(pitch=10, degrees=True), duration=0.25)
            _reachy.goto_target(head=create_head_pose(pitch=0, degrees=True), duration=0.2)
    _safe(_do)


def shake() -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        for _ in range(2):
            _reachy.goto_target(head=create_head_pose(roll=8, degrees=True), duration=0.2)
            _reachy.goto_target(head=create_head_pose(roll=-8, degrees=True), duration=0.2)
        _reachy.goto_target(head=create_head_pose(roll=0, degrees=True), duration=0.2)
    _safe(_do)


def listening_pose() -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        _reachy.goto_target(head=create_head_pose(pitch=5, degrees=True), duration=0.3)
    _safe(_do)


def antenna_happy() -> None:
    def _do():
        for _ in range(3):
            _reachy.goto_target(antennas=np.deg2rad([30, -30]), duration=0.15)
            _reachy.goto_target(antennas=np.deg2rad([-30, 30]), duration=0.15)
        _reachy.goto_target(antennas=np.deg2rad([0, 0]), duration=0.2)
    _safe(_do)


def antenna_droop() -> None:
    def _do():
        _reachy.goto_target(antennas=np.deg2rad([-45, -45]), duration=0.4)
        time.sleep(1.0)
        _reachy.goto_target(antennas=np.deg2rad([0, 0]), duration=0.4)
    _safe(_do)


def antenna_thinking() -> None:
    def _do():
        for _ in range(2):
            _reachy.goto_target(antennas=np.deg2rad([15, 15]), duration=0.4)
            _reachy.goto_target(antennas=np.deg2rad([-15, -15]), duration=0.4)
        _reachy.goto_target(antennas=np.deg2rad([0, 0]), duration=0.3)
    _safe(_do)


def idle() -> None:
    def _do():
        from reachy_mini.utils import create_head_pose
        _reachy.goto_target(head=create_head_pose(pitch=-3, degrees=True), duration=2.0)
        _reachy.goto_target(head=create_head_pose(pitch=0, degrees=True), duration=2.0)
    _safe(_do)


@contextmanager
def thinking_context():
    thinking()
    try:
        yield
    finally:
        speaking()
