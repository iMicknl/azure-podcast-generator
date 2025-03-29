"""Module for Document Processing utils."""

import os
from dataclasses import dataclass

import streamlit as st
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    DocumentContentFormat,
)
from azure.core.credentials import AzureKeyCredential
from utils.identity import get_azure_credential


@dataclass
class DocumentResponse:
    markdown: str
    pages: int


@st.cache_data
def document_to_markdown(file: bytes) -> DocumentResponse:
    """Convert document to markdown using Azure Document Intelligence."""

    if os.getenv("DOCUMENTINTELLIGENCE_API_KEY"):
        doc_client = DocumentIntelligenceClient(
            endpoint=os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["DOCUMENTINTELLIGENCE_API_KEY"]),
        )
    else:
        doc_client = DocumentIntelligenceClient(
            endpoint=os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"],
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

    return DocumentResponse(markdown=markdown, pages=pages)
