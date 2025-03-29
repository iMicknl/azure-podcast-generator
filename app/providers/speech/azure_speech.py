"""Azure Speech provider implementation."""

import os

import azure.cognitiveservices.speech as speechsdk
from const import AZURE_HD_VOICES, LOGGER
from providers.speech.base import SpeechProvider
from utils.identity import get_speech_token


class AzureSpeechProvider(SpeechProvider):
    """Azure Speech provider for text-to-speech conversion."""

    def __init__(self, **kwargs):
        """Initialize the Azure Speech provider."""
        self.speech_key = kwargs.get("speech_key", os.environ.get("AZURE_SPEECH_KEY"))
        self.speech_region = kwargs.get(
            "speech_region", os.environ.get("AZURE_SPEECH_REGION")
        )
        self.speech_resource_id = kwargs.get(
            "speech_resource_id", os.environ.get("AZURE_SPEECH_RESOURCE_ID")
        )
        self.voices = kwargs.get("voices", AZURE_HD_VOICES)
        self.output_format = kwargs.get(
            "output_format",
            speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
        )

    def text_to_speech(self, ssml: str) -> bytes:
        """Convert SSML to audio using Azure Speech Service.

        Args:
            ssml: The SSML text to convert to speech

        Returns:
            bytes of audio data
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
        result = speech_synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data

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
            ssml += f"<voice name='{self.voices[line['name']]}'>{message}</voice>"

        ssml += "</speak>"

        return ssml
