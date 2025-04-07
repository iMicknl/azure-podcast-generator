"""MarkItDown provider implementation."""

import io

from markitdown import MarkItDown as MDClient
from providers.document.base import DocumentProvider, DocumentResponse


class MarkItDownProvider(DocumentProvider):
    """MarkItDown provider for document processing."""

    name = "MarkItDown"
    description = "Open-source document conversion tool for PDFs, Word, Excel, PowerPoint, images, and more."

    def __init__(self, **kwargs):
        """Initialize the MarkItDown provider."""
        self.docintel_endpoint = kwargs.get("docintel_endpoint", None)
        self.llm_client = kwargs.get("llm_client", None)
        self.llm_model = kwargs.get("llm_model", None)

    @classmethod
    def render_options_ui(cls, st) -> dict:
        """Render MarkItDown specific options using Streamlit widgets."""
        options = {}
        return options

    @property
    def supported_file_types(self):
        """Get the supported file types for this provider."""
        return [
            "pdf",
            "doc",
            "docx",
            "ppt",
            "pptx",
            "xls",
            "xlsx",
            "txt",
            "md",
            "html",
            "htm",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "msg",
            "zip",
            "epub",
            "csv",
        ]

    def document_to_markdown(self, file: bytes) -> DocumentResponse:
        """Convert document to markdown using MarkItDown.

        Args:
            file: The document file as bytes

        Returns:
            DocumentResponse with markdown content and page count
        """
        # Create a file-like object from bytes
        file_obj = io.BytesIO(file)

        # Initialize MarkItDown client with configurations
        md_client = MDClient(
            enable_plugins=False,  # Plugins are disabled by default
            docintel_endpoint=self.docintel_endpoint,
            llm_client=self.llm_client,
            llm_model=self.llm_model,
        )

        # Convert the document to markdown
        result = md_client.convert_stream(file_obj)

        # Return document response with markdown content
        # MarkItDown doesn't explicitly return page count, assuming 1 for now
        # and no cost since it's open source
        return DocumentResponse(
            markdown=result.text_content,
            pages=0,  # MarkItDown doesn't explicitly return page count
            cost=0.0,
        )
