"""Streamlit app for Azure Podcast Generator"""

import logging
import os

import streamlit as st
from const import AZURE_HD_VOICES, LOGGER
from dotenv import find_dotenv, load_dotenv
from utils.cost import (
    calculate_azure_ai_speech_costs,
    calculate_azure_document_intelligence_costs,
    calculate_azure_openai_costs,
)
from utils.document import DocumentResponse, document_to_markdown
from utils.llm import document_to_podcast_script, get_encoding
from utils.speech import podcast_script_to_ssml, text_to_speech

st.set_page_config(
    page_title="Azure Podcast Generator",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("🗣️ Podcast Generator")

st.write(
    "Generate an engaging ~2 minute podcast based on your documents (e.g. scientific papers from arXiv) using Azure OpenAI and Azure Speech."
)

st.info(
    "Generative AI may produce inaccuracies in podcast scripts. Always review for inconsistencies before publishing.",
    icon="ℹ️",
)

final_audio = None

# Podcast title input
podcast_title = st.text_input("Podcast Title", value="AI in Action")

# File upload
uploaded_file = st.file_uploader(
    "Upload your document",
    accept_multiple_files=False,
    type=["pdf", "docx", "pptx", "txt", "md"],
)

# Advanced Settings popover
with st.expander("Advanced options", expanded=False):
    col1, col2 = st.columns(2)

    # Voice 1 select box
    voice_1 = col1.selectbox(
        "Voice 1",
        options=list(AZURE_HD_VOICES.keys()),
        index=0,
        key="voice_1",
    )

    # Voice 2 select box
    voice_2 = col2.selectbox(
        "Voice 2",
        options=list(AZURE_HD_VOICES.keys()),
        index=4,
        key="voice_2",
    )

    # col3, col4 = st.columns(2)

    # # Tone select slider
    # tone = col3.select_slider(
    #     "Tone",
    #     options=["Formal", "Neutral", "Informal"],
    #     value="Neutral",
    # )

    # # Length select box
    # length = col4.select_slider(
    #     "Length",
    #     options=["Short (~1 min)", "Medium (~2 min)", "Long (~3 min)"],
    #     value="Medium (~2 min)",
    # )

# Submit button
generate_podcast = st.button(
    "Generate Podcast", type="primary", disabled=not uploaded_file
)

if generate_podcast:
    st.session_state["generate_podcast_disabled"] = True
else:
    st.session_state["generate_podcast_disabled"] = False

if uploaded_file and generate_podcast:
    bytes_data = uploaded_file.read()

    with st.status(
        "Processing document with Azure Document Intelligence...", expanded=False
    ) as status:
        LOGGER.info(
            f"Processing document: {uploaded_file.name}, type: {uploaded_file.type}"
        )

        # Convert PDF/image/Word files to Markdown with Document Intelligence
        if uploaded_file.type in [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]:
            document_response = document_to_markdown(bytes_data)
        else:
            document_response = DocumentResponse(
                markdown=bytes_data.decode("utf-8"), pages=0
            )

        LOGGER.info(
            f"Processing document: {uploaded_file.name}, type: {uploaded_file.type}"
        )

        status.update(
            label="Analyzing document and generating podcast script with Azure OpenAI...",
            state="running",
            expanded=False,
        )

        num_tokens = len(get_encoding().encode(document_response.markdown))
        LOGGER.info(f"Number of document tokens: {num_tokens}")

        # Convert input document to podcast script
        podcast_response = document_to_podcast_script(
            document=document_response.markdown,
            title=podcast_title,
            voice_1=voice_1,
            voice_2=voice_2,
        )

        st.markdown("### Podcast script:")
        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['name']}**: {item['message']}")

        status.update(
            label="Generate podcast using Azure Speech (HD voices)...",
            state="running",
            expanded=False,
        )

        # Convert podcast script to audio
        ssml = podcast_script_to_ssml(podcast_response.podcast)
        audio = text_to_speech(ssml)

        status.update(
            label="Calculate Azure costs...",
            state="running",
            expanded=False,
        )

        # Calculate costs
        azure_document_intelligence_costs = calculate_azure_document_intelligence_costs(
            pages=document_response.pages
        )
        azure_openai_costs = calculate_azure_openai_costs(
            input_tokens=podcast_response.usage.prompt_tokens,
            output_tokens=podcast_response.usage.completion_tokens,
        )

        azure_ai_speech_costs = calculate_azure_ai_speech_costs(
            characters=sum(len(item["message"]) for item in podcast_script)
        )

        st.markdown("### Costs")
        st.markdown(
            f"**Azure: Document Intelligence**: ${azure_document_intelligence_costs:.2f}"
        )
        st.markdown(f"**Azure OpenAI Service**: ${azure_openai_costs:.2f}")
        st.markdown(f"**Azure AI Speech**: ${azure_ai_speech_costs:.2f}")
        st.markdown(
            f"**Total costs**: ${(azure_ai_speech_costs + azure_openai_costs + azure_document_intelligence_costs):.2f}"
        )

        final_audio = True
        status.update(label="Finished", state="complete", expanded=False)

# Display audio player after generation
if final_audio:
    st.audio(audio, format="audio/wav")


# Footer
st.divider()
st.caption(
    "Created by [Mick Vleeshouwer](https://github.com/imicknl). The source code is available on [GitHub](https://github.com/iMicknl/azure-podcast-generator), contributions are welcome."
)

if __name__ == "__main__":
    load_dotenv(find_dotenv())

if os.getenv("RUNNING_IN_PRODUCTION") and os.getenv("DEBUG_MODE") != "true":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)
