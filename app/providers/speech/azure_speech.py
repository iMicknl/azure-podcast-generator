"""Azure Speech provider implementation."""

import os
from typing import Any

import azure.cognitiveservices.speech as speechsdk
import streamlit
from const import LOGGER
from providers.speech.base import SpeechProvider, SpeechResponse
from utils.identity import get_speech_token

# The new voices are currently not listed in the Voice List API or documentation.
# Will retrieve voice list from tts.speech.microsoft.com/cognitiveservices/voices/list in the future
# TODO: Split voices by language
AZURE_HD_VOICES = {
    "Alloy": "en-US-Alloy:DragonHDLatestNeural",
    "Adam": "en-US-Adam:DragonHDLatestNeural",
    "Andrew": "en-US-Andrew3:DragonHDLatestNeural",
    "Aria": "en-US-Aria:DragonHDLatestNeural",
    "Ava": "en-US-Ava3:DragonHDLatestNeural",
    "Brian": "en-US-Brian:DragonHDLatestNeural",
    "Davis": "en-US-Davis:DragonHDLatestNeural",
    "Emma": "en-US-Emma2:DragonHDLatestNeural",
    "Jenny": "en-US-Jenny:DragonHDLatestNeural",
    "Nova": "en-US-Nova:DragonHDLatestNeural",
    "Phoebe": "en-US-Phoebe:DragonHDLatestNeural",
    "Serena": "en-US-Serena:DragonHDLatestNeural",
    "Steffan": "en-US-Steffan:DragonHDLatestNeural",
    # "Ava-Andrew": "en-US-MultiTalker-Ava-Andrew:DragonHDLatestNeural",
    # "ja-JP-Masaru": "ja-JP-Masaru:DragonHDLatestNeural",
    # "zh-CN-Xiaochen": "zh-CN-Xiaochen:DragonHDLatestNeural",
    # "de-DE-Florian": "de-DE-Florian:DragonHDLatestNeural",
    # "de-DE-Seraphina": "de-DE-Seraphina:DragonHDLatestNeural",
    # "es-ES-Ximena": "es-ES-Ximena:DragonHDLatestNeural",
    # "es-ES-Tristan": "es-ES-Tristan:DragonHDLatestNeural",
    # "fr-FR-Vivienne": "fr-FR-Vivienne:DragonHDLatestNeural",
    # "fr-FR-Remy": "fr-FR-Remy:DragonHDLatestNeural",
    # "ja-JP-Nanami": "ja-JP-Nanami:DragonHDLatestNeural",
    # "zh-CN-Yunfan": "zh-CN-Yunfan:DragonHDLatestNeural",
}


class AzureSpeechProvider(SpeechProvider):
    """Azure Speech provider for text-to-speech conversion."""

    cost: float = 0.0

    def __init__(self, **kwargs):
        """Initialize the Azure Speech provider."""
        self.speech_key = os.environ.get("AZURE_SPEECH_KEY")
        self.speech_region = os.environ.get("AZURE_SPEECH_REGION")
        self.speech_resource_id = os.environ.get("AZURE_SPEECH_RESOURCE_ID")
        self.voices = kwargs.get("voices", AZURE_HD_VOICES)
        self.voice_1 = kwargs.get("voice_1", "Andrew")
        self.voice_2 = kwargs.get("voice_2", "Ava")
        self.output_format = speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm

    @classmethod
    def render_options_ui(cls, st: streamlit) -> dict[str, Any]:
        """Render Azure Speech specific options using Streamlit widgets."""
        st.markdown("##### Speech")

        options = {}
        col1, col2 = st.columns(2)

        with col1:
            options["voice_1"] = st.selectbox(
                "Voice 1",
                options=list(AZURE_HD_VOICES.keys()),
                index=list(AZURE_HD_VOICES.keys()).index("Andrew"),
                help="The first voice used in the podcast",
            )

        with col2:
            options["voice_2"] = st.selectbox(
                "Voice 2",
                options=list(AZURE_HD_VOICES.keys()),
                index=list(AZURE_HD_VOICES.keys()).index("Ava"),
                help="The second voice used in the podcast",
            )

        return options

    def text_to_speech(self, ssml: str) -> SpeechResponse:
        """Convert SSML to audio using Azure Speech Service.

        Args:
            ssml: The SSML text to convert to speech

        Returns:
            SpeechResponse containing audio data and cost
        """
        if self.speech_key:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region,
            )
        else:
            speech_config = speechsdk.SpeechConfig(
                auth_token=get_speech_token(self.speech_resource_id),
                region=self.speech_region,
            )

        audio_config = None  # enable in-memory audio stream

        speech_config.set_speech_synthesis_output_format(self.output_format)

        # Creates a speech synthesizer using the Azure Speech Service
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Synthesizes the received text to speech
        result = speech_synthesizer.speak_ssml(ssml)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return SpeechResponse(audio=result.audio_data, cost=self.cost)

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            LOGGER.warning(f"Speech synthesis canceled: {cancellation_details.reason}")

            if (
                cancellation_details.reason == speechsdk.CancellationReason.Error
                and cancellation_details.error_details
            ):
                LOGGER.error(f"Error details: {cancellation_details.error_details}")

            raise Exception(f"Error details: {cancellation_details.error_details}")

        raise Exception(f"Unknown exit reason: {result.reason}")

    def podcast_script_to_ssml(self, podcast: dict) -> str:
        """Convert podcast script to SSML for Azure Speech Service.

        Args:
            podcast: The podcast script data

        Returns:
            SSML string for speech synthesis
        """
        podcast_script = podcast["script"]
        language = podcast.get("config", {}).get("language", "en-US")
        ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{language}'>"
        character_count = 0

        for line in podcast_script:
            # Escape SSML special characters
            message = (
                line["message"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
            )

            # Map speakers to the configured voices
            voice = self.voice_1 if line["speaker"] == "speaker_1" else self.voice_2
            ssml += f"<voice name='{self.voices[voice]}'>{message}</voice>"
            character_count += len(message)

        ssml += "</speak>"

        self.cost = 30 * (character_count / 1_000_000)

        return ssml
