"""Base document provider interface."""

from abc import abstractmethod
from dataclasses import dataclass

from providers.base import Provider


@dataclass
class DocumentResponse:
    """Document response with markdown content and page count."""

    markdown: str
    pages: int
    cost: float = 0.0  # Cost in USD for the document processing


class DocumentProvider(Provider):
    """Base class for document processing providers."""

    @abstractmethod
    def document_to_markdown(self, file: bytes) -> DocumentResponse:
        """Convert document to markdown.

        Args:
            file: The document file as bytes

        Returns:
            DocumentResponse with markdown and page count
        """
        pass
