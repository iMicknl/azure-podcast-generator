"""Basic speech provider implementation with simple SSML support."""

import os

import azure.cognitiveservices.speech as speechsdk
from const import LOGGER
from providers.speech.base import SpeechProvider, SpeechResponse
from utils.identity import get_speech_token


class AzureSpeechMultitalker(SpeechProvider):
    """AzureSpeechMultitalker provider for text-to-speech conversion with multitalker support."""

    name = "Azure Speech (MultiTalker Voice)"
    description = "Use Azure's innovative MultiTalker voices for natural, dynamic conversations with emotional consistency."

    cost: float = 0.0

    def __init__(self, **kwargs):
        """Initialize the Azure Speech provider."""
        self.speech_key = os.environ.get("AZURE_SPEECH_KEY")
        self.speech_region = os.environ.get("AZURE_SPEECH_REGION")
        self.speech_resource_id = os.environ.get("AZURE_SPEECH_RESOURCE_ID")
        self.output_format = speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm

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
        """Convert podcast script to multitalker SSML.

        Args:
            podcast: The podcast script data

        Returns:
            SSML string for speech synthesis with multitalker support
        """
        podcast_script = podcast["script"]
        language = podcast.get("config", {}).get("language", "en-US")
        character_count = 0

        # Start with the SSML header and multitalker-specific namespace
        ssml = '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        ssml += 'xmlns:mstts="https://www.w3.org/2001/mstts" '
        ssml += f'xml:lang="{language}">'

        # Create the voice wrapper for the entire dialog
        ssml += '<voice name="en-US-MultiTalker-Ava-Andrew:DragonHDLatestNeural">'
        ssml += "<mstts:dialog>"

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

            # Convert speaker name to lowercase for the turn attribute
            speaker = "andrew" if line["speaker"] == "speaker_1" else "ava"
            ssml += f'<mstts:turn speaker="{speaker}">{message}</mstts:turn>'
            character_count += len(message)

        # Close all tags
        ssml += "</mstts:dialog></voice></speak>"

        self.cost = 30 * (character_count / 1_000_000)

        return ssml
