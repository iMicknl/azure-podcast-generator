"""Azure OpenAI provider implementation."""

import json
import os
from typing import Any

import streamlit as st
import tiktoken
from openai import AzureOpenAI
from providers.llm.base import LLMProvider, PodcastScriptResponse
from utils.identity import get_token_provider

AZURE_OPENAI_API_VERSION = "2024-10-21"

PROMPT = """
Create a highly engaging podcast script between two people based on the input text. Use informal language to enhance the human-like quality of the conversation, including expressions like \"wow,\", and pauses such as \"uhm.\"

# Steps

1. **Review the Document(s) and Podcast Title**: Understand the main themes, key points, interesting facts and tone.
2. **Adjust your plan to the requested podcast duration**: The conversation should be engaging and take about 5 minutes to read out loud.
3. **Character Development**: Define two distinct personalities for the hosts.
4. **Script Structure**: Outline the introduction, main discussion, and conclusion.
5. **Incorporate Informal Language**: Use expressions and fillers to create a natural dialogue flow.
6. **Engage with Humor and Emotion**: Include laughter and emotional responses to make the conversation lively. Think about how the hosts would react to the content and make it an engaging conversation.


# Output Format

- A conversational podcast script in structured JSON.
- Include informal expressions and pauses.
- Clearly mark speaker turns.
- Name the hosts {voice_1} and {voice_2}.

# Examples

**Input:**
- Document: [Brief overview of the content, main themes, or key points]
- Podcast Title: \"Exploring the Wonders of Space\"

**Output:**
- Speaker 1: \"Hey everyone, welcome to 'Exploring the Wonders of Space!' I'm [Name], and with me is [Name].\"
- Speaker 2: \"Hey! Uhm, I'm super excited about today's topic. Did you see the latest on the new satellite launch?\"
- Speaker 1: \"Wow, yes! It's incredible. I mean, imagine the data we'll get!\"
- (Continue with discussion, incorporating humor and informal language)

# Notes

- Maintain a balance between informal language and clear communication.
- Ensure the conversation is coherent and follows a logical progression.
- Adapt the style and tone based on the document's content and podcast title.
- Think step by step, grasp the key points of the document / paper, and explain them in a conversational tone.
""".strip()

JSON_SCHEMA = {
    "name": "podcast",
    "strict": True,
    "description": "An AI generated podcast script.",
    "schema": {
        "type": "object",
        "properties": {
            "config": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Language code + locale (BCP-47), e.g. en-US or es-PA",
                    }
                },
                "required": ["language"],
                "additionalProperties": False,
            },
            "script": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the host. Use the provided names, don't change the casing or name.",
                        },
                        "message": {"type": "string"},
                    },
                    "required": ["name", "message"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["config", "script"],
        "additionalProperties": False,
    },
}


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider for podcast script generation."""

    def __init__(self, **kwargs):
        """Initialize the Azure OpenAI provider."""
        self.api_key = kwargs.get("api_key", os.environ.get("AZURE_OPENAI_KEY"))
        self.endpoint = kwargs.get("endpoint", os.environ.get("AZURE_OPENAI_ENDPOINT"))
        self.model = kwargs.get(
            "model", os.environ.get("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o")
        )
        self.api_version = kwargs.get("api_version", AZURE_OPENAI_API_VERSION)
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 8000)

    @classmethod
    def render_options_ui(cls, st) -> dict[str, Any]:
        """Render Azure OpenAI specific options using Streamlit widgets."""
        options = {}
        col1, col2 = st.columns(2)

        with col1:
            options["temperature"] = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Controls randomness in the generation. Higher values make the output more random, lower values make it more focused and deterministic.",
            )

        with col2:
            options["max_tokens"] = st.number_input(
                "Max Tokens",
                min_value=1000,
                max_value=128000,
                value=8000,
                step=1000,
                help="Maximum number of tokens (words/subwords) to generate in the response",
            )

        return options

    def document_to_podcast_script(
        self,
        document: str,
        title: str = "AI in Action",
        voice_1: str = "Andrew",
        voice_2: str = "Ava",
    ) -> PodcastScriptResponse:
        """Convert document to podcast script using Azure OpenAI.

        Args:
            document: The document content as string
            title: The podcast title
            voice_1: The first voice name
            voice_2: The second voice name

        Returns:
            PodcastScriptResponse with generated podcast script and usage metrics
        """
        # Authenticate via API key (not advised for production)
        if self.api_key:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )
        # Authenticate via DefaultAzureCredential (e.g. managed identity or Azure CLI)
        else:
            client = AzureOpenAI(
                api_version=self.api_version,
                azure_ad_token_provider=get_token_provider(),
            )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": PROMPT.format(voice_1=voice_1, voice_2=voice_2),
                },
                # Wrap the document in <documents> tag for Prompt Shield Indirect attacks
                # https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter?tabs=warning%2Cindirect%2Cpython-new#embedding-documents-in-your-prompt
                {
                    "role": "user",
                    "content": f"<title>{title}</title><documents><document>{document}</document></documents>",
                },
            ],
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
            max_tokens=self.max_tokens,
        )

        message = chat_completion.choices[0].message.content
        json_message = json.loads(message)

        return PodcastScriptResponse(podcast=json_message, usage=chat_completion.usage)


@st.cache_resource
def get_encoding() -> tiktoken.Encoding:
    """Get TikToken."""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    return encoding
