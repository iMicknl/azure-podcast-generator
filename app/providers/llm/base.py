"""Base LLM provider interface."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, TypedDict

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

    @classmethod
    def render_default_ui(cls, st) -> dict[str, Any]:
        """Render LLM provider-specific default UI elements using Streamlit.

        Args:
            st: The Streamlit module to use for rendering UI elements

        Returns:
            Dict containing podcast_title and speaker names
        """
        options = {}

        # Podcast title input
        options["podcast_title"] = st.text_input("Podcast Title", value="AI in Action")

        # Speaker names in two columns
        col1, col2 = st.columns(2)

        with col1:
            options["speaker_1"] = st.text_input(
                "Speaker 1 Name",
                value="Andrew",
                help="Name of the first speaker in the podcast script",
            )

        with col2:
            options["speaker_2"] = st.text_input(
                "Speaker 2 Name",
                value="Ava",
                help="Name of the second speaker in the podcast script",
            )

        return options

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
