"""Speech provider interface."""

from abc import abstractmethod
from dataclasses import dataclass

from providers.base import Provider
from providers.llm.base import PodcastContent


@dataclass
class SpeechResponse:
    """Speech response with audio data and cost."""

    audio: bytes
    cost: float = 0.0  # Cost in USD for the speech synthesis


class SpeechProvider(Provider):
    """Base class for speech synthesis providers."""

    @abstractmethod
    def text_to_speech(self, ssml: str) -> SpeechResponse:
        """Convert SSML to audio.

        Args:
            ssml: The SSML text to convert to speech

        Returns:
            SpeechResponse containing audio data and cost
        """
        pass

    @abstractmethod
    def podcast_script_to_ssml(self, podcast: PodcastContent) -> str:
        """Convert podcast script to SSML.

        Args:
            podcast: The podcast script data including configuration and dialogue

        Returns:
            SSML string for speech synthesis
        """
        pass
