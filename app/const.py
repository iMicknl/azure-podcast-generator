"""Constants for the app"""

import logging

LOGGER: logging.Logger = logging.getLogger(__name__)


# The new voices are currently not listed in the Voice List API or documentation.
# TODO: Retrieve voice list from tts.speech.microsoft.com/cognitiveservices/voices/list in the future
AZURE_HD_VOICES = {
    "de-DE-Seraphina": "de-DE-Seraphina:DragonHDLatestNeural",
    "en-US-Andrew": "en-US-Andrew:DragonHDLatestNeural",
    "en-US-Andrew2": "en-US-Andrew2:DragonHDLatestNeural",
    "en-US-Aria": "en-US-Aria:DragonHDLatestNeural",
    "en-US-Ava": "en-US-Ava:DragonHDLatestNeural",
    "en-US-Davis": "en-US-Davis:DragonHDLatestNeural",
    "en-US-Emma": "en-US-Emma:DragonHDLatestNeural",
    "en-US-Emma2": "en-US-Emma2:DragonHDLatestNeural",
    "en-US-Jenny": "en-US-Jenny:DragonHDLatestNeural",
    "en-US-Steffan": "en-US-Steffan:DragonHDLatestNeural",
    "ja-JP-Masaru": "ja-JP-Masaru:DragonHDLatestNeural",
    "zh-CN-Xiaochen": "zh-CN-Xiaochen:DragonHDLatestNeural",
}
