"""Azure Document Intelligence provider implementation."""

import os

import streamlit as st
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    DocumentContentFormat,
)
from azure.core.credentials import AzureKeyCredential
from providers.document.base import DocumentProvider, DocumentResponse
from utils.identity import get_azure_credential


@st.cache_data
def _cached_document_to_markdown(
    endpoint: str,
    file: bytes,
    api_key: str = None,
) -> DocumentResponse:
    """Cached version of document to markdown conversion.

    Args:
        endpoint: The Azure Document Intelligence endpoint
        file: The document file as bytes
        api_key: Optional API key for authentication

    Returns:
        DocumentResponse with markdown and page count
    """
    if api_key:
        doc_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )
    else:
        doc_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=get_azure_credential(),
        )

    document_request = AnalyzeDocumentRequest(bytes_source=file)

    poller = doc_client.begin_analyze_document(
        "prebuilt-layout",
        document_request,
        output_content_format=DocumentContentFormat.MARKDOWN,
    )
    result = poller.result()

    markdown = result.content
    pages = len(result.pages)

    # Calculate cost: $10 per 1,000 pages for Layout API
    cost = 10 * (pages / 1_000)

    return DocumentResponse(markdown=markdown, pages=pages, cost=cost)


class AzureDocumentIntelligenceProvider(DocumentProvider):
    """Azure Document Intelligence provider for document processing."""

    name = "Azure Document Intelligence"
    description = "Extract text and structure from PDFs, images and Office documents using Azure Document Intelligence's Layout API"

    def __init__(self, **kwargs):
        """Initialize the Azure Document Intelligence provider."""
        self.endpoint = kwargs.get(
            "endpoint", os.environ.get("DOCUMENTINTELLIGENCE_ENDPOINT")
        )
        self.api_key = kwargs.get(
            "api_key", os.environ.get("DOCUMENTINTELLIGENCE_API_KEY")
        )

    def document_to_markdown(self, file: bytes) -> DocumentResponse:
        """Convert document to markdown using Azure Document Intelligence.

        Args:
            file: The document file as bytes

        Returns:
            DocumentResponse with markdown and page count
        """
        return _cached_document_to_markdown(
            endpoint=self.endpoint,
            file=file,
            api_key=self.api_key,
        )
