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
from utils.llm import (
    PodcastStyle, 
    PodcastTone,
    document_to_podcast_script, 
    get_encoding,
    get_podcast_style_name,
    get_podcast_tone_name
)
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
    "Generate an engaging podcast based on your documents using Azure OpenAI and Azure Speech."
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
with form_container.expander("Podcast Settings", expanded=True):
    # Duration slider
    duration = st.slider(
        "Podcast Duration (minutes)",
        min_value=2,
        max_value=60,
        value=5,
        step=1,
        help="Select the target podcast duration in minutes."
    )
    
    # Podcast style selector
    col1, col2 = st.columns(2)
    
    style_options = list(PodcastStyle)
    podcast_style = col1.selectbox(
        "Podcast Style",
        options=style_options,
        format_func=get_podcast_style_name,
        index=4,  # Default to TED Talks style
        help="Select a predefined podcast format style."
    )
    
    # Podcast tone selector
    tone_options = list(PodcastTone)
    podcast_tone = col2.selectbox(
        "Podcast Tone",
        options=tone_options,
        format_func=get_podcast_tone_name,
        index=0,  # Default to Conversational tone
        help="Select the tone for your podcast."
    )
    
    # Content depth slider
    content_depth = st.slider(
        "Content Depth",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
        help="1: Overview with basic information, 3: Balanced content, 5: Deep technical dive with details"
    )

with form_container.expander("Voice Settings", expanded=False):
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

with form_container.expander("AI Generation Controls", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    # Temperature slider
    temperature = col1.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Control creativity: Lower values produce more predictable output, higher values produce more varied output."
    )
    
    # Max tokens slider
    max_tokens = col2.slider(
        "Max Tokens",
        min_value=1000,
        max_value=32000,
        value=8000,
        step=500,
        help="Select the maximum number of tokens to be used for generating the podcast script. Adjust this according to your OpenAI quota.",
    )
    
    # Show generation steps checkbox
    show_steps = col3.checkbox(
        "Show Generation Steps",
        value=True,
        help="Show the ReAct generation steps in the UI"
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
        "Processing document with Azure Document Intelligence...", expanded=True
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
            expanded=True,
        )

        num_tokens = len(get_encoding().encode(document_response.markdown))
        LOGGER.info(f"Generating podcast script. Document tokens: {num_tokens}")

        # Convert input document to podcast script with the new customization options
        podcast_response = document_to_podcast_script(
            document=document_response.markdown,
            title=podcast_title,
            voice_1=voice_1,
            voice_2=voice_2,
            max_tokens=max_tokens,
            duration=duration,
            podcast_style=podcast_style,
            podcast_tone=podcast_tone,
            content_depth=content_depth,
            temperature=temperature,
            show_steps=show_steps,
        )

        podcast_script = podcast_response.podcast["script"]
        
        status.update(
            label="Generating podcast using Azure AI Speech...",
            state="running",
            expanded=True,
        )

        # Convert podcast script to audio
        ssml = podcast_script_to_ssml(podcast_response.podcast)
        audio = text_to_speech(ssml)

        status.update(
            label="Calculating Azure costs...",
            state="running",
            expanded=True,
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

    # Create four tabs (added ReAct Process tab)
    audio_tab, transcript_tab, react_tab, costs_tab = st.tabs(["Audio", "Transcript", "ReAct Process", "Costs"])

    with audio_tab:
        st.audio(audio, format="audio/wav")

    with transcript_tab:
        # Display podcast configuration details
        st.subheader("Podcast Configuration")
        col1, col2, col3 = st.columns(3)
        col1.metric("Duration Target", f"{duration} minutes")
        col2.metric("Style", get_podcast_style_name(podcast_style))
        col3.metric("Tone", get_podcast_tone_name(podcast_tone))
        
        st.subheader("Transcript")
        podcast_script = podcast_response.podcast["script"]
        for item in podcast_script:
            st.markdown(f"**{item['name']}**: {item['message']}")

    with react_tab:
        st.subheader("ReAct Generation Process")
        
        # Display each generation step in an expander
        for step in podcast_response.generation_steps:
            with st.expander(f"{step['step']}", expanded=False):
                st.markdown("### Reasoning")
                st.markdown(step["reasoning"])
                
                st.markdown("### Action")
                if step["action"]:
                    # Format JSON data nicely
                    st.json(step["action"])
                else:
                    st.info("No action data available for this step")

    with costs_tab:
        st.markdown(
            f"**Azure Document Intelligence**: ${azure_document_intelligence_costs:.2f}"
        )
        st.markdown(f"**Azure OpenAI Service**: ${azure_openai_costs:.2f}")
        st.markdown(f"**Azure AI Speech**: ${azure_ai_speech_costs:.2f}")
        st.markdown(
            f"**Total costs**: ${(azure_ai_speech_costs + azure_openai_costs + azure_document_intelligence_costs):.2f}"
        )
        
        # Token usage breakdown
        st.subheader("Token Usage")
        col1, col2, col3 = st.columns(3)
        col1.metric("Prompt Tokens", f"{podcast_response.usage.prompt_tokens:,}")
        col2.metric("Completion Tokens", f"{podcast_response.usage.completion_tokens:,}")
        col3.metric("Total Tokens", f"{podcast_response.usage.total_tokens:,}")

# Footer
st.divider()
st.caption(
    "Created by [Mick Vleeshouwer](https://github.com/imicknl). The source code is available on [GitHub](https://github.com/iMicknl/azure-podcast-generator), contributions are welcome."
)

if __name__ == "__main__":
    load_dotenv(find_dotenv())

if os.getenv("DEBUG_MODE") == "true":
    logging.basicConfig(level=logging.INFO)