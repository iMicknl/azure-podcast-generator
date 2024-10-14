"""Module for Document Processing utils."""

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, ContentFormat

import os
from azure.core.credentials import AzureKeyCredential


def document_to_markdown(file: bytes):
    document_request = AnalyzeDocumentRequest(bytes_source=file)

    doc_client = DocumentIntelligenceClient(
        endpoint=os.environ["DOCUMENTINTELLIGENCE_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["DOCUMENTINTELLIGENCE_API_KEY"]),
    )
    poller = doc_client.begin_analyze_document(
        "prebuilt-layout",
        document_request,
        output_content_format=ContentFormat.MARKDOWN,
    )
    result = poller.result()
    markdown = result.content

    return markdown
