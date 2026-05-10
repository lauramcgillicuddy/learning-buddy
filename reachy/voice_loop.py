"""Continuous voice loop for Reachy — listen, think, speak, react."""

import threading
from reachy import controller
from ai.client import chat, reset_conversation
from voice.stt import transcribe, listen as local_listen, _load_model
from voice.tts import speak


def _listen(duration: float) -> str:
    """Record from Reachy's mic if connected, otherwise fall back to local mic."""
    raw = controller.record_audio(duration=duration)
    if raw is not None:
        return transcribe(raw)
    print("[Voice] Reachy mic unavailable — using local microphone")
    return local_listen(duration=duration)


def run(wake_word: str = "hey buddy", duration: float = 6.0):
    """
    Continuous loop:
      1. Listen via Reachy's built-in microphone (falls back to local mic)
      2. Transcribe with faster-whisper
      3. Get AI response
      4. Speak reply + animate Reachy
    Press Ctrl+C to stop.
    """
    reset_conversation()

    # Pre-warm Whisper so the first response isn't slow
    print("[Learning Buddy] Loading speech model...")
    _load_model()

    # Open Reachy's mic once for the whole session (WebRTC needs ~2s to settle)
    controller.start_audio_session()

    print("[Learning Buddy] Voice loop started — start talking!")
    print("[Learning Buddy] Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                controller.listening_pose()
                print(f"[Listening for {duration:.0f}s...]")
                text = _listen(duration=duration)

                if not text.strip():
                    print("[heard nothing — listening again]")
                    continue

                print(f"You: {text}")

                threading.Thread(target=controller.antenna_thinking, daemon=True).start()
                reply = chat(text)
                print(f"Buddy: {reply}\n")

                controller.speaking()
                speak(reply)

                threading.Thread(target=controller.nod, args=(1,), daemon=True).start()

            except Exception as e:
                print(f"[Error] {e}")
                continue

    except KeyboardInterrupt:
        print("\n[Learning Buddy] Voice loop stopped.")
    finally:
        controller.stop_audio_session()
