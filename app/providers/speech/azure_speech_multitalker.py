"""Basic speech provider implementation with simple SSML support."""

from providers.speech.base import SpeechProvider


class AzureSpeechMultitalker(SpeechProvider):
    """Basic speech provider for text-to-speech conversion.

    This is a template implementation that shows how to implement a custom
    speech provider. It uses a basic SSML format and could be extended to
    work with other TTS services or local TTS engines.
    """

    def __init__(self, **kwargs):
        """Initialize the Basic Speech provider."""
        self.voices = kwargs.get("voices", {"Andrew": "andrew", "Ava": "ava"})

    def text_to_speech(self, ssml: str) -> bytes:
        """Convert SSML to audio.

        This is a template implementation. You would need to implement
        the actual TTS logic here using your preferred TTS engine.

        Args:
            ssml: The SSML text to convert to speech

        Returns:
            bytes of audio data
        """
        # This is where you would implement the actual TTS conversion
        # For example, using a local TTS engine or another cloud service
        raise NotImplementedError(
            "This is a template implementation. You need to implement the actual TTS logic."
        )

    def podcast_script_to_ssml(self, podcast: dict) -> str:
        """Convert podcast script to multitalker SSML.

        Args:
            podcast: The podcast script data

        Returns:
            SSML string for speech synthesis with multitalker support
        """
        podcast_script = podcast["script"]
        language = podcast.get("config", {}).get("language", "en-US")

        # Start with the SSML header and multitalker-specific namespace
        ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        ssml += 'xmlns:mstts="https://www.w3.org/2001/mstts" '
        ssml += f'xml:lang="{language}">'

        # Create the voice wrapper for the entire dialog
        ssml += '<voice name="en-US-MultiTalker-Ava-Andrew:DragonHDLatestNeural">'
        ssml += "<mstts:dialog>"

        for line in podcast_script:
            # Escape SSML special characters
            message = (
                line["message"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
            )

            # Convert speaker name to lowercase for the turn attribute
            speaker = line["name"].lower()
            ssml += f'<mstts:turn speaker="{speaker}">{message}</mstts:turn>'

        # Close all tags
        ssml += "</mstts:dialog></voice></speak>"
        return ssml
