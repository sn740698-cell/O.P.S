import logging

logger = logging.getLogger(__name__)

class WisprFlowVoiceService:
    """
    Wispr Flow Voice-to-Text Integration Service for O.P.S.
    Triggers via global hotkey (Ctrl + Windows) to record, transcribe speech,
    and pipe text directly into the O.P.S. 7-Tier Intelligence Pipeline.
    """
    def __init__(self):
        self.is_listening = False
        self.trigger_hotkey = "Ctrl+Win"
        self.provider = "Wispr Flow"

    def toggle_listening(self):
        self.is_listening = not self.is_listening
        status = "started" if self.is_listening else "stopped"
        logger.info(f"[Wispr Flow] Voice recording {status} via hotkey {self.trigger_hotkey}.")
        return {
            "status": "recording" if self.is_listening else "idle",
            "is_listening": self.is_listening,
            "hotkey": self.trigger_hotkey,
            "provider": self.provider
        }

    def process_voice_transcript(self, transcript_text: str):
        """
        Receives transcribed text from Wispr Flow engine, cleans it,
        and prepares it for dispatch into the O.P.S. intent router.
        """
        cleaned_text = transcript_text.strip()
        logger.info(f"[Wispr Flow] Received transcript: '{cleaned_text}'")
        return {
            "transcript": cleaned_text,
            "length": len(cleaned_text),
            "status": "ready_for_dispatch",
            "provider": self.provider
        }

    def get_status(self):
        return {
            "provider": self.provider,
            "hotkey": self.trigger_hotkey,
            "is_listening": self.is_listening,
            "stt_engine": "Wispr Flow Low-Latency STT"
        }
