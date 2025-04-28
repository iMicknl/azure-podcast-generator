"""Document provider interface."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from providers.base import Provider


@dataclass
class DocumentResponse:
    """Document response with markdown content and page count."""

    markdown: str
    pages: int
    cost: float = 0.0  # Cost in USD for the document processing


class DocumentProvider(Provider):
    """Base class for document processing providers."""

    @property
    def supported_file_types(self) -> list[str]:
        """Get the supported file types for this provider.

        Returns:
            List of supported file extensions
        """
        return ["pdf", "doc", "docx", "ppt", "pptx", "txt", "md"]

    @classmethod
    def render_default_ui(cls, st) -> dict[str, Any]:
        """Render document provider-specific default UI elements using Streamlit.

        Args:
            st: The Streamlit module to use for rendering UI elements

        Returns:
            Dict containing uploaded_file with the file object
        """
        # Create a temporary instance to access instance properties
        temp_provider = cls()

        # Get supported file types
        supported_file_types = getattr(
            temp_provider,
            "supported_file_types",
            ["pdf", "doc", "docx", "ppt", "pptx", "txt", "md"],
        )

        # File upload
        uploaded_file = st.file_uploader(
            "Upload your document",
            accept_multiple_files=False,
            type=supported_file_types,
        )

        return {"uploaded_file": uploaded_file}

    @abstractmethod
    def document_to_markdown(self, file: bytes) -> DocumentResponse:
        """Convert document to markdown.

        Args:
            file: The document file as bytes

        Returns:
            DocumentResponse with markdown and page count
        """
        pass
