"""Constants for the app"""

import logging

LOGGER: logging.Logger = logging.getLogger(__name__)


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
