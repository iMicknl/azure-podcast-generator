"""Base LLM provider interface."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import TypedDict

from providers.base import Provider


class PodcastConfig(TypedDict):
    """Type definition for podcast configuration."""

    language: str


class PodcastScript(TypedDict):
    """Type definition for a single script entry."""

    speaker: str
    message: str


class PodcastContent(TypedDict):
    """Type definition for the full podcast content."""

    config: PodcastConfig
    script: list[PodcastScript]


@dataclass
class PodcastScriptResponse:
    """Podcast script response with generated content and usage metrics."""

    podcast: PodcastContent
    cost: float = 0.0  # Cost in USD for the LLM processing


class LLMProvider(Provider):
    """Base class for LLM providers."""

    @abstractmethod
    def document_to_podcast_script(
        self,
        document: str,
        title: str,
        voice_1: str,
        voice_2: str,
        max_tokens: int,
    ) -> PodcastScriptResponse:
        """Convert document to podcast script.

        Args:
            document: The document content as string
            title: The podcast title
            voice_1: The first voice name
            voice_2: The second voice name
            max_tokens: Maximum tokens for generation

        Returns:
            PodcastScriptResponse with generated podcast script and usage metrics
        """
        pass
