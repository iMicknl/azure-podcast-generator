"""Streamlit app for Azure Podcast Generator"""

import logging
import os
import xml.dom.minidom

import streamlit as st
from const import LOGGER
from dotenv import find_dotenv, load_dotenv
from profiles import PROFILES
from utils.identity import check_claim_for_tenant
from utils.llm import get_encoding

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

# Profile selection
selected_profile_name = form_container.selectbox(
    "Profile",
    options=list(PROFILES.keys()),
    index=0,
    help="Select a profile to use different combinations of document processing, LLM, and speech providers",
)

# Get the selected profile and create provider instances
profile = PROFILES[selected_profile_name]
providers = profile.create_providers()

# Podcast title input
podcast_title = form_container.text_input("Podcast Title", value="AI in Action")

# File upload
uploaded_file = form_container.file_uploader(
    "Upload your document",
    accept_multiple_files=False,
    type=["pdf", "doc", "docx", "ppt", "pptx", "txt", "md"],
)

# Advanced options expander
provider_options = {}
with form_container.expander("Advanced options", expanded=False):
    # Get configurable options from each provider
    for provider_name, provider_class in profile.get_provider_classes().items():
        provider_options[provider_name] = provider_class.render_options_ui(st)

# Submit button
generate_podcast = form_container.button(
    "Generate Podcast", type="primary", disabled=not uploaded_file
)

if uploaded_file and generate_podcast:
    bytes_data = uploaded_file.read()
    form.empty()

    # Create provider instances with the UI-configured options
    providers = profile.create_providers(**provider_options)

    status_container = st.empty()
    with status_container.status(
        f"Processing document with {profile.document_provider.__name__}...",
        expanded=False,
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
            document_response = providers["document"].document_to_markdown(bytes_data)
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            st.stop()

        status.update(
            label=f"Analyzing document and generating podcast script with {profile.llm_provider.__name__}...",
            state="running",
            expanded=False,
        )

        num_tokens = len(get_encoding().encode(document_response.markdown))
        LOGGER.info(f"Generating podcast script. Document tokens: {num_tokens}")

        # Convert input document to podcast script
        podcast_response = providers["llm"].document_to_podcast_script(
            document=document_response.markdown, title=podcast_title
        )

        podcast_script = podcast_response.podcast["script"]

        status.update(
            label=f"Generating podcast using {profile.speech_provider.__name__}...",
            state="running",
            expanded=False,
        )

        # Convert podcast script to audio
        ssml = providers["speech"].podcast_script_to_ssml(podcast_response.podcast)
        speech_response = providers["speech"].text_to_speech(ssml)

        status.update(
            label="Calculating costs...",
            state="running",
            expanded=False,
        )

        # Get costs from provider responses
        total_cost = (
            document_response.cost + podcast_response.cost + speech_response.cost
        )

        status.update(label="Finished", state="complete", expanded=False)
        final_audio = True


# Display audio player after generation
if final_audio:
    status_container.empty()

    # Create four tabs
    audio_tab, transcript_tab, ssml_tab, costs_tab = st.tabs(
        ["Audio", "Transcript", "SSML", "Costs"]
    )

    with audio_tab:
        st.audio(speech_response.audio, format="audio/wav")

    with transcript_tab:
        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['speaker']}**: {item['message']}")

    with ssml_tab:
        # Pretty print the XML/SSML for better readability
        pretty_ssml = xml.dom.minidom.parseString(ssml).toprettyxml(indent="  ")
        st.code(pretty_ssml, language="xml")

    with costs_tab:
        st.markdown(f"**Document Processing**: ${document_response.cost:.2f}")
        st.markdown(f"**LLM Processing**: ${podcast_response.cost:.2f}")
        st.markdown(f"**Speech Synthesis**: ${speech_response.cost:.2f}")
        st.markdown(f"**Total costs**: ${total_cost:.2f}")

# Footer
st.divider()
st.caption(
    "Created by [Mick Vleeshouwer](https://github.com/imicknl). The source code is available on [GitHub](https://github.com/iMicknl/azure-podcast-generator), contributions are welcome."
)

if __name__ == "__main__":
    load_dotenv(find_dotenv())

if os.getenv("DEBUG_MODE") == "true":
    logging.basicConfig(level=logging.INFO)
