"""Module for LLM utils."""

from openai import AzureOpenAI
import os
import tiktoken
import streamlit as st

from utils.identity import get_token_provider

PROMPT = """
        Create a conversational, engaging podcast script named '{title}' between two hosts from the input text. Use informal language like haha, wow etc. and keep it engaging.
        Think step by step, grasp the key points of the paper, and explain them in a conversational tone, at the end, summarize. 
        Output into SSML format like below, please don't change voice name.

	    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='en-US'>
	    <voice name='en-us-andrew2:DragonHDLatestNeural'>text</voice> 
        <voice name='en-us-emma2:DragonHDLatestNeural'>text</voice>
        </speak>
"""


def document_to_podcast_script(document: str, title: str = "AI in Action") -> str:
    """Get LLM response."""

    if os.getenv("AZURE_OPENAI_KEY"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-09-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
    else:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-09-01-preview",
            azure_ad_token_provider=get_token_provider(),
        )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": PROMPT.format(title=title),
            },
            # Wrap the document in <documents> tag for Prompt Shield Indirect attacks
            # https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter?tabs=warning%2Cindirect%2Cpython-new#embedding-documents-in-your-prompt
            {
                "role": "user",
                "content": f"<documents>{document}</documents>",
            },
        ],
        model="gpt-4o",
        temperature=0.7,
    )

    message = chat_completion.choices[0].message.content

    return message


@st.cache_resource
def get_encoding():
    """Get TikToken."""
    encoding = tiktoken.encoding_for_model("gpt-4o")

    return encoding
