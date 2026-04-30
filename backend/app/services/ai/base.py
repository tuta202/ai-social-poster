"""
Abstract base interfaces for AI providers.
All providers must implement these interfaces.
"""
from abc import ABC, abstractmethod


class TextProvider(ABC):
    """Abstract interface for text generation (LLM)."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text completion.
        Returns the generated text string.
        Raises Exception on failure — no silent fallback.
        """
        ...


class ImageProvider(ABC):
    """Abstract interface for image generation."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        size: str = "1024x1024",
    ) -> str:
        """
        Generate image from prompt.
        Returns image URL string.
        Raises Exception on failure — no silent fallback.
        """
        ...
