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
        return True
    except Exception as e:
        print(f"[Reachy] Could not connect to {config.REACHY_HOST}: {e}")
        print("[Reachy] Running without robot — voice + CLI still work.")
        _connected = False
        return False


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


@contextmanager
def thinking_context():
    """Context manager: tilt while in block, return to neutral after."""
    thinking()
    try:
        yield
    finally:
        speaking()
