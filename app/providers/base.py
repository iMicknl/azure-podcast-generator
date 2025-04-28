"""Base provider interface for the podcast generator."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class Provider(ABC):
    """Abstract base class for all providers."""

    name: ClassVar[str] = ""  # Human readable name for the provider
    description: ClassVar[str] = ""  # Description of what the provider does

    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize the provider with optional configuration."""
        pass

    @classmethod
    def render_default_ui(cls, st) -> dict[str, Any]:
        """Render provider-specific default UI elements using Streamlit.

        This method should render required inputs that are needed for the provider
        to function, such as file uploads for document providers or titles for LLM providers.

        Args:
            st: The Streamlit module to use for rendering UI elements

        Returns:
            Dict of option names to their values selected in the UI
        """
        return {}

    @classmethod
    def render_options_ui(cls, st) -> dict[str, Any]:
        """Render provider-specific advanced options UI using Streamlit.

        Args:
            st: The Streamlit module to use for rendering UI elements

        Returns:
            Dict of option names to their values selected in the UI
        """
        return {}
