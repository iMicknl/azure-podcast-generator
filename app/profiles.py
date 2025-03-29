"""Profile configuration system for the podcast generator."""

from dataclasses import dataclass

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
    document_provider_config: dict = None
    llm_provider_config: dict = None
    speech_provider_config: dict = None

    def create_providers(self):
        """Create provider instances from the profile configuration."""
        return {
            "document": self.document_provider(**(self.document_provider_config or {})),
            "llm": self.llm_provider(**(self.llm_provider_config or {})),
            "speech": self.speech_provider(**(self.speech_provider_config or {})),
        }


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
