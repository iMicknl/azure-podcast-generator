from utils.speech import text_to_speech
import streamlit as st
from utils.llm import document_to_podcast_script
from utils.document import document_to_markdown
from dotenv import load_dotenv, find_dotenv
import logging
import tiktoken
import os

# TODO use managed identities

logger = logging.getLogger(__name__)

encoding = tiktoken.encoding_for_model("gpt-4o")

st.set_page_config(
    page_title="Azure Podcast Generator",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("🗣️ Podcast Generator")

st.write(
    "Generate an engaging podcast based on your document using Azure OpenAI and Azure Speech."
)

st.info("Generative AI is used to generate a podcast script, thus fabrication / hallucination may occur. Always check your podcast script for inconsistencies prior to publishing.", icon="ℹ️")


final_audio = None

# File upload
uploaded_file = st.file_uploader(
    "Upload your document",
    accept_multiple_files=False,
    type=["pdf", "docx", "png", "jpg", "jpeg", "txt", "md"],
)

if uploaded_file:
    bytes_data = uploaded_file.read()

    with st.status(
        "Processing document with Azure Document Intelligence...", expanded=False
    ) as status:
        logger.info(
            f"Processing document: {uploaded_file.name}, type: {uploaded_file.type}"
        )

        # Convert PDF to Markdown with Document Intelligence
        if uploaded_file.type in [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            document = document_to_markdown(bytes_data)

        logger.info(
            f"Processing document: {uploaded_file.name}, type: {uploaded_file.type}"
        )

        status.update(
            label="Analyzing document and generating podcast script with Azure OpenAI...",
            state="running",
            expanded=False,
        )

        num_tokens = len(encoding.encode(document))
        logger.info(f"Number of tokens: {num_tokens}")

        # Convert input document to podcast script
        podcast_script = document_to_podcast_script(document)

        # TODO Calculate approx max tokens based on token lenght

        status.update(
            label="Generate podcast using Azure Speech (HD voices)...",
            state="running",
            expanded=False,
        )

        # Convert podcast script to audio
        audio = text_to_speech(podcast_script)
        final_audio = True

        status.update(label="Finished", state="complete", expanded=False)

# Show audio player
if final_audio:
    st.audio(audio, format="audio/wav")

# TODO Calculate costs of end to end solution
# st.write("Total podcast costs: $0.00")

if __name__ == "__main__":
    load_dotenv(find_dotenv())

if os.getenv("RUNNING_IN_PRODUCTION") and os.getenv("DEBUG_MODE") != "true":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)
