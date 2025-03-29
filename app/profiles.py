"""Profile configuration system for the podcast generator."""

from dataclasses import dataclass, field

from providers.document.azure_document_intelligence import (
    AzureDocumentIntelligenceProvider,
)
from providers.document.base import DocumentProvider
from providers.llm.azure_openai import AzureOpenAIProvider
from providers.llm.base import LLMProvider
from providers.speech.azure_speech import AzureSpeechProvider
from providers.speech.base import SpeechProvider
from providers.speech.basic_speech import BasicSpeechProvider


@dataclass
class Profile:
    """Profile configuration for the podcast generator."""

    name: str
    document_provider: type[DocumentProvider]
    llm_provider: type[LLMProvider]
    speech_provider: type[SpeechProvider]
    document_provider_config: dict = field(default_factory=dict)
    llm_provider_config: dict = field(default_factory=dict)
    speech_provider_config: dict = field(default_factory=dict)

    def get_provider_classes(self) -> dict[str, type]:
        """Get all provider classes in this profile."""
        return {
            "document": self.document_provider,
            "llm": self.llm_provider,
            "speech": self.speech_provider,
        }

    def create_providers(self, **kwargs):
        """Create provider instances from the profile configuration.

        Args:
            **kwargs: Provider options from UI, organized by provider name
        """
        providers = {}

        # Create each provider with its config plus any UI options
        doc_config = self.document_provider_config.copy()
        doc_config.update(kwargs.get("document", {}))
        providers["document"] = self.document_provider(**doc_config)

        llm_config = self.llm_provider_config.copy()
        llm_config.update(kwargs.get("llm", {}))
        providers["llm"] = self.llm_provider(**llm_config)

        speech_config = self.speech_provider_config.copy()
        speech_config.update(kwargs.get("speech", {}))
        providers["speech"] = self.speech_provider(**speech_config)

        return providers


# Default Azure profile using all Azure services
AZURE_PROFILE = Profile(
    name="Azure",
    document_provider=AzureDocumentIntelligenceProvider,
    llm_provider=AzureOpenAIProvider,
    speech_provider=AzureSpeechProvider,
)

# Example profile using Azure services with basic speech
AZURE_BASIC_SPEECH_PROFILE = Profile(
    name="azure-basic-speech",
    document_provider=AzureDocumentIntelligenceProvider,
    llm_provider=AzureOpenAIProvider,
    speech_provider=BasicSpeechProvider,
    speech_provider_config={
        "voices": {
            "Andrew": "en-US-Male-1",
            "Emma": "en-US-Female-1",
        },
        "rate": "medium",
        "pitch": "medium",
    },
)

# Dictionary of available profiles
PROFILES = {
    "Azure": AZURE_PROFILE,
    "azure-basic-speech": AZURE_BASIC_SPEECH_PROFILE,
}
