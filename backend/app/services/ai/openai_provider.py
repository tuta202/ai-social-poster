"""
OpenAI implementation of TextProvider and ImageProvider.
"""
from openai import AsyncOpenAI
from app.services.ai.base import TextProvider, ImageProvider


class OpenAITextProvider(TextProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content.strip()


class OpenAIImageProvider(ImageProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        model: str,
        size: str = "1024x1024",
    ) -> str:
        response = await self._client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
