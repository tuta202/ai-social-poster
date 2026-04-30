"""
Factory functions — read env config and return correct provider instances.
Providers are cached as module-level singletons after first init.
"""
import logging
from typing import Optional
from app.core.config import settings
from app.services.ai.base import TextProvider, ImageProvider

logger = logging.getLogger(__name__)

_text_provider: Optional[TextProvider] = None
_image_provider: Optional[ImageProvider] = None


def get_text_provider() -> TextProvider:
    """Return singleton TextProvider based on AI_TEXT_PROVIDER env var."""
    global _text_provider
    if _text_provider is not None:
        return _text_provider

    provider_name = settings.AI_TEXT_PROVIDER.lower()
    logger.info(f"Initializing text provider: {provider_name}")

    if provider_name == "openai":
        from app.services.ai.openai_provider import OpenAITextProvider
        _text_provider = OpenAITextProvider(api_key=settings.OPENAI_API_KEY)

    elif provider_name == "gemini":
        from app.services.ai.gemini_provider import GeminiTextProvider
        _text_provider = GeminiTextProvider(api_key=settings.GEMINI_API_KEY)

    else:
        raise ValueError(
            f"Unknown AI_TEXT_PROVIDER: '{provider_name}'. "
            f"Supported: 'openai', 'gemini'"
        )

    logger.info(f"Text provider ready: {provider_name} / {settings.AI_TEXT_MODEL}")
    return _text_provider


def get_image_provider() -> ImageProvider:
    """Return singleton ImageProvider based on AI_IMAGE_PROVIDER env var."""
    global _image_provider
    if _image_provider is not None:
        return _image_provider

    provider_name = settings.AI_IMAGE_PROVIDER.lower()
    logger.info(f"Initializing image provider: {provider_name}")

    if provider_name == "openai":
        from app.services.ai.openai_provider import OpenAIImageProvider
        _image_provider = OpenAIImageProvider(api_key=settings.OPENAI_API_KEY)

    elif provider_name == "gemini":
        from app.services.ai.gemini_provider import GeminiImageProvider
        _image_provider = GeminiImageProvider(api_key=settings.GEMINI_API_KEY)

    else:
        raise ValueError(
            f"Unknown AI_IMAGE_PROVIDER: '{provider_name}'. "
            f"Supported: 'openai', 'gemini'"
        )

    logger.info(f"Image provider ready: {provider_name} / {settings.AI_IMAGE_MODEL}")
    return _image_provider


def reset_providers():
    """Reset singletons — useful for testing."""
    global _text_provider, _image_provider
    _text_provider = None
    _image_provider = None
