"""
Google Gemini implementation of TextProvider and ImageProvider.
- Text: google-generativeai SDK (gemini-1.5-pro, gemini-1.5-flash)
- Image: Imagen 3 via Gemini API (imagen-3.0-generate-001)

Note: google-generativeai imports are lazy (inside methods) to avoid
module-level import errors on Python 3.14 due to a protobuf C-extension
metaclass incompatibility. Production (Python 3.11/3.12) is unaffected.
"""
import asyncio
import httpx
from app.services.ai.base import TextProvider, ImageProvider


class GeminiTextProvider(TextProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self._api_key = api_key

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
        Gemini uses system_instruction separately from user message.
        Runs sync SDK in executor to avoid blocking event loop.
        """
        import google.generativeai as genai  # lazy import — avoids protobuf crash at module load

        genai.configure(api_key=self._api_key)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
        )

        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system,
            generation_config=generation_config,
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gemini_model.generate_content(user),
        )

        text = response.text.strip()

        # Strip markdown code fences if present (Gemini sometimes adds them)
        if json_mode and text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]).strip()

        return text


class GeminiImageProvider(ImageProvider):
    """
    Imagen 3 via Gemini Developer API.
    Returns base64 data URL — caller must handle Facebook compatibility.
    fb_poster.py detects data: URLs and falls back to text-only post.
    """

    IMAGEN_ENDPOINT = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        "/{model}:predict"
    )

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self._api_key = api_key

    async def generate(
        self,
        prompt: str,
        model: str,
        size: str = "1024x1024",
    ) -> str:
        """
        Generate image via Imagen 3 API.
        Returns base64 data URL (data:image/png;base64,...).
        Note: Facebook Graph API needs a public URL — fb_poster.py handles this
        by falling back to text-only when a data URL is detected.
        """
        url = self.IMAGEN_ENDPOINT.format(model=model)

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
            )

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text[:200])
            raise Exception(f"Imagen API error {response.status_code}: {error_msg}")

        data = response.json()
        predictions = data.get("predictions", [])
        if not predictions:
            raise Exception("Imagen API returned no predictions")

        b64_image = predictions[0].get("bytesBase64Encoded")
        if not b64_image:
            raise Exception("Imagen API: no image data in response")

        return f"data:image/png;base64,{b64_image}"
