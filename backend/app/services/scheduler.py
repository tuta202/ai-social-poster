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
    Check for PENDING posts that are due (scheduled_time <= now).
    Post them to Facebook and update status.
    Skips posts belonging to PAUSED jobs.
    """
    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()

    try:
        due_posts = (
            db.query(JobPost)
            .join(Job)
            .filter(
                JobPost.status == PostStatus.PENDING,
                JobPost.scheduled_time <= now,
                Job.status.in_([JobStatus.SCHEDULED, JobStatus.RUNNING]),
            )
            .order_by(JobPost.scheduled_time)
            .limit(20)
            .all()
        )

        if not due_posts:
            return

        logger.info(f"Scheduler: {len(due_posts)} due posts found")

        for job_post in due_posts:
            job = job_post.job

            # Get Facebook page for this user
            page = (
                db.query(FacebookPage)
                .filter(FacebookPage.user_id == job.user_id)
                .first()
            )

            if not page:
                logger.warning(
                    f"No Facebook page configured for user {job.user_id}, "
                    f"skipping post {job_post.id}"
                )
                job_post.status = PostStatus.FAILED
                job_post.error_message = "No Facebook page configured for this user"
                db.commit()
                continue

            # Set job to RUNNING on first post
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
                logger.info(f"Posted job_post {job_post.id} -> fb_post_id={fb_post_id}")

            except Exception as e:
                job_post.status = PostStatus.FAILED
                job_post.error_message = str(e)[:500]
                logger.error(f"Failed to post job_post {job_post.id}: {e}")

            db.commit()
            _check_job_completion(job, db)

    except Exception as e:
        logger.error(f"Scheduler tick error: {e}")
    finally:
        db.close()


def _check_job_completion(job: Job, db: Session):
    """Mark job as DONE if all posts are POSTED or FAILED."""
    pending_count = (
        db.query(JobPost)
        .filter(
            JobPost.job_id == job.id,
            JobPost.status == PostStatus.PENDING,
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
