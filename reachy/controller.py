"""Reachy Mini controller using the official reachy-mini SDK."""

import time
import threading
import numpy as np
from contextlib import contextmanager

import config

_reachy = None
_connected = False
_recording = False


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


def start_audio_session() -> None:
    """Open Reachy's mic once for the whole voice loop session."""
    global _recording
    if not _connected or not _reachy or _recording:
        return
    try:
        _reachy.media.start_recording()
        _recording = True
        time.sleep(2.5)  # let WebRTC audio chain settle before first capture
        print("[Reachy] Microphone ready")
    except Exception as e:
        print(f"[Reachy] Could not open mic: {e}")


def stop_audio_session() -> None:
    global _recording
    if _connected and _reachy and _recording:
        try:
            _reachy.media.stop_recording()
        except Exception:
            pass
        _recording = False


def play_audio(wav_bytes: bytes) -> None:
    """Play WAV audio through Reachy's built-in speaker."""
    if not _connected or not _reachy:
        return
    try:
        import io
        import soundfile as sf

        data, samplerate = sf.read(io.BytesIO(wav_bytes), dtype="float32")
        # Convert to mono
        if data.ndim == 2:
            data = np.mean(data, axis=1)
        # Resample to 16 kHz if needed
        if samplerate != 16000:
            ratio = 16000 / samplerate
            n = int(len(data) * ratio)
            data = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)
        # Reachy expects shape (n, 1)
        samples = data.reshape(-1, 1).astype(np.float32)
        duration = len(samples) / 16000.0

        _reachy.media.start_playing()
        _reachy.media.push_audio_sample(samples)
        time.sleep(duration)
        _reachy.media.stop_playing()
    except Exception as e:
        print(f"[Reachy] Speaker error: {e}")


def record_audio(duration: float = 6.0) -> "np.ndarray | None":
    """Capture audio from Reachy's mic for `duration` seconds.

    Requires start_audio_session() to have been called first.
    Returns mono float32 numpy array at 16 kHz, or None if unavailable.
    """
    if not _connected or not _reachy or not _recording:
        return None
    try:
        chunks = []
        deadline = time.time() + duration
        while time.time() < deadline:
            samples = _reachy.media.get_audio_sample()
            if samples is not None:
                chunks.append(samples)
            time.sleep(0.05)
        print(f"[Reachy] Mic: collected {len(chunks)} chunks")
        if not chunks:
            print("[Reachy] Mic: no data — WebRTC audio may not be streaming from robot")
            return None
        audio = np.concatenate(chunks, axis=0)
        print(f"[Reachy] Mic: audio shape={audio.shape}, max={np.abs(audio).max():.4f}")
        if audio.ndim == 2:
            audio = np.mean(audio, axis=1)
        return audio.astype(np.float32)
    except Exception as e:
        print(f"[Reachy] Mic error: {e}")
        return None
