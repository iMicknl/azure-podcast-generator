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
from utils.llm import (
    document_to_podcast_script,
    document_to_podcast_script_iterative,
    get_encoding,
)
from utils.speech import podcast_script_to_ssml, text_to_speech
from utils.speech import synthesize_in_chunks


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
    "Generate an engaging podcast based on your documents (e.g. scientific papers from arXiv) using Azure OpenAI and Azure Speech."
)

st.info(
    "Generative AI may produce inaccuracies. Review for inconsistencies before publishing.",
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

# Podcast length selection
podcast_duration = form_container.selectbox(
    "Podcast Duration",
    options=["Short (2-3 min)", "Medium (10-15 min)", "Long (20-30 min)"],
    index=0,
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
        index=list(AZURE_HD_VOICES.keys()).index("Emma")
        if "Emma" in AZURE_HD_VOICES
        else 1,
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

        # Convert file to Markdown
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

        # Decide approach based on duration
        duration_choice = podcast_duration.split()[0].lower()  # short, medium, long
        if duration_choice == "short":
            podcast_response = document_to_podcast_script(
                document=document_response.markdown,
                title=podcast_title,
                voice_1=voice_1,
                voice_2=voice_2,
            )
        else:
            # Use iterative approach for medium / long
            podcast_response = document_to_podcast_script_iterative(
                document=document_response.markdown,
                title=podcast_title,
                voice_1=voice_1,
                voice_2=voice_2,
                duration=duration_choice,
            )

        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['name']}**: {item['message']}")

        status.update(
            label="Generating podcast audio using Azure Speech (HD voices)...",
            state="running",
            expanded=False,
        )

        #ssml = podcast_script_to_ssml(podcast_response.podcast)
        audio = synthesize_in_chunks(podcast_response.podcast)

        status.update(
            label="Calculating Azure costs...",
            state="running",
            expanded=False,
        )

        # Costs
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

if final_audio:
    status_container.empty()

    # Tabs
    if final_audio:
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

st.divider()
st.caption(
    "Created by [Mick Vleeshouwer](https://github.com/imicknl). Source on [GitHub](https://github.com/iMicknl/azure-podcast-generator)."
)

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    print(os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT"))

if os.getenv("DEBUG_MODE") == "true":
    logging.basicConfig(level=logging.INFO)
