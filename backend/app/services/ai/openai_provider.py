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
        quality: str = "low",
        style: str = "vivid",
    ) -> str:
        kwargs: dict = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }

        # gpt-image-1.x / gpt-image-2 family: quality=low|medium|high, NO style/response_format param
        # These models return b64_json by default (url field will be None)
        GPT_IMAGE_FAMILY = ("gpt-image-1", "gpt-image-1.5", "gpt-image-2")
        if model in GPT_IMAGE_FAMILY:
            kwargs["quality"] = quality if quality in ("low", "medium", "high") else "low"

        elif model == "dall-e-3":
            # dall-e-3: quality=standard|hd, style=vivid|natural — returns URL
            kwargs["quality"] = quality if quality in ("standard", "hd") else "standard"
            kwargs["style"] = style if style in ("vivid", "natural") else "vivid"

        # dall-e-2: no quality/style — returns URL by default

        response = await self._client.images.generate(**kwargs)
        img = response.data[0]

        # gpt-image family returns b64_json → convert to data URI
        if img.url:
            return img.url
        if img.b64_json:
            return f"data:image/png;base64,{img.b64_json}"
        raise ValueError(f"OpenAI image response has neither url nor b64_json (model={model})")

