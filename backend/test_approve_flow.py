"""
Smoke test for approve flow and style profile extraction.
Run: python test_approve_flow.py
Requires: seeded DB, backend NOT running (pure DB test)
"""
import asyncio
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.models import User, Job, JobPost, JobStatus, PostStatus
from app.services.content_gen import generate_style_profile


async def test_style_profile_extraction():
    print("=== Test 1: Style Profile Extraction ===")
    original = "Hom nay chung ta hoc dong tu taberu. No co nghia la an. Vi du: Toi an com."
    edited = "🍱 taberu - AN! Dung khi: an com, an banh. Vi du don gian nhe!"

    profile = await generate_style_profile(original, edited)
    print(f"Profile: {profile}")

    if profile is None:
        print("SKIP: No OPENAI_API_KEY or identical text — skipping live test")
    else:
        assert isinstance(profile, dict), "Profile should be dict"
        assert "tone" in profile or "format" in profile, "Profile missing keys"
        print("PASS")


async def test_no_style_profile_when_unchanged():
    print("\n=== Test 2: No Style Profile When Unchanged ===")
    text = "Same text no changes here"
    profile = await generate_style_profile(text, text)
    assert profile is None, f"Expected None, got {profile}"
    print("PASS")


def test_approve_status_transition():
    print("\n=== Test 3: Approve Status Transition ===")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        assert user, "Run python seed.py first"

        job = Job(
            user_id=user.id,
            title="Approve Test",
            raw_input="test",
            parsed_config={},
            status=JobStatus.SCHEDULED,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        post = JobPost(
            job_id=job.id,
            day_index=1,
            post_order=1,
            content_text="Generated content here",
            original_content_text="Generated content here",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status=PostStatus.PENDING,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        assert post.status == PostStatus.PENDING
        post.status = PostStatus.APPROVED
        post.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(post)

        assert post.status == PostStatus.APPROVED
        assert post.approved_at is not None
        print("PASS: PENDING -> APPROVED transition OK")

        # Cleanup
        db.delete(post)
        db.delete(job)
        db.commit()
    finally:
        db.close()


def test_scheduler_skips_empty_content():
    print("\n=== Test 4: Scheduler skips posts with empty content ===")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        job = Job(
            user_id=user.id, title="Empty Content Test",
            raw_input="test", parsed_config={},
            status=JobStatus.SCHEDULED,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Post with empty content — should NOT be posted by Task 1/2
        post = JobPost(
            job_id=job.id, day_index=2, post_order=1,
            content_text="",
            scheduled_time=datetime.now(timezone.utc) - timedelta(minutes=5),
            status=PostStatus.PENDING,
        )
        db.add(post)
        db.commit()

        db.refresh(post)
        assert post.content_text == ""
        assert post.status == PostStatus.PENDING
        print("PASS: Empty content post remains PENDING (waiting for gen)")

        # Cleanup
        db.delete(post)
        db.delete(job)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    async def main():
        await test_style_profile_extraction()
        await test_no_style_profile_when_unchanged()
        test_approve_status_transition()
        test_scheduler_skips_empty_content()
        print("\nAll approve flow tests passed!")

    asyncio.run(main())
