"""Module for LLM utils."""

import json
import os
from dataclasses import dataclass

import streamlit as st
import tiktoken
from openai import AzureOpenAI
from openai.types import CompletionUsage
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


@dataclass
class PodcastScriptResponse:
    podcast: dict
    usage: CompletionUsage


def document_to_podcast_script(
    document: str,
    title: str = "AI in Action",
    voice_1: str = "Andrew",
    voice_2: str = "Emma",
    max_tokens: int = 8000,
) -> PodcastScriptResponse:
    """Get LLM response."""

    # Authenticate via API key (not advised for production)
    if os.getenv("AZURE_OPENAI_KEY"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    # Authenticate via DefaultAzureCredential (e.g. managed identity or Azure CLI)
    else:
        client = AzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
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
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o"),
        temperature=0.7,
        response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
        max_tokens=max_tokens,
    )

    message = chat_completion.choices[0].message.content
    json_message = json.loads(message)

    return PodcastScriptResponse(podcast=json_message, usage=chat_completion.usage)


@st.cache_resource
def get_encoding() -> tiktoken.Encoding:
    """Get TikToken."""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    return encoding
