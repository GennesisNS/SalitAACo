import logging

import requests

logger = logging.getLogger(__name__)


class ElevenLabsError(Exception):
    """ElevenLabs could not be reached, or refused the request."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ElevenLabs:
    """
    Text to speech and voice cloning through the ElevenLabs API (https://elevenlabs.io/docs).

    Usage:

    elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY, model_id=settings.ELEVENLABS_MODEL)
    mp3_bytes = elevenlabs.text_to_speech(voice_id, "gusto ko")
    voice_id = elevenlabs.add_voice("Nanay", "sample.webm", sample_bytes, "audio/webm")
    elevenlabs.delete_voice(voice_id)
    """

    BASE_URL = "https://api.elevenlabs.io"
    TIMEOUT_SECONDS = 60
    OUTPUT_FORMAT = "mp3_44100_128"

    def __init__(self, api_key: str, model_id: str = "eleven_multilingual_v2"):
        if not api_key:
            raise ValueError("An ElevenLabs API key is needed (ELEVENLABS_API_KEY in .env).")
        self.api_key = api_key
        self.model_id = model_id

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = {"xi-api-key": self.api_key, **kwargs.pop("headers", {})}
        url = f"{self.BASE_URL}{path}"

        try:
            response = requests.request(method, url, headers=headers, timeout=self.TIMEOUT_SECONDS, **kwargs)
        except requests.RequestException as error:
            logger.error("ElevenLabs %s %s failed: %s", method, path, error)
            raise ElevenLabsError(f"Could not reach ElevenLabs: {error}") from error

        if not response.ok:
            detail = response.text[:300]
            logger.error("ElevenLabs %s %s answered %s: %s", method, path, response.status_code, detail)
            raise ElevenLabsError(f"ElevenLabs answered {response.status_code}: {detail}", response.status_code)

        logger.info("ElevenLabs %s %s answered %s", method, path, response.status_code)
        return response

    def text_to_speech(self, voice_id: str, text: str) -> bytes:
        """The MP3 of `text` spoken in the voice `voice_id`."""
        response = self._request(
            "POST",
            f"/v1/text-to-speech/{voice_id}",
            params={"output_format": self.OUTPUT_FORMAT},
            json={"text": text, "model_id": self.model_id},
        )
        return response.content

    def add_voice(self, name: str, sample_name: str, sample: bytes, sample_mime: str, description: str = "") -> str:
        """Clone a voice from one recording (instant voice cloning). Returns the new voice's ID."""
        response = self._request(
            "POST",
            "/v1/voices/add",
            data={"name": name, "description": description},
            files=[("files", (sample_name, sample, sample_mime))],
        )
        result = response.json()
        if result.get("requires_verification"):
            logger.warning("ElevenLabs voice %s needs verification before it can be used", result.get("voice_id"))
        return result["voice_id"]

    def delete_voice(self, voice_id: str) -> None:
        self._request("DELETE", f"/v1/voices/{voice_id}")
