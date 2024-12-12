import json
import os
from dataclasses import dataclass
import streamlit as st
import tiktoken
from openai import AzureOpenAI
from openai.types import CompletionUsage
from utils.identity import get_token_provider

AZURE_OPENAI_API_VERSION = "2024-10-21"

BASE_PROMPT = """
Create a highly engaging podcast script between two people based on the input text. Use informal language to enhance the human-like quality of the conversation, including expressions like "wow," laughter, and pauses such as "uhm."

# Steps
1. Review the Document(s) and Podcast Title.
2. Adjust your plan to the requested podcast duration: {duration_description}.
3. Character Development: Define two distinct personalities for the hosts.
4. Script Structure: Outline introduction, main discussion, and conclusion.
5. Incorporate informal language and maintain a natural dialogue flow.
6. Engage with humor and emotion.

# Output Format
- A conversational podcast script in structured JSON.
- Include informal expressions and pauses.
- Use the provided host names exactly: {voice_1} and {voice_2}.
- The final JSON must follow the schema.

# Examples

**Input:**
- Document: [Brief overview of the content, main themes, or key points]
- Podcast Title: \"Exploring the Wonders of Space\"

**Output:**
- Speaker 1: \"Hey everyone, welcome to 'Exploring the Wonders of Space!' I'm [Name], and with me is [Name].\"
- Speaker 2: \"Hey! Uhm, I'm super excited about today's topic. Did you see the latest on the new satellite launch?\"
- Speaker 1: \"Wow, yes! It's incredible. I mean, imagine the data we'll get! [laughter]\"
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


def _get_client():
    # Authenticate
    if os.getenv("AZURE_OPENAI_KEY"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    else:
        client = AzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
            azure_ad_token_provider=get_token_provider(),
        )
    return client


def document_to_podcast_script(
    document: str,
    title: str = "AI in Action",
    voice_1: str = "Andrew",
    voice_2: str = "Emma",
) -> PodcastScriptResponse:
    """Single-shot short podcast script generation."""
    duration_description = "about 2-3 minutes"
    prompt = BASE_PROMPT.format(
        duration_description=duration_description, voice_1=voice_1, voice_2=voice_2
    )

    client = _get_client()

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"<title>{title}</title><documents><document>{document}</document></documents>",
            },
        ],
        model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o"),
        temperature=0.7,
        response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
        max_tokens=8000,
    )

    message = chat_completion.choices[0].message.content
    json_message = json.loads(message)

    return PodcastScriptResponse(podcast=json_message, usage=chat_completion.usage)


def document_to_podcast_script_iterative(
    document: str,
    title: str = "AI in Action",
    voice_1: str = "Andrew",
    voice_2: str = "Emma",
    duration: str = "medium",
) -> PodcastScriptResponse:
    """
    Iterative generation for medium / long podcasts.
    duration: "medium" (10-15 min), "long" (20-30 min)
    The idea: generate in multiple segments.
    """
    if duration == "medium":
        # For a 10-15 min podcast, let's do 4 segments.
        total_segments = 4
        duration_description = "about 10-15 minutes total"
    else:
        # For a 20-30 min podcast, let's do 8 segments.
        total_segments = 8
        duration_description = "about 20-30 minutes total"

    prompt = BASE_PROMPT.format(
        duration_description=duration_description, voice_1=voice_1, voice_2=voice_2
    )

    client = _get_client()

    all_script_items = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # We'll guide the model step-by-step.
    # On each iteration, we provide the document and what we have so far.
    for segment_index in range(total_segments):
        segment_number = segment_index + 1
        user_content = (
            f"<title>{title}</title>"
            f"<documents><document>{document}</document></documents>\n\n"
            f"We are creating a podcast of {duration_description}. "
            f"This is segment {segment_number} out of {total_segments}. "
            f"{'Below is what has been generated so far:' if segment_number > 1 else 'No previous segment.'}"
        )

        if segment_number > 1:
            # Include previously generated script in the user prompt for continuity
            existing_script_text = ""
            for line in all_script_items:
                existing_script_text += f"{line['name']}: {line['message']}\n"
            user_content += f"\n\nPreviously generated script:\n{existing_script_text}"

            user_content += "\n\nPlease continue the conversation naturally from where it left off."

        # Make the request
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
            model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o"),
            temperature=0.7,
            response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
            max_tokens=8000,
        )

        message = chat_completion.choices[0].message.content
        json_message = json.loads(message)

        # Append to the global script
        # NOTE: We assume the model returns a full script object each time.
        # We'll just append the "script" items. The first call defines language, etc.
        if segment_number == 1:
            # On first segment, store config + script
            combined_podcast = json_message
        else:
            # Append script lines from subsequent segments
            combined_podcast["script"].extend(json_message["script"])

        # Update usage tokens
        total_prompt_tokens += chat_completion.usage.prompt_tokens
        total_completion_tokens += chat_completion.usage.completion_tokens

        # Update our running script items
        all_script_items = combined_podcast["script"]

    # After all segments generated, we have a combined script.
    # Return combined result.
    # Create a mock usage object summarizing total usage
    combined_usage = CompletionUsage(
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        total_tokens=total_prompt_tokens + total_completion_tokens,
    )
    return PodcastScriptResponse(podcast=combined_podcast, usage=combined_usage)


@st.cache_resource
def get_encoding() -> tiktoken.Encoding:
    """Get TikToken."""
    encoding = tiktoken.encoding_for_model("gpt-4o")
    return encoding
