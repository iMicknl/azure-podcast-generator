"""Base speech provider interface."""

from abc import abstractmethod

from providers.base import Provider


class SpeechProvider(Provider):
    """Base class for speech synthesis providers."""

    @abstractmethod
    def text_to_speech(self, ssml: str) -> bytes:
        """Convert SSML to audio.

        Args:
            ssml: The SSML text to convert to speech

        Returns:
            bytes of audio data
        """
        pass

    @abstractmethod
    def podcast_script_to_ssml(self, podcast: dict) -> str:
        """Convert podcast script to SSML.

        Args:
            podcast: The podcast script data

        Returns:
            SSML string for speech synthesis
        """
        pass
