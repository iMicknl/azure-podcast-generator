"""Configuration system for the podcast generator."""

from dataclasses import dataclass, field

from providers.document.azure_document_intelligence import (
    AzureDocumentIntelligenceProvider,
)
from providers.document.base import DocumentProvider
from providers.document.markitdown import MarkItDownProvider
from providers.llm.azure_openai import AzureOpenAIProvider
from providers.llm.base import LLMProvider
from providers.speech.azure_speech import AzureSpeechProvider
from providers.speech.azure_speech_multitalker import AzureSpeechMultitalker
from providers.speech.base import SpeechProvider


@dataclass
class Configuration:
    """Configuration for the podcast generator."""

    document_provider: type[DocumentProvider]
    llm_provider: type[LLMProvider]
    speech_provider: type[SpeechProvider]
    document_provider_config: dict = field(default_factory=dict)
    llm_provider_config: dict = field(default_factory=dict)
    speech_provider_config: dict = field(default_factory=dict)

    def create_providers(
        self, default_options=None, **kwargs
    ) -> dict[str, DocumentProvider | LLMProvider | SpeechProvider]:
        """Create provider instances from the configuration.

        Args:
            default_options: Provider default options from UI, organized by provider name
            **kwargs: Provider advanced options from UI, organized by provider name

        Returns:
            A dictionary mapping provider types to their instances
        """
        providers: dict[str, DocumentProvider | LLMProvider | SpeechProvider] = {}
        default_options = default_options or {}

        # Create each provider with its config plus any UI options (both default and advanced)
        doc_config = self.document_provider_config.copy()
        doc_config.update(default_options.get("document", {}))
        doc_config.update(kwargs.get("document", {}))
        providers["document"] = self.document_provider(**doc_config)

        llm_config = self.llm_provider_config.copy()
        llm_config.update(default_options.get("llm", {}))
        llm_config.update(kwargs.get("llm", {}))
        providers["llm"] = self.llm_provider(**llm_config)

        speech_config = self.speech_provider_config.copy()
        speech_config.update(default_options.get("speech", {}))
        speech_config.update(kwargs.get("speech", {}))
        providers["speech"] = self.speech_provider(**speech_config)

        return providers


# Available providers by type
DOCUMENT_PROVIDERS: dict[str, type[DocumentProvider]] = {
    AzureDocumentIntelligenceProvider.name: AzureDocumentIntelligenceProvider,
    MarkItDownProvider.name: MarkItDownProvider,
}

LLM_PROVIDERS: dict[str, type[LLMProvider]] = {
    AzureOpenAIProvider.name: AzureOpenAIProvider,
}

SPEECH_PROVIDERS: dict[str, type[SpeechProvider]] = {
    AzureSpeechProvider.name: AzureSpeechProvider,
    AzureSpeechMultitalker.name: AzureSpeechMultitalker,
}
