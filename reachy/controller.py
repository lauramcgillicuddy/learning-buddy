"""Reachy Mini controller — expressions and head movements over WiFi."""

import time
import threading
from contextlib import contextmanager

import config

_reachy = None
_connected = False


def connect() -> bool:
    global _reachy, _connected
    try:
        from reachy_sdk import ReachySDK
        _reachy = ReachySDK(host=config.REACHY_HOST)
        _connected = True
        print(f"[Reachy] Connected to {config.REACHY_HOST}")
        # Run startup sequence in background so it doesn't block the UI
        threading.Thread(target=startup_sequence, daemon=True).start()
        return True
    except Exception as e:
        print(f"[Reachy] Could not connect to {config.REACHY_HOST}: {e}")
        print("[Reachy] Running without robot — voice and UI still work.")
        _connected = False
        return False


def startup_sequence() -> None:
    """Play on startup to signal Reachy is awake and ready."""
    def _do():
        time.sleep(0.5)  # small pause to let the SDK settle
        # Gentle head raise
        _reachy.head.neck_pitch.goal_position = -5
        time.sleep(0.4)
        _reachy.head.neck_pitch.goal_position = 0
        time.sleep(0.3)
        # Happy antenna wiggle
        for _ in range(3):
            _reachy.joints["l_antenna"].goal_position = 30
            _reachy.joints["r_antenna"].goal_position = -30
            time.sleep(0.15)
            _reachy.joints["l_antenna"].goal_position = -30
            _reachy.joints["r_antenna"].goal_position = 30
            time.sleep(0.15)
        # Return to neutral
        _reachy.joints["l_antenna"].goal_position = 0
        _reachy.joints["r_antenna"].goal_position = 0
        time.sleep(0.3)
        # Single nod: "ready!"
        _reachy.head.neck_pitch.goal_position = 8
        time.sleep(0.25)
        _reachy.head.neck_pitch.goal_position = 0
    _safe(_do)


def is_connected() -> bool:
    return _connected


def _safe(fn):
    """Run a robot command only if connected, silently skip otherwise."""
    if _connected and _reachy:
        try:
            fn()
        except Exception:
            pass


def thinking() -> None:
    """Slight head tilt while Claude is processing."""
    def _do():
        _reachy.head.neck_roll.goal_position = -5
        time.sleep(0.3)
    _safe(_do)


def speaking() -> None:
    """Return head to neutral when speaking."""
    def _do():
        _reachy.head.neck_roll.goal_position = 0
        _reachy.head.neck_pitch.goal_position = 0
    _safe(_do)


def nod(count: int = 2) -> None:
    """Nod head for correct answer."""
    def _do():
        for _ in range(count):
            _reachy.head.neck_pitch.goal_position = 10
            time.sleep(0.25)
            _reachy.head.neck_pitch.goal_position = 0
            time.sleep(0.2)
    _safe(_do)


def shake() -> None:
    """Shake head for wrong answer."""
    def _do():
        for _ in range(2):
            _reachy.head.neck_roll.goal_position = 8
            time.sleep(0.2)
            _reachy.head.neck_roll.goal_position = -8
            time.sleep(0.2)
        _reachy.head.neck_roll.goal_position = 0
    _safe(_do)


def idle() -> None:
    """Gentle idle drift to show the robot is alive."""
    def _do():
        _reachy.head.neck_pitch.goal_position = -3
        time.sleep(2)
        _reachy.head.neck_pitch.goal_position = 0
    _safe(_do)


def listening_pose() -> None:
    """Lean slightly forward when listening."""
    def _do():
        _reachy.head.neck_pitch.goal_position = 5
    _safe(_do)


def antenna_happy() -> None:
    """Wiggle antennas for excitement / correct answer."""
    def _do():
        for _ in range(3):
            _reachy.joints["l_antenna"].goal_position = 30
            _reachy.joints["r_antenna"].goal_position = -30
            time.sleep(0.15)
            _reachy.joints["l_antenna"].goal_position = -30
            _reachy.joints["r_antenna"].goal_position = 30
            time.sleep(0.15)
        _reachy.joints["l_antenna"].goal_position = 0
        _reachy.joints["r_antenna"].goal_position = 0
    _safe(_do)


def antenna_droop() -> None:
    """Droop antennas for wrong answer / sad."""
    def _do():
        _reachy.joints["l_antenna"].goal_position = -45
        _reachy.joints["r_antenna"].goal_position = -45
        time.sleep(1.0)
        _reachy.joints["l_antenna"].goal_position = 0
        _reachy.joints["r_antenna"].goal_position = 0
    _safe(_do)


def antenna_thinking() -> None:
    """Slow antenna sway while processing."""
    def _do():
        for _ in range(2):
            _reachy.joints["l_antenna"].goal_position = 15
            _reachy.joints["r_antenna"].goal_position = 15
            time.sleep(0.4)
            _reachy.joints["l_antenna"].goal_position = -15
            _reachy.joints["r_antenna"].goal_position = -15
            time.sleep(0.4)
        _reachy.joints["l_antenna"].goal_position = 0
        _reachy.joints["r_antenna"].goal_position = 0
    _safe(_do)



    """Context manager: tilt while in block, return to neutral after."""
    thinking()
    try:
        yield
    finally:
        speaking()
