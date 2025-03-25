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
from utils.identity import check_claim_for_tenant
from utils.llm import document_to_podcast_script, get_encoding
from utils.speech import podcast_script_to_ssml, text_to_speech

# optional: only allow specific tenants to access the app (using Azure Entra ID)
headers = st.context.headers
if os.getenv("ENTRA_AUTHORIZED_TENANTS") and headers.get("X-Ms-Client-Principal"):
    authorized_tenants = os.environ["ENTRA_AUTHORIZED_TENANTS"].split(",")
    ms_client_principal = headers.get("X-Ms-Client-Principal")
    access = check_claim_for_tenant(ms_client_principal, authorized_tenants)

    if access is not True:
        st.error("Access denied.")
        st.stop()


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
form = st.empty()
form_container = form.container()

# Podcast title input
podcast_title = form_container.text_input("Podcast Title", value="AI in Action")

# File upload
uploaded_file = form_container.file_uploader(
    "Upload your document",
    accept_multiple_files=False,
    type=["pdf", "doc", "docx", "ppt", "pptx", "txt", "md"],
)

# Advanced options expander
with form_container.expander("Advanced options", expanded=False):
    col1, col2 = st.columns(2)

    # Voice 1 select box
    voice_1 = col1.selectbox(
        "Voice 1",
        options=list(AZURE_HD_VOICES.keys()),
        index=list(AZURE_HD_VOICES.keys()).index("Andrew")
        if "Andrew" in AZURE_HD_VOICES
        else 0,
    )

    # Voice 2 select box
    voice_2 = col2.selectbox(
        "Voice 2",
        options=list(AZURE_HD_VOICES.keys()),
        index=list(AZURE_HD_VOICES.keys()).index("Ava")
        if "Ava" in AZURE_HD_VOICES
        else 1,
    )

    # Max tokens slider
    max_tokens = st.slider(
        "Max Tokens",
        min_value=1000,
        max_value=32000,
        value=8000,
        step=500,
        help="Select the maximum number of tokens to be used for generating the podcast script. Adjust this according to your OpenAI quota.",
    )
# Submit button
generate_podcast = form_container.button(
    "Generate Podcast", type="primary", disabled=not uploaded_file
)

if uploaded_file and generate_podcast:
    bytes_data = uploaded_file.read()
    form.empty()

    status_container = st.empty()
    with status_container.status(
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
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]:
            document_response = document_to_markdown(bytes_data)
        else:
            document_response = DocumentResponse(
                markdown=bytes_data.decode("utf-8"), pages=0
            )

        status.update(
            label="Analyzing document and generating podcast script with Azure OpenAI...",
            state="running",
            expanded=False,
        )

        num_tokens = len(get_encoding().encode(document_response.markdown))
        LOGGER.info(f"Generating podcast script. Document tokens: {num_tokens}")

        # Convert input document to podcast script
        podcast_response = document_to_podcast_script(
            document=document_response.markdown,
            title=podcast_title,
            voice_1=voice_1,
            voice_2=voice_2,
            max_tokens=max_tokens,
        )

        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['name']}**: {item['message']}")

        status.update(
            label="Generating podcast using Azure Speech (HD voices)...",
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

        status.update(label="Finished", state="complete", expanded=False)
        final_audio = True


# Display audio player after generation
if final_audio:
    status_container.empty()

    # Create three tabs
    audio_tab, transcript_tab, costs_tab = st.tabs(["Audio", "Transcript", "Costs"])

    with audio_tab:
        st.audio(audio, format="audio/wav")

    with transcript_tab:
        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['name']}**: {item['message']}")

    with costs_tab:
        st.markdown(
            f"**Azure: Document Intelligence**: ${azure_document_intelligence_costs:.2f}"
        )
        st.markdown(f"**Azure OpenAI Service**: ${azure_openai_costs:.2f}")
        st.markdown(f"**Azure AI Speech**: ${azure_ai_speech_costs:.2f}")
        st.markdown(
            f"**Total costs**: ${(azure_ai_speech_costs + azure_openai_costs + azure_document_intelligence_costs):.2f}"
        )

# Footer
st.divider()
st.caption(
    "Created by [Mick Vleeshouwer](https://github.com/imicknl). The source code is available on [GitHub](https://github.com/iMicknl/azure-podcast-generator), contributions are welcome."
)

if __name__ == "__main__":
    load_dotenv(find_dotenv())

if os.getenv("DEBUG_MODE") == "true":
    logging.basicConfig(level=logging.INFO)
