"""
Facebook token setup endpoints.
Flow: user pastes short-lived token → system exchanges for long-lived → gets page token → saves.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.models import User, FacebookPage
from app.schemas.schemas import FacebookTokenSetup, FacebookPageOut
from app.services.fb_poster import (
    exchange_for_long_lived_token,
    get_page_token,
    get_page_info,
)

router = APIRouter()


@router.post("/setup-token", response_model=FacebookPageOut)
async def setup_facebook_token(
    body: FacebookTokenSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Setup Facebook Page integration.
    body.short_lived_token: short-lived User access token from Graph API Explorer
    body.page_id: the Facebook Page ID to post to

    Flow:
    1. Exchange short-lived → long-lived user token
    2. Get permanent page token from long-lived token
    3. Fetch page name
    4. Save/update in DB
    """
    try:
        long_lived_user_token = await exchange_for_long_lived_token(
            short_lived_token=body.short_lived_token,
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
        )

        page_token = await get_page_token(long_lived_user_token, body.page_id)

        page_info = await get_page_info(page_token, body.page_id)
        page_name = page_info.get("name", "")

        existing = (
            db.query(FacebookPage)
            .filter(FacebookPage.user_id == current_user.id)
            .first()
        )
        if existing:
            existing.page_id = body.page_id
            existing.page_name = page_name
            existing.access_token = page_token
            existing.token_expires_at = None
            fb_page = existing
        else:
            fb_page = FacebookPage(
                user_id=current_user.id,
                page_id=body.page_id,
                page_name=page_name,
                access_token=page_token,
                token_expires_at=None,
            )
            db.add(fb_page)

        db.commit()
        db.refresh(fb_page)
        return fb_page

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/page", response_model=FacebookPageOut)
def get_facebook_page(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the configured Facebook page for current user."""
    page = (
        db.query(FacebookPage)
        .filter(FacebookPage.user_id == current_user.id)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="No Facebook page configured")
    return page


@router.delete("/page", status_code=204)
def remove_facebook_page(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove Facebook page integration."""
    page = (
        db.query(FacebookPage)
        .filter(FacebookPage.user_id == current_user.id)
        .first()
    )
    if page:
        db.delete(page)
        db.commit()
