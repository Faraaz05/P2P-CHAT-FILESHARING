from deep_translator import GoogleTranslator, MyMemoryTranslator, LingueeTranslator
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

def translate_text(text, target_language, source_language=None):
    """
    Translate text using deep-translator with fallback mechanisms
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (e.g., 'en', 'hi')
        source_language (str, optional): Source language code. Defaults to 'auto'.
    
    Returns:
        str: Translated text or original text if translation fails
    """
    if not text or not target_language:
        return text
    
    # If target and source languages are the same, no need to translate
    if source_language and source_language == target_language:
        return text
    
    # Create cache key from text and target language
    cache_key = f"translation_{hash(text)}_{target_language}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return cached_result
    
    # If we're in DEBUG mode and want to use mock translations for development
    if getattr(settings, 'DEBUG', False) and getattr(settings, 'USE_MOCK_TRANSLATION', False):
        translation = f"[{target_language}] {text}"
        cache.set(cache_key, translation, 3600)
        return translation
    
    # Try translation with multiple providers for redundancy
    translation = None
    exceptions = []
    
    # Try Google Translator (faster and most reliable)
    if not translation:
        try:
            # Use 'auto' if source_language is None
            src_lang = source_language if source_language else 'auto'
            translator = GoogleTranslator(source=src_lang, target=target_language)
            translation = translator.translate(text)
        except Exception as e:
            exceptions.append(f"Google Translator error: {e}")
    
    # Fallback to MyMemory translator if Google fails
    if not translation:
        try:
            # MyMemory requires explicit source language
            src_lang = source_language if source_language else 'en'  # Default to English if auto-detect needed
            translator = MyMemoryTranslator(source=src_lang, target=target_language)
            translation = translator.translate(text)
        except Exception as e:
            exceptions.append(f"MyMemory Translator error: {e}")
    
    # Final fallback to Linguee for common European languages
    if not translation and len(text.split()) < 5:  # Linguee works best with short phrases
        try:
            # Linguee doesn't support 'auto' detection and has limited language pairs
            supported_langs = ['en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'ru']
            if (source_language in supported_langs and target_language in supported_langs):
                translator = LingueeTranslator(source=source_language, target=target_language)
                translation = translator.translate(text)
        except Exception as e:
            exceptions.append(f"Linguee Translator error: {e}")
    
    # If all translators failed, log errors and return original text
    if not translation:
        for exception in exceptions:
            logger.error(exception)
        return text
    
    # Cache successful translation for future use (1 hour expiry)
    cache.set(cache_key, translation, 3600)
    
    return translation