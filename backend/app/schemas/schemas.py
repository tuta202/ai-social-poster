from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import JobStatus, PostStatus


# ── Auth ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Facebook ──────────────────────────────────────────
class FacebookTokenSetup(BaseModel):
    short_lived_token: str
    page_id: str


class FacebookPageOut(BaseModel):
    page_id: str
    page_name: Optional[str]
    token_expires_at: Optional[datetime]
    model_config = {"from_attributes": True}


# ── Jobs ──────────────────────────────────────────────
class ParseJobRequest(BaseModel):
    raw_input: str = Field(..., min_length=10, max_length=2000)


class ParsedConfig(BaseModel):
    title: str
    duration_days: int
    items_per_day: int
    post_time: str
    content_type: str
    has_images: bool
    image_description: str = ""
    tags: List[str] = []
    notes: str = ""


class JobPostOut(BaseModel):
    id: int
    job_id: int
    day_index: int
    post_order: int
    content_text: Optional[str]
    original_content_text: Optional[str]
    image_url: Optional[str]
    image_prompt: Optional[str]
    image_style_note: Optional[str] = None
    scheduled_time: datetime
    status: PostStatus
    fb_post_id: Optional[str]
    error_message: Optional[str]
    posted_at: Optional[datetime]
    approved_at: Optional[datetime]
    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    title: str
    raw_input: str
    parsed_config: Optional[dict]
    status: JobStatus
    style_profile: Optional[dict]
    created_at: datetime
    updated_at: Optional[datetime]
    posts: List[JobPostOut] = []
    model_config = {"from_attributes": True}


class ApprovePostRequest(BaseModel):
    image_style_note: Optional[str] = None


class RegenerateImageRequest(BaseModel):
    image_style_note: Optional[str] = None


class JobPreviewResponse(BaseModel):
    job_id: int
    config: ParsedConfig
    posts: List[JobPostOut]


class JobListOut(BaseModel):
    id: int
    title: str
    status: JobStatus
    created_at: datetime
    total_posts: int
    posted_count: int
    failed_count: int
    model_config = {"from_attributes": True}
