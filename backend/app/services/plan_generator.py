from datetime import datetime, timedelta, timezone
from typing import List, Optional
from app.schemas.schemas import ParsedConfig


def generate_schedule(
    config: ParsedConfig,
    job_id: int,
    start_date: Optional[datetime] = None,
) -> List[dict]:
    """
    Generate a list of post schedule entries from ParsedConfig.
    Returns list of dicts ready to create JobPost records.
    Does NOT generate content — only metadata + scheduled_time.
    """
    if start_date is None:
        now = datetime.now(timezone.utc)
        start_date = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    hour, minute = map(int, config.post_time.split(":"))
    posts = []

    for day_index in range(1, config.duration_days + 1):
        for post_order in range(1, config.items_per_day + 1):
            scheduled_dt = start_date + timedelta(days=day_index - 1)
            scheduled_dt = scheduled_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

            posts.append({
                "job_id": job_id,
                "day_index": day_index,
                "post_order": post_order,
                "content_text": None,
                "image_url": None,
                "image_prompt": None,
                "scheduled_time": scheduled_dt,
                "status": "PENDING",
            })

    return posts
