"""
APScheduler background job — polls DB every minute for due posts.
Runs inside the FastAPI process (single worker on Railway).
"""
import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import Job, JobPost, JobStatus, PostStatus, FacebookPage
from app.services.fb_poster import post_to_facebook

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _post_due_items():
    """
    Scheduler tick — runs every minute. Handles 3 tasks:
    1. Post APPROVED posts that are due
    2. Fallback: post PENDING posts with content that are overdue
    3. Generate content for next day's posts (when scheduled_time arrives)
    """
    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()

    try:
        # ── Task 1: Post APPROVED due posts ───────────────────────────────
        approved_due = (
            db.query(JobPost)
            .join(Job)
            .filter(
                JobPost.status == PostStatus.APPROVED,
                JobPost.scheduled_time <= now,
                Job.status.in_([JobStatus.SCHEDULED, JobStatus.RUNNING]),
            )
            .order_by(JobPost.scheduled_time)
            .limit(20)
            .all()
        )

        for job_post in approved_due:
            await _do_post(job_post, db)

        # ── Task 2: Fallback — post PENDING overdue posts with content ────
        pending_overdue = (
            db.query(JobPost)
            .join(Job)
            .filter(
                JobPost.status == PostStatus.PENDING,
                JobPost.content_text.isnot(None),
                JobPost.content_text != "",
                JobPost.scheduled_time <= now,
                Job.status.in_([JobStatus.SCHEDULED, JobStatus.RUNNING]),
            )
            .order_by(JobPost.scheduled_time)
            .limit(20)
            .all()
        )

        for job_post in pending_overdue:
            logger.info(f"Fallback: posting unapproved post {job_post.id} (past due)")
            await _do_post(job_post, db)

        # ── Task 3: Generate next day content ─────────────────────────────
        await _generate_upcoming_content(db, now)

    except Exception as e:
        logger.error(f"Scheduler tick error: {e}")
    finally:
        db.close()


async def _do_post(job_post: JobPost, db: Session):
    """Post a single JobPost to Facebook and update status."""
    job = job_post.job

    page = (
        db.query(FacebookPage)
        .filter(FacebookPage.user_id == job.user_id)
        .first()
    )
    if not page:
        job_post.status = PostStatus.FAILED
        job_post.error_message = "No Facebook page configured for this user"
        db.commit()
        return

    if job.status == JobStatus.SCHEDULED:
        job.status = JobStatus.RUNNING
        db.commit()

    try:
        fb_post_id = await post_to_facebook(
            page=page,
            message=job_post.content_text,
            image_url=job_post.image_url,
        )
        job_post.status = PostStatus.POSTED
        job_post.fb_post_id = fb_post_id
        job_post.posted_at = datetime.now(timezone.utc)
        job_post.error_message = None
        logger.info(f"Posted job_post {job_post.id} → fb_post_id={fb_post_id}")
    except Exception as e:
        job_post.status = PostStatus.FAILED
        job_post.error_message = str(e)[:500]
        logger.error(f"Failed to post job_post {job_post.id}: {e}")

    db.commit()
    _check_job_completion(job, db)


async def _generate_upcoming_content(db: Session, now: datetime):
    """
    Find posts for upcoming days that have no content yet → generate.
    Only generates if content_text is empty (not yet generated).
    """
    from itertools import groupby
    from operator import attrgetter
    from app.services.content_gen import generate_day_content
    from app.schemas.schemas import ParsedConfig

    from sqlalchemy import or_

    empty_due = (
        db.query(JobPost)
        .join(Job)
        .filter(
            JobPost.status == PostStatus.PENDING,
            or_(JobPost.content_text.is_(None), JobPost.content_text == ""),
            JobPost.scheduled_time <= now,
            Job.status.in_([JobStatus.SCHEDULED, JobStatus.RUNNING]),
        )
        .order_by(JobPost.job_id, JobPost.day_index)
        .all()
    )

    if not empty_due:
        return

    empty_due.sort(key=lambda p: (p.job_id, p.day_index))
    for (job_id, day_index), posts_group in groupby(
        empty_due, key=lambda p: (p.job_id, p.day_index)
    ):
        posts = list(posts_group)
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.parsed_config:
            continue

        try:
            config = ParsedConfig(**job.parsed_config)
            logger.info(f"Generating content for job {job_id} day {day_index}")

            results = await generate_day_content(
                config=config,
                day_index=day_index,
                job_id=job_id,
                style_profile=job.style_profile,
            )

            for post, result in zip(
                sorted(posts, key=attrgetter("post_order")), results
            ):
                post.content_text = result["content_text"]
                post.original_content_text = result["content_text"]
                post.image_url = result.get("image_url")
                post.image_prompt = result.get("image_prompt")

            db.commit()
            logger.info(f"Generated {len(results)} posts for job {job_id} day {day_index}")

        except Exception as e:
            logger.error(f"Failed to generate day {day_index} for job {job_id}: {e}")


def _check_job_completion(job: Job, db: Session):
    """Mark job as DONE if all posts are POSTED or FAILED."""
    pending_count = (
        db.query(JobPost)
        .filter(
            JobPost.job_id == job.id,
            JobPost.status.in_([PostStatus.PENDING, PostStatus.APPROVED]),
        )
        .count()
    )
    if pending_count == 0:
        job.status = JobStatus.DONE
        db.commit()
        logger.info(f"Job {job.id} marked DONE")


def start_scheduler():
    """Start APScheduler. Call on FastAPI startup."""
    scheduler.add_job(
        _post_due_items,
        trigger="interval",
        minutes=1,
        id="post_due_items",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("APScheduler started — polling every 60 seconds")


def stop_scheduler():
    """Stop APScheduler. Call on FastAPI shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
