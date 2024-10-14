"""Module for audio utils."""

import os

import azure.cognitiveservices.speech as speechsdk
from utils.identity import get_speech_token


def text_to_speech(ssml) -> bytes:
    """Use Azure Speech Service and convert SSML to audio bytes."""

    if os.getenv("AZURE_SPEECH_KEY"):
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_KEY"],
            region=os.environ["AZURE_SPEECH_REGION"],
        )
    else:
        speech_config = speechsdk.SpeechConfig(
            auth_token=get_speech_token(os.environ["AZURE_SPEECH_RESOURCE_ID"]),
            region=os.environ["AZURE_SPEECH_REGION"],
        )

    audio_config = None  # enable in-memory audio stream

    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm
    )

    # Creates a speech synthesizer using the Azure Speech Service.
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    # Synthesizes the received text to speech.
    result = speech_synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if (
            cancellation_details.reason == speechsdk.CancellationReason.Error
            and cancellation_details.error_details
        ):
            print(f"Error details: {cancellation_details.error_details}")

        raise Exception(f"Error details: {cancellation_details.error_details}")

    raise Exception(f"Unknown exit reason: {result.reason}")
