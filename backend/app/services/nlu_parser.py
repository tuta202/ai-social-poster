import json
import re
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.schemas import ParsedConfig

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT = """You are a social media campaign planning assistant.
Your job is to parse natural language commands (in ANY language) into structured JSON campaign configurations.

The user wants to create a Facebook posting campaign. Extract the following information:

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no explanation:
{
  "title": "short campaign title in the same language as input",
  "duration_days": <integer, number of days>,
  "items_per_day": <integer, posts per day>,
  "post_time": "<HH:MM in 24h format, e.g. 08:00>",
  "content_type": "<one of: vocabulary, grammar, dialogue, motivation, lifestyle, custom>",
  "has_images": <true or false>,
  "tags": ["tag1", "tag2"],
  "notes": "any extra instructions for content generation"
}

DEFAULTS if not specified:
- duration_days: 7
- items_per_day: 1
- post_time: "08:00"
- content_type: "custom"
- has_images: false
- tags: []
- notes: ""

RULES:
- Always return valid JSON only
- Infer content_type from context (e.g. "từ vựng N2" → "vocabulary", "động lực" → "motivation")
- If user mentions images/ảnh → has_images: true
- Normalize typos (e.g. "1O ngày" → duration_days: 10)
- post_time: if user says "buổi sáng/morning" → "08:00", "trưa/noon" → "12:00", "tối/evening" → "20:00"
- title: concise, max 60 chars
"""


async def parse_command(raw_input: str) -> ParsedConfig:
    """
    Parse natural language input into ParsedConfig using GPT-4o.
    Falls back to defaults on any parse error.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_input.strip()},
            ],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)


        return _normalize_config(data, raw_input)

    except Exception as e:
        return _default_config(raw_input, error=str(e))


def _normalize_config(data: dict, raw_input: str) -> ParsedConfig:
    """Validate and normalize parsed config, applying defaults for missing fields."""

    duration_days = max(1, min(int(data.get("duration_days", 7)), 365))
    items_per_day = max(1, min(int(data.get("items_per_day", 1)), 10))

    post_time = data.get("post_time", "08:00")
    if not re.match(r"^\d{2}:\d{2}$", str(post_time)):
        post_time = "08:00"

    valid_types = {"vocabulary", "grammar", "dialogue", "motivation", "lifestyle", "custom"}
    content_type = data.get("content_type", "custom")
    if content_type not in valid_types:
        content_type = "custom"

    title = str(data.get("title", "")).strip()
    if not title:
        title = raw_input[:60].strip()

    return ParsedConfig(
        title=title,
        duration_days=duration_days,
        items_per_day=items_per_day,
        post_time=post_time,
        content_type=content_type,
        has_images=bool(data.get("has_images", False)),
        tags=[str(t) for t in data.get("tags", [])],
        notes=str(data.get("notes", "")),
    )


def _default_config(raw_input: str, error: str = "") -> ParsedConfig:
    """Emergency fallback config when parsing completely fails."""
    return ParsedConfig(
        title=raw_input[:60].strip(),
        duration_days=7,
        items_per_day=1,
        post_time="08:00",
        content_type="custom",
        has_images=False,
        tags=[],
        notes=f"[Auto-generated from: {raw_input[:100]}]" + (f" [Parse error: {error[:100]}]" if error else ""),
    )
