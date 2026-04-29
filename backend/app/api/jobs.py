import asyncio
import json
from typing import AsyncGenerator, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import Job, JobPost, JobStatus, PostStatus, User
from app.schemas.schemas import (
    ParseJobRequest, JobOut, JobListOut, JobPreviewResponse, JobPostOut, ParsedConfig
)
from app.services.nlu_parser import parse_command
from app.services.plan_generator import generate_schedule
from app.services.content_gen import generate_all_content

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────

def _compute_counts(job_id: int, db: Session) -> dict:
    """Compute post status counts for a job."""
    posts = db.query(JobPost).filter(JobPost.job_id == job_id).all()
    return {
        "total_posts": len(posts),
        "posted_count": sum(1 for p in posts if p.status == PostStatus.POSTED),
        "failed_count": sum(1 for p in posts if p.status == PostStatus.FAILED),
    }


# ── POST /jobs/parse ───────────────────────────────────────────────────────

@router.post("/parse")
async def parse_job(
    request: ParseJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parse natural language → create Job DRAFT → return SSE stream with progress.
    SSE events:
      step: {step: "parsing", message: "Analysing your command..."}
      step: {step: "parsed", config: ParsedConfig.dict()}
      step: {step: "scheduling", message: "Building post schedule..."}
      done: {job_id: int, config: dict, posts: list}
      error: {message: str}
    """
    async def event_stream() -> AsyncGenerator[str, None]:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

        try:
            # Step 1: Parse
            yield sse("step", {"step": "parsing", "message": "Analysing your command..."})
            config: ParsedConfig = await parse_command(request.raw_input)
            yield sse("step", {"step": "parsed", "config": config.model_dump()})

            # Step 2: Create Job in DB
            yield sse("step", {"step": "scheduling", "message": "Building post schedule..."})
            job = Job(
                user_id=current_user.id,
                title=config.title,
                raw_input=request.raw_input,
                parsed_config=config.model_dump(),
                status=JobStatus.DRAFT,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Step 3: Generate schedule slots (no content yet)
            slots = generate_schedule(config, job_id=job.id)
            for slot in slots:
                post = JobPost(
                    job_id=job.id,
                    day_index=slot["day_index"],
                    post_order=slot["post_order"],
                    content_text="",
                    image_url=None,
                    image_prompt=None,
                    scheduled_time=slot["scheduled_time"],
                    status=PostStatus.PENDING,
                )
                db.add(post)
            db.commit()

            # Reload posts
            db.refresh(job)
            posts_out = [
                JobPostOut.model_validate(p).model_dump(mode="json")
                for p in sorted(job.posts, key=lambda x: x.scheduled_time)
            ]

            yield sse("done", {
                "job_id": job.id,
                "config": config.model_dump(),
                "posts": posts_out,
            })

        except Exception as e:
            yield sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /jobs/{id}/confirm ────────────────────────────────────────────────

@router.post("/{job_id}/confirm")
async def confirm_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirm job preview → generate all content via GPT/DALL-E → set SCHEDULED.
    SSE events:
      step: {step: "generating", message: ..., current: int, total: int}
      step: {step: "complete", message: "All content generated!"}
      done: {job_id: int, status: "SCHEDULED"}
      error: {message: str}
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DRAFT:
        raise HTTPException(status_code=400, detail=f"Job is {job.status}, not DRAFT")

    async def event_stream() -> AsyncGenerator[str, None]:
        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

        try:
            config = ParsedConfig(**job.parsed_config)
            posts = sorted(job.posts, key=lambda x: x.scheduled_time)
            total = len(posts)

            yield sse("step", {
                "step": "generating",
                "message": "Generating content...",
                "current": 0,
                "total": total,
            })

            slots = [
                {
                    "day_index": p.day_index,
                    "post_order": p.post_order,
                    "image_url": p.image_url,
                    "image_prompt": p.image_prompt,
                }
                for p in posts
            ]

            progress_queue: asyncio.Queue = asyncio.Queue()

            async def run_generation():
                def on_progress(current: int, total_: int):
                    progress_queue.put_nowait((current, total_))
                results = await generate_all_content(config, slots, on_progress=on_progress)
                progress_queue.put_nowait(None)  # sentinel
                return results

            gen_task = asyncio.create_task(run_generation())

            while True:
                try:
                    item = await asyncio.wait_for(progress_queue.get(), timeout=60.0)
                    if item is None:
                        break
                    current, total_ = item
                    yield sse("step", {
                        "step": "generating",
                        "message": f"Generating post {current} of {total_}...",
                        "current": current,
                        "total": total_,
                    })
                except asyncio.TimeoutError:
                    yield sse("error", {"message": "Generation timed out"})
                    gen_task.cancel()
                    return

            results = await gen_task

            for post, result in zip(posts, results):
                post.content_text = result["content_text"]
                post.image_url = result.get("image_url")
                post.image_prompt = result.get("image_prompt")

            job.status = JobStatus.SCHEDULED
            db.commit()

            yield sse("step", {"step": "complete", "message": "All content generated!"})
            yield sse("done", {"job_id": job.id, "status": "SCHEDULED"})

        except Exception as e:
            yield sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── GET /jobs/ ─────────────────────────────────────────────────────────────

@router.get("/", response_model=List[JobListOut])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(Job)
        .filter(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    result = []
    for job in jobs:
        counts = _compute_counts(job.id, db)
        result.append(JobListOut(
            id=job.id,
            title=job.title,
            status=job.status,
            created_at=job.created_at,
            **counts,
        ))
    return result


# ── GET /jobs/{id} ─────────────────────────────────────────────────────────

@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── POST /jobs/{id}/pause ──────────────────────────────────────────────────

@router.post("/{job_id}/pause", response_model=JobOut)
def pause_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.RUNNING, JobStatus.SCHEDULED):
        raise HTTPException(status_code=400, detail=f"Cannot pause job with status {job.status}")
    job.status = JobStatus.PAUSED
    db.commit()
    db.refresh(job)
    return job


# ── POST /jobs/{id}/resume ─────────────────────────────────────────────────

@router.post("/{job_id}/resume", response_model=JobOut)
def resume_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Job is not PAUSED")
    job.status = JobStatus.SCHEDULED
    db.commit()
    db.refresh(job)
    return job


# ── DELETE /jobs/{id} ──────────────────────────────────────────────────────

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT jobs can be deleted")
    db.query(JobPost).filter(JobPost.job_id == job_id).delete()
    db.delete(job)
    db.commit()


# ── PUT /jobs/{id}/posts/{post_id} ─────────────────────────────────────────

@router.put("/{job_id}/posts/{post_id}", response_model=JobPostOut)
def update_post(
    job_id: int,
    post_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow user to edit content_text of a single post before confirming."""
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    post = db.query(JobPost).filter(JobPost.id == post_id, JobPost.job_id == job_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if "content_text" in body:
        post.content_text = str(body["content_text"])
    db.commit()
    db.refresh(post)
    return post
