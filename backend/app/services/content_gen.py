import asyncio
from typing import Optional, Callable
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.schemas import ParsedConfig

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ── Text Generation ────────────────────────────────────────────────────────

TEXT_SYSTEM_PROMPT = """You are a creative social media content writer for Facebook.
Generate engaging post content based on the campaign configuration provided.
Write in the SAME LANGUAGE as the campaign notes/title unless specified otherwise.
Keep posts natural, engaging, and appropriate for Facebook audiences.
Do NOT include hashtags in content_text — they will be added separately from tags list.
Do NOT add any meta-commentary. Output ONLY the post text itself.
"""


def _build_text_prompt(config: ParsedConfig, day_index: int, post_order: int) -> str:
    return f"""Campaign: {config.title}
Content type: {config.content_type}
Day: {day_index} of {config.duration_days}
Post: {post_order} of {config.items_per_day}
Notes: {config.notes}
Tags to reference (do NOT include as hashtags): {', '.join(config.tags)}

Write the Facebook post content for this slot. Be specific, engaging, and varied from other days.
If content_type is 'vocabulary': include the word, reading, meaning, and example sentence.
If content_type is 'motivation': write an inspiring message relevant to the campaign theme.
If content_type is 'grammar': explain a grammar point with clear examples.
Otherwise: create appropriate content for the campaign theme."""


async def generate_text(
    config: ParsedConfig,
    day_index: int,
    post_order: int,
    max_retries: int = 2,
) -> str:
    """Generate post text content via GPT-4o. Returns fallback string on failure."""
    for attempt in range(max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": TEXT_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_text_prompt(config, day_index, post_order)},
                ],
                temperature=0.8,
                max_tokens=600,
            )
            text = response.choices[0].message.content.strip()
            if config.tags:
                hashtags = " ".join(f"#{t.strip().replace(' ', '_')}" for t in config.tags)
                text = f"{text}\n\n{hashtags}"
            return text
        except Exception as e:
            if attempt == max_retries:
                return f"[Content for Day {day_index}, Post {post_order} — generation failed: {str(e)[:80]}]"
            await asyncio.sleep(1)

    return f"[Content for Day {day_index}, Post {post_order}]"


# ── Image Generation ───────────────────────────────────────────────────────

IMAGE_PROMPT_TEMPLATE = """Simple, clean illustration for a Facebook educational post.
Theme: {theme}
Style: flat design, minimal, warm colors, no text in image.
Content hint: Day {day_index} - {content_type} post.
Aspect ratio: square."""


def _build_image_prompt(config: ParsedConfig, day_index: int) -> str:
    theme = config.notes if config.notes else config.title
    return IMAGE_PROMPT_TEMPLATE.format(
        theme=theme[:200],
        day_index=day_index,
        content_type=config.content_type,
    )


async def generate_image(
    config: ParsedConfig,
    day_index: int,
    max_retries: int = 1,
) -> tuple[Optional[str], str]:
    """
    Generate image via DALL-E 3.
    Returns (image_url, image_prompt).
    image_url is None on failure (post will be text-only).
    """
    prompt = _build_image_prompt(config, day_index)

    for attempt in range(max_retries + 1):
        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            url = response.data[0].url
            return url, prompt
        except Exception:
            if attempt == max_retries:
                return None, prompt
            await asyncio.sleep(2)

    return None, prompt


# ── Batch Generation ───────────────────────────────────────────────────────

async def generate_all_content(
    config: ParsedConfig,
    post_slots: list[dict],
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict]:
    """
    Generate content for all post slots.
    post_slots: list of dicts from generate_schedule()
    on_progress: optional callback(current, total) for SSE progress
    Returns updated post_slots with content_text, image_url, image_prompt filled in.
    """
    total = len(post_slots)
    results = []

    for i, slot in enumerate(post_slots):
        text = await generate_text(config, slot["day_index"], slot["post_order"])

        image_url = slot.get("image_url")
        image_prompt = slot.get("image_prompt")

        if config.has_images and not image_url:
            image_url, image_prompt = await generate_image(config, slot["day_index"])

        updated = {
            **slot,
            "content_text": text,
            "image_url": image_url,
            "image_prompt": image_prompt,
        }
        results.append(updated)

        if on_progress:
            on_progress(i + 1, total)

        if i < total - 1:
            await asyncio.sleep(0.3)

    return results
