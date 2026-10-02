"""
Test Suite for O.P.S.: Multimodal Perception & Voice Engine
Tests:
1. Vision: Desktop Screen Capture & Base64 PNG Encoding.
2. Vision: Visual Reasoning & UI Element Detection with Bounding Boxes.
3. Voice: Text-to-Speech (TTS) Neural Audio Synthesis.
4. Voice: Speech-to-Text (STT) Audio Transcription.
5. REST API: /vision/screenshot/, /vision/analyze/, and /voice/synthesize/ Endpoints.
"""

import os
import sys
import json
import base64
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from rest_framework.test import APIClient
from ops_core.services.vision_service import OPSVisionService
from ops_core.services.voice_service import WisprFlowVoiceService


class TestMultimodalPerception(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()
        self.vision = OPSVisionService()
        self.voice = WisprFlowVoiceService()

    def test_01_screen_capture_and_encoding(self):
        """Test capturing desktop screen and base64 PNG output."""
        capture = self.vision.capture_screenshot()

        self.assertEqual(capture.get("status"), "success")
        self.assertGreater(capture.get("width", 0), 0)
        self.assertGreater(capture.get("height", 0), 0)
        self.assertEqual(capture.get("format"), "PNG")
        self.assertTrue(len(capture.get("base64", "")) > 100)

        # Validate base64 decodability
        raw_bytes = base64.b64decode(capture["base64"])
        self.assertTrue(raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_02_visual_analysis_and_ui_detection(self):
        """Test visual reasoning and bounding box detection for UI elements."""
        res = self.vision.analyze_screen("Find search box and submit button")

        self.assertEqual(res.get("status"), "success")
        self.assertIn("analysis", res)
        detected = res.get("detected_elements", [])
        self.assertGreaterEqual(len(detected), 1)

        first_element = detected[0]
        self.assertIn("label", first_element)
        self.assertIn("bbox", first_element)
        self.assertEqual(len(first_element["bbox"]), 4)

    def test_03_voice_synthesize_speech(self):
        """Test Piper TTS neural voice synthesis."""
        text = "Hello! O.P.S. multimodal engine is operational."
        res = self.voice.synthesize_speech(text)

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("format"), "WAV")
        self.assertTrue(len(res.get("audio_base64", "")) > 50)

        # Validate WAV header (RIFF...WAVE)
        raw_audio = base64.b64decode(res["audio_base64"])
        self.assertTrue(raw_audio.startswith(b"RIFF"))

    def test_04_voice_transcription(self):
        """Test audio transcription pipeline."""
        dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        res = self.voice.transcribe_audio_bytes(dummy_audio)

        self.assertEqual(res.get("status"), "success")
        self.assertIn("transcript", res)
        self.assertGreater(len(res["transcript"]), 0)

    def test_05_rest_api_vision_and_voice(self):
        """Test REST API endpoints for screenshot, vision analysis, and voice synthesis."""
        # 1. Screenshot API
        res_screen = self.client.get('/api/v1/vision/screenshot/')
        self.assertEqual(res_screen.status_code, 200)
        self.assertEqual(res_screen.json().get("format"), "PNG")

        # 2. Vision Analyze API
        res_analyze = self.client.post('/api/v1/vision/analyze/', {
            "prompt": "Detect open application windows"
        }, format='json')
        self.assertEqual(res_analyze.status_code, 200)
        self.assertIn("detected_elements", res_analyze.json())

        # 3. Voice Synthesize API
        res_voice = self.client.post('/api/v1/voice/synthesize/', {
            "text": "System check passed"
        }, format='json')
        self.assertEqual(res_voice.status_code, 200)
        self.assertEqual(res_voice.json().get("format"), "WAV")


if __name__ == "__main__":
    unittest.main()
