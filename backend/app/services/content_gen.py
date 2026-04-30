import asyncio
import json
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


def _build_text_prompt(
    config: ParsedConfig,
    day_index: int,
    post_order: int,
    style_profile: Optional[dict] = None,
) -> str:
    base = f"""Campaign: {config.title}
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

    if style_profile:
        base += f"""

IMPORTANT — Follow this user's style profile strictly:
{json.dumps(style_profile, ensure_ascii=False, indent=2)}
"""
    return base


async def generate_text(
    config: ParsedConfig,
    day_index: int,
    post_order: int,
    max_retries: int = 2,
    style_profile: Optional[dict] = None,
) -> str:
    for attempt in range(max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": TEXT_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_text_prompt(
                        config, day_index, post_order, style_profile
                    )},
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


# ── Style Profile Extraction ───────────────────────────────────────────────

STYLE_EXTRACT_PROMPT = """You are analyzing edits a user made to social media content.
Compare the original and edited versions, then extract the user's style preferences.

Return ONLY valid JSON (no markdown):
{
  "tone": "describe the tone (e.g. casual, formal, playful, professional)",
  "format": "describe formatting preferences (e.g. uses emojis, bullet points, bold words)",
  "length": "describe length preference (e.g. short and punchy, detailed with examples)",
  "structure": "describe content structure (e.g. word → reading → meaning → example)",
  "language_notes": "any language-specific observations (e.g. mixes Vietnamese and Japanese)",
  "other": "any other notable style preferences"
}

If the versions are identical or nearly identical, return:
{"no_changes": true}
"""


async def generate_style_profile(
    original_text: str,
    edited_text: str,
) -> Optional[dict]:
    """
    Extract style profile from user's edits using GPT-4o Mini.
    Returns None if no significant changes detected.
    """
    if not original_text or not edited_text:
        return None
    if original_text.strip() == edited_text.strip():
        return None

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": STYLE_EXTRACT_PROMPT},
                {"role": "user", "content": f"ORIGINAL:\n{original_text}\n\nEDITED:\n{edited_text}"},
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        if data.get("no_changes"):
            return None
        return data
    except Exception:
        return None


# ── Day-level Generation ───────────────────────────────────────────────────

async def generate_day_content(
    config: ParsedConfig,
    day_index: int,
    job_id: int,
    style_profile: Optional[dict] = None,
) -> list[dict]:
    """
    Generate content for all posts in a single day.
    Used by confirm (Day 1) and scheduler (Day N+1).
    """
    posts_per_day = config.items_per_day
    results = []

    for post_order in range(1, posts_per_day + 1):
        text = await generate_text(
            config, day_index, post_order, style_profile=style_profile
        )
        image_url = None
        image_prompt = None
        if config.has_images:
            image_url, image_prompt = await generate_image(config, day_index)

        results.append({
            "day_index": day_index,
            "post_order": post_order,
            "content_text": text,
            "original_content_text": text,
            "image_url": image_url,
            "image_prompt": image_prompt,
        })
        if post_order < posts_per_day:
            await asyncio.sleep(0.3)

    return results


# ── Image Generation ───────────────────────────────────────────────────────

IMAGE_PROMPT_DEVELOPER_SYSTEM = """You are an expert at writing prompts for DALL-E 3 image generation.
Your job is to take a user's image description and develop it into an optimal DALL-E 3 prompt.

Rules:
- Output ONLY the prompt text, no explanation, no quotes
- Always add: "No text or typography in the image. Square format, suitable for Facebook post."
- Keep it under 150 words
- Be specific about style, colors, mood, composition
- If description mentions a specific style (anime, flat design, etc.), emphasize it
- Make it visually appealing for social media
"""


async def generate_image_prompt(
    image_description: str,
    content_type: str,
    day_index: int,
) -> str:
    """
    Develop user's image description into optimized DALL-E 3 prompt via GPT-4o Mini.
    Falls back to a generic prompt if no description or API fails.
    """
    if not image_description.strip():
        return (
            f"Clean, minimal flat design illustration for a {content_type} social media post. "
            f"Warm colors, professional look. No text or typography. Square format."
        )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": IMAGE_PROMPT_DEVELOPER_SYSTEM},
                {"role": "user", "content": (
                    f"Image description: {image_description}\n"
                    f"Content type: {content_type}\n"
                    f"Day: {day_index}\n"
                    f"Develop this into an optimal DALL-E 3 prompt."
                )},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            f"{image_description}. Clean illustration for {content_type} Facebook post. "
            f"No text or typography in the image. Square format."
        )


async def generate_image(
    config: ParsedConfig,
    day_index: int,
    max_retries: int = 1,
) -> tuple[Optional[str], str]:
    """
    Generate image via DALL-E 3.
    Uses GPT-4o Mini to develop image_description into optimized prompt.
    Returns (image_url, image_prompt). image_url is None on failure.
    """
    prompt = await generate_image_prompt(
        image_description=config.image_description,
        content_type=config.content_type,
        day_index=day_index,
    )

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
