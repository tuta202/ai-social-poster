from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    PAUSED = "PAUSED"


class PostStatus(str, enum.Enum):
    PENDING  = "PENDING"
    APPROVED = "APPROVED"
    POSTED   = "POSTED"
    FAILED   = "FAILED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobs = relationship("Job", back_populates="owner")
    fb_page = relationship("FacebookPage", back_populates="owner", uselist=False)


class FacebookPage(Base):
    __tablename__ = "facebook_pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    page_id = Column(String(100), nullable=False)
    page_name = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="fb_page")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    raw_input = Column(Text, nullable=False)
    parsed_config = Column(JSON, nullable=True)
    status = Column(SAEnum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    style_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="jobs")
    posts = relationship("JobPost", back_populates="job", order_by="JobPost.scheduled_time")


class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    day_index = Column(Integer, nullable=False)
    post_order = Column(Integer, default=1)
    content_text = Column(Text, nullable=True)
    original_content_text = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SAEnum(PostStatus), default=PostStatus.PENDING, nullable=False)
    fb_post_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("Job", back_populates="posts")
