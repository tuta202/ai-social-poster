"""
Facebook Graph API poster.
Handles text-only and text+image posts to a Facebook Page.
"""
import httpx
from typing import Optional
from app.models.models import FacebookPage

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


async def post_to_facebook(
    page: FacebookPage,
    message: str,
    image_url: Optional[str] = None,
) -> str:
    """
    Post content to Facebook Page.
    Returns fb_post_id on success.
    Raises Exception with descriptive message on failure.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        if image_url:
            return await _post_with_image(client, page, message, image_url)
        else:
            return await _post_text_only(client, page, message)


async def _post_text_only(
    client: httpx.AsyncClient,
    page: FacebookPage,
    message: str,
) -> str:
    """POST to /PAGE_ID/feed"""
    url = f"{GRAPH_API_BASE}/{page.page_id}/feed"
    payload = {
        "message": message,
        "access_token": page.access_token,
    }
    response = await client.post(url, data=payload)
    return _handle_response(response)


async def _post_with_image(
    client: httpx.AsyncClient,
    page: FacebookPage,
    message: str,
    image_url: str,
) -> str:
    """
    POST to /PAGE_ID/photos — uploads image from URL and attaches caption.
    Facebook will fetch the image from the URL directly.
    """
    url = f"{GRAPH_API_BASE}/{page.page_id}/photos"
    payload = {
        "caption": message,
        "url": image_url,
        "access_token": page.access_token,
    }
    response = await client.post(url, data=payload)
    return _handle_response(response)


def _handle_response(response: httpx.Response) -> str:
    """Parse Graph API response. Returns post ID or raises."""
    try:
        data = response.json()
    except Exception:
        raise Exception(f"Facebook API returned non-JSON: {response.text[:200]}")

    if "error" in data:
        err = data["error"]
        code = err.get("code", "unknown")
        msg = err.get("message", "Unknown error")
        raise Exception(f"Facebook API error {code}: {msg}")

    # Text post returns {"id": "PAGE_ID_POST_ID"}
    # Photo post returns {"post_id": "...", "id": "..."}
    post_id = data.get("post_id") or data.get("id")
    if not post_id:
        raise Exception(f"Facebook API: no post ID in response: {data}")

    return str(post_id)


async def exchange_for_long_lived_token(
    short_lived_token: str,
    app_id: str,
    app_secret: str,
) -> str:
    """
    Exchange short-lived user token for long-lived user token (60 days).
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": short_lived_token,
            },
        )
        data = response.json()
        if "error" in data:
            raise Exception(f"Token exchange failed: {data['error'].get('message')}")
        return data["access_token"]


async def get_page_token(long_lived_user_token: str, page_id: str) -> str:
    """
    Get permanent Page Access Token from long-lived User token.
    Page tokens from long-lived user tokens do NOT expire.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": long_lived_user_token},
        )
        data = response.json()
        if "error" in data:
            raise Exception(f"Get page token failed: {data['error'].get('message')}")

        pages = data.get("data", [])
        for page in pages:
            if page["id"] == page_id:
                return page["access_token"]

        raise Exception(
            f"Page {page_id} not found in user's pages. "
            f"Available: {[p['id'] for p in pages]}"
        )


async def get_page_info(page_token: str, page_id: str) -> dict:
    """Get page name and basic info."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={
                "fields": "id,name",
                "access_token": page_token,
            },
        )
        data = response.json()
        if "error" in data:
            raise Exception(f"Get page info failed: {data['error'].get('message')}")
        return data
