import io
import os
import azure.cognitiveservices.speech as speechsdk
from typing import List
from pydub import AudioSegment
from const import AZURE_HD_VOICES
from azure.cognitiveservices.speech import SpeechConfig, AudioDataStream, ResultReason, SpeechSynthesizer, SpeechSynthesisOutputFormat
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from utils.identity import get_speech_token

def text_to_speech(ssml: str) -> bytes:
    """
    Call Azure Speech service to convert SSML to speech.
    Returns the audio as bytes.
    """
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
    # Use Neural voice
    speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    result = synthesizer.speak_ssml_async(ssml).get()
    if result.reason == ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        raise Exception(f"Speech synthesis canceled: {cancellation_details.error_details}")
    elif result.reason != ResultReason.SynthesizingAudioCompleted:
        raise Exception(f"Speech synthesis failed with reason: {result.reason}")

    return result.audio_data

def podcast_script_to_ssml(podcast: dict) -> str:
    """
    Convert the entire podcast script into SSML.
    We won't worry about the 50-voice limit here, just create a single SSML with all lines.
    We'll rely on the chunking logic later.
    """
    language = podcast["config"]["language"]
    script = podcast["script"]

    ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{language}'>"
    for line in script:
        speaker = line["name"]
        message = line["message"]
        voice_short_name = AZURE_HD_VOICES.get(speaker, AZURE_HD_VOICES["Andrew"])
        ssml += f"<voice name='{voice_short_name}'>{message}</voice>"
    ssml += "</speak>"
    return ssml

def podcast_script_to_ssml_chunks(podcast: dict) -> List[str]:
    """
    Convert the podcast script into multiple SSML chunks, each having <= 50 <voice> elements.
    This ensures we never exceed the Azure Speech limit.

    Steps:
    1. Extract all lines as voice elements.
    2. Batch them into chunks of up to 50.
    3. Wrap each batch into a <speak> tag.
    """

    language = podcast["config"]["language"]
    script = podcast["script"]

    # Create list of voice elements as strings
    voice_elements = []
    for line in script:
        speaker = line["name"]
        message = line["message"]
        voice_short_name = AZURE_HD_VOICES.get(speaker, AZURE_HD_VOICES["Andrew"])
        voice_elements.append(f"<voice name='{voice_short_name}'>{message}</voice>")

    # Chunk the voice elements into batches of <= 50
    chunks = []
    chunk_size = 50
    for i in range(0, len(voice_elements), chunk_size):
        batch = voice_elements[i:i+chunk_size]
        # Wrap batch in <speak> tag
        ssml_chunk = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{language}'>" + "".join(batch) + "</speak>"
        chunks.append(ssml_chunk)

    return chunks

def synthesize_in_chunks(podcast: dict) -> bytes:
    """
    Synthesize the podcast in chunks to avoid the 50 <voice> element limit.
    - Converts script to multiple SSML chunks.
    - Synthesizes each chunk separately.
    - Concatenates all audio segments into a single audio file.
    """
    ssml_chunks = podcast_script_to_ssml_chunks(podcast)

    # Synthesize each chunk and store in a list
    segments = []
    for chunk in ssml_chunks:
        audio_data = text_to_speech(chunk)
        # Load into pydub AudioSegment for concatenation
        segment = AudioSegment.from_wav(io.BytesIO(audio_data))
        segments.append(segment)

    # Concatenate all segments
    if len(segments) == 1:
        final_audio = segments[0]
    else:
        final_audio = segments[0]
        for seg in segments[1:]:
            final_audio += seg

    # Export concatenated audio to bytes
    out_buffer = io.BytesIO()
    final_audio.export(out_buffer, format="wav")
    out_buffer.seek(0)
    return out_buffer.read()
