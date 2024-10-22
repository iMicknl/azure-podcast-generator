"""Constants for the app"""

import logging

LOGGER: logging.Logger = logging.getLogger(__name__)


# The new voices are currently not listed in the Voice List API or documentation.
# Will retrieve voice list from tts.speech.microsoft.com/cognitiveservices/voices/list in the future
# TODO: Split voices by language
AZURE_HD_VOICES = {
    # "de-DE-Seraphina": "de-DE-Seraphina:DragonHDLatestNeural",
    # "en-US-Andrew": "en-US-Andrew:DragonHDLatestNeural",
    "Andrew": "en-US-Andrew2:DragonHDLatestNeural",
    "Aria": "en-US-Aria:DragonHDLatestNeural",
    "Ava": "en-US-Ava:DragonHDLatestNeural",
    "Brian": "en-US-Brian:DragonHDLatestNeural",
    "Davis": "en-US-Davis:DragonHDLatestNeural",
    # "Emma": "en-US-Emma:DragonHDLatestNeural",
    "Emma": "en-US-Emma2:DragonHDLatestNeural",
    "Jenny": "en-US-Jenny:DragonHDLatestNeural",
    "Steffan": "en-US-Steffan:DragonHDLatestNeural",
    # "ja-JP-Masaru": "ja-JP-Masaru:DragonHDLatestNeural",
    # "zh-CN-Xiaochen": "zh-CN-Xiaochen:DragonHDLatestNeural",
}
