"""
Language configuration for JARVIS voice assistant
Comprehensive language and voice mapping with validation
"""

# Comprehensive language to voice mapping
LANGUAGE_VOICE_MAP = {
    # English variants
    "english": "en-GB-RyanNeural",
    "english male": "en-GB-RyanNeural",
    "english female": "en-GB-SoniaNeural",
    "english us": "en-US-AriaNeural",
    "english us male": "en-US-GuyNeural",
    "english us female": "en-US-AriaNeural",
    "english uk": "en-GB-RyanNeural",
    "english uk male": "en-GB-RyanNeural",
    "english uk female": "en-GB-SoniaNeural",
    
    # Hindi
    "hindi": "hi-IN-MadhurNeural",
    "hindi male": "hi-IN-MadhurNeural",
    "hindi female": "hi-IN-SwaraNeural",
    
    # French
    "french": "fr-FR-AlainNeural",
    "french male": "fr-FR-AlainNeural",
    "french female": "fr-FR-BrigitteNeural",
    
    # Spanish
    "spanish": "es-ES-AlvaroNeural",
    "spanish male": "es-ES-AlvaroNeural",
    "spanish female": "es-ES-ElviraNeural",
    
    # German
    "german": "de-DE-ConradNeural",
    "german male": "de-DE-ConradNeural",
    "german female": "de-DE-KatjaNeural",
    
    # Italian
    "italian": "it-IT-DiegoNeural",
    "italian male": "it-IT-DiegoNeural",
    "italian female": "it-IT-ElsaNeural",
    
    # Portuguese
    "portuguese": "pt-BR-AntonioNeural",
    "portuguese male": "pt-BR-AntonioNeural",
    "portuguese female": "pt-BR-FranciscaNeural",
    
    # Japanese
    "japanese": "ja-JP-KeitaNeural",
    "japanese male": "ja-JP-KeitaNeural",
    "japanese female": "ja-JP-NanamiNeural",
    
    # Korean
    "korean": "ko-KR-InJoonNeural",
    "korean male": "ko-KR-InJoonNeural",
    "korean female": "ko-KR-SunHiNeural",
    
    # Chinese
    "chinese": "zh-CN-XiaoxiaoNeural",
    "chinese male": "zh-CN-YunxiNeural",
    "chinese female": "zh-CN-XiaoxiaoNeural",
    
    # Russian
    "russian": "ru-RU-DmitryNeural",
    "russian male": "ru-RU-DmitryNeural",
    "russian female": "ru-RU-SvetlanaNeural",
    
    # Arabic
    "arabic": "ar-SA-HamedNeural",
    "arabic male": "ar-SA-HamedNeural",
    "arabic female": "ar-SA-ZariyahNeural",
}

# Language to code mapping for translation API
LANGUAGE_CODE_MAP = {
    "english": "en",
    "hindi": "hi",
    "french": "fr",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "japanese": "ja",
    "korean": "ko",
    "chinese": "zh",
    "russian": "ru",
    "arabic": "ar",
}

def get_supported_languages():
    """Return a list of all supported languages"""
    return list(LANGUAGE_VOICE_MAP.keys())

def validate_language(language):
    """Validate if a language is supported"""
    if not language:
        return False
    
    # Normalize the input
    language = language.strip().lower()
    
    # Check exact match
    if language in LANGUAGE_VOICE_MAP:
        return True
    
    # Check partial matches
    for supported_lang in LANGUAGE_VOICE_MAP.keys():
        if language in supported_lang or supported_lang in language:
            return True
    
    return False

def get_voice_for_language(language):
    """Get the voice for a given language"""
    if not language:
        return "en-GB-RyanNeural"  # Default
    
    language = language.strip().lower()
    
    # Try exact match first
    if language in LANGUAGE_VOICE_MAP:
        return LANGUAGE_VOICE_MAP[language]
    
    # Try partial match
    for supported_lang, voice in LANGUAGE_VOICE_MAP.items():
        if language in supported_lang:
            return voice
    
    return "en-GB-RyanNeural"  # Default fallback

def get_language_code(language):
    """Get the language code for translation API"""
    if not language:
        return "en"
    
    language = language.strip().lower()
    
    # Try exact match
    if language in LANGUAGE_CODE_MAP:
        return LANGUAGE_CODE_MAP[language]
    
    # Try partial match
    for supported_lang, code in LANGUAGE_CODE_MAP.items():
        if language in supported_lang:
            return code
    
    return "en"  # Default fallback

def get_language_suggestions():
    """Get helpful language suggestions for users"""
    return {
        "popular": ["english", "spanish", "french", "german", "hindi", "chinese"],
        "all": get_supported_languages(),
        "examples": [
            "change language to spanish",
            "change voice to french female",
            "switch to german",
            "set language to japanese"
        ]
    }
