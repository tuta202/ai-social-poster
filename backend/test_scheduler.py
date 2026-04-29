"""
Manual smoke test for scheduler logic (no real Facebook calls).
Tests: _post_due_items with mock FB page, status transitions, job completion.
Run: python test_scheduler.py
Requires: seeded DB (python seed.py), no uvicorn needed.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from app.core.database import SessionLocal
from app.models.models import (
    User, Job, JobPost, JobStatus, PostStatus, FacebookPage
)
from app.services.scheduler import _post_due_items, _check_job_completion


def setup_test_data(db):
    """Create test job with 2 due posts and 1 future post."""
    user = db.query(User).filter(User.username == "admin").first()
    assert user, "Run python seed.py first"

    page = db.query(FacebookPage).filter(FacebookPage.user_id == user.id).first()
    if not page:
        page = FacebookPage(
            user_id=user.id,
            page_id="123456789",
            page_name="Test Page",
            access_token="fake-token-for-testing",
        )
        db.add(page)
        db.commit()

    now = datetime.now(timezone.utc)

    job = Job(
        user_id=user.id,
        title="Test Scheduler Job",
        raw_input="test",
        parsed_config={},
        status=JobStatus.SCHEDULED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    posts = [
        JobPost(job_id=job.id, day_index=1, post_order=1,
                content_text="Post 1 -- due", scheduled_time=now - timedelta(minutes=5),
                status=PostStatus.PENDING),
        JobPost(job_id=job.id, day_index=1, post_order=2,
                content_text="Post 2 -- due", scheduled_time=now - timedelta(minutes=1),
                status=PostStatus.PENDING),
        JobPost(job_id=job.id, day_index=2, post_order=1,
                content_text="Post 3 -- future", scheduled_time=now + timedelta(hours=2),
                status=PostStatus.PENDING),
    ]
    for p in posts:
        db.add(p)
    db.commit()

    return job.id


async def test_scheduler_posts_due_items():
    db = SessionLocal()
    job_id = setup_test_data(db)
    db.close()

    with patch(
        "app.services.scheduler.post_to_facebook",
        new_callable=AsyncMock,
        return_value="fake_fb_post_id_123",
    ):
        await _post_due_items()

    db = SessionLocal()
    try:
        posts = (
            db.query(JobPost)
            .filter(JobPost.job_id == job_id)
            .order_by(JobPost.day_index, JobPost.post_order)
            .all()
        )
        job = db.query(Job).filter(Job.id == job_id).first()

        assert posts[0].status == PostStatus.POSTED, f"Post 1: {posts[0].status}"
        assert posts[0].fb_post_id == "fake_fb_post_id_123"
        assert posts[1].status == PostStatus.POSTED, f"Post 2: {posts[1].status}"
        assert posts[2].status == PostStatus.PENDING, f"Post 3 should still be pending"
        assert job.status == JobStatus.RUNNING, f"Job should be RUNNING, got {job.status}"

        print("PASS: 2 due posts -> POSTED, 1 future post -> PENDING, job -> RUNNING")

        db.query(JobPost).filter(JobPost.job_id == job_id).delete()
        db.query(Job).filter(Job.id == job_id).delete()
        db.commit()

    finally:
        db.close()


async def test_job_completion():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()

    job = Job(
        user_id=user.id, title="Completion Test", raw_input="test",
        parsed_config={}, status=JobStatus.RUNNING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    posts = [
        JobPost(job_id=job.id, day_index=1, post_order=1,
                content_text="p1", scheduled_time=datetime.now(timezone.utc),
                status=PostStatus.POSTED),
        JobPost(job_id=job.id, day_index=1, post_order=2,
                content_text="p2", scheduled_time=datetime.now(timezone.utc),
                status=PostStatus.FAILED),
    ]
    for p in posts:
        db.add(p)
    db.commit()

    _check_job_completion(job, db)
    db.refresh(job)
    assert job.status == JobStatus.DONE, f"Expected DONE, got {job.status}"
    print("PASS: job with no PENDING posts -> DONE")

    db.query(JobPost).filter(JobPost.job_id == job.id).delete()
    db.query(Job).filter(Job.id == job.id).delete()
    db.commit()
    db.close()


async def test_paused_job_skipped():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    now = datetime.now(timezone.utc)

    job = Job(
        user_id=user.id, title="Paused Job", raw_input="test",
        parsed_config={}, status=JobStatus.PAUSED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    post = JobPost(
        job_id=job.id, day_index=1, post_order=1,
        content_text="paused post", scheduled_time=now - timedelta(minutes=1),
        status=PostStatus.PENDING,
    )
    db.add(post)
    db.commit()
    job_id = job.id
    post_id = post.id
    db.close()

    with patch("app.services.scheduler.post_to_facebook", new_callable=AsyncMock) as mock_fb:
        await _post_due_items()
        assert not mock_fb.called, "post_to_facebook should not be called for PAUSED job"

    db = SessionLocal()
    try:
        p = db.query(JobPost).filter(JobPost.id == post_id).first()
        assert p.status == PostStatus.PENDING, f"PAUSED job post should stay PENDING, got {p.status}"
        print("PASS: PAUSED job posts are skipped by scheduler")
        db.query(JobPost).filter(JobPost.job_id == job_id).delete()
        db.query(Job).filter(Job.id == job_id).delete()
        db.commit()
    finally:
        db.close()


async def test_post_failure():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    now = datetime.now(timezone.utc)

    page = db.query(FacebookPage).filter(FacebookPage.user_id == user.id).first()
    if not page:
        page = FacebookPage(
            user_id=user.id, page_id="999", page_name="Test",
            access_token="fake",
        )
        db.add(page)
        db.commit()

    job = Job(
        user_id=user.id, title="Fail Test", raw_input="test",
        parsed_config={}, status=JobStatus.SCHEDULED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    post = JobPost(
        job_id=job.id, day_index=1, post_order=1,
        content_text="fail post", scheduled_time=now - timedelta(minutes=1),
        status=PostStatus.PENDING,
    )
    db.add(post)
    db.commit()
    job_id = job.id
    post_id = post.id
    db.close()

    with patch(
        "app.services.scheduler.post_to_facebook",
        new_callable=AsyncMock,
        side_effect=Exception("API error: invalid token"),
    ):
        await _post_due_items()  # must not raise

    db = SessionLocal()
    try:
        p = db.query(JobPost).filter(JobPost.id == post_id).first()
        assert p.status == PostStatus.FAILED, f"Expected FAILED, got {p.status}"
        assert "API error" in (p.error_message or ""), f"error_message: {p.error_message}"
        print("PASS: post failure -> FAILED status + error_message, no crash")
        db.query(JobPost).filter(JobPost.job_id == job_id).delete()
        db.query(Job).filter(Job.id == job_id).delete()
        db.commit()
    finally:
        db.close()


async def test_no_facebook_page():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    now = datetime.now(timezone.utc)

    # Remove any existing page
    db.query(FacebookPage).filter(FacebookPage.user_id == user.id).delete()
    db.commit()

    job = Job(
        user_id=user.id, title="No Page Test", raw_input="test",
        parsed_config={}, status=JobStatus.SCHEDULED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    post = JobPost(
        job_id=job.id, day_index=1, post_order=1,
        content_text="no page post", scheduled_time=now - timedelta(minutes=1),
        status=PostStatus.PENDING,
    )
    db.add(post)
    db.commit()
    job_id = job.id
    post_id = post.id
    db.close()

    await _post_due_items()

    db = SessionLocal()
    try:
        p = db.query(JobPost).filter(JobPost.id == post_id).first()
        assert p.status == PostStatus.FAILED
        assert "No Facebook page configured" in (p.error_message or "")
        print("PASS: no FacebookPage -> post FAILED with descriptive message")
        db.query(JobPost).filter(JobPost.job_id == job_id).delete()
        db.query(Job).filter(Job.id == job_id).delete()
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    async def main():
        print("=== Test 1: Scheduler posts due items ===")
        await test_scheduler_posts_due_items()

        print("\n=== Test 2: Job completion check ===")
        await test_job_completion()

        print("\n=== Test 3: Paused job skipped ===")
        await test_paused_job_skipped()

        print("\n=== Test 4: Post failure graceful ===")
        await test_post_failure()

        print("\n=== Test 5: No Facebook page configured ===")
        await test_no_facebook_page()

        print("\nAll scheduler tests passed!")

    asyncio.run(main())
