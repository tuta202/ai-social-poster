"""
Manual smoke test for content generator.
Run: python test_content_gen.py
Requires OPENAI_API_KEY in .env
"""
import asyncio
from app.schemas.schemas import ParsedConfig
from app.services.content_gen import generate_text, generate_image, generate_all_content
from app.services.plan_generator import generate_schedule


async def test_text_gen():
    print("=== Test 1: Text Generation ===")
    config = ParsedConfig(
        title="Learn JLPT N2 Vocabulary",
        duration_days=3,
        items_per_day=1,
        post_time="08:00",
        content_type="vocabulary",
        has_images=False,
        tags=["N2", "JLPT", "Japanese"],
        notes="Focus on common verbs used in business settings",
    )
    text = await generate_text(config, day_index=1, post_order=1)
    print(f"Generated text:\n{text}\n")
    assert len(text) > 20, "Text too short"
    assert not text.startswith("[Content for"), "Fallback triggered -- check API key"
    print("PASS\n")


async def test_image_gen():
    print("=== Test 2: Image Generation ===")
    config = ParsedConfig(
        title="Daily Motivation",
        duration_days=5,
        items_per_day=1,
        post_time="08:00",
        content_type="motivation",
        has_images=True,
        tags=["motivation"],
        notes="Inspiring messages for language learners",
    )
    url, prompt = await generate_image(config, day_index=1)
    print(f"Image URL: {url}")
    print(f"Prompt used: {prompt[:100]}...")
    assert url is not None, "Image URL is None -- check API key or DALL-E quota"
    assert url.startswith("https://"), "URL format invalid"
    print("PASS\n")


async def test_batch_gen():
    print("=== Test 3: Batch Generation (2 days x 1 post, no images) ===")
    config = ParsedConfig(
        title="Test Campaign",
        duration_days=2,
        items_per_day=1,
        post_time="08:00",
        content_type="motivation",
        has_images=False,
        tags=["test"],
        notes="Short test posts",
    )
    slots = generate_schedule(config, job_id=999)
    assert len(slots) == 2

    results = await generate_all_content(
        config,
        slots,
        on_progress=lambda cur, tot: print(f"  Progress: {cur}/{tot}"),
    )
    assert len(results) == 2
    for r in results:
        assert r["content_text"], f"Empty content for day {r['day_index']}"
        assert r["image_url"] is None  # has_images=False
    print("All 2 posts generated")
    print("PASS\n")


async def test_fallback():
    print("=== Test 4: Fallback on invalid API key ===")
    from app.services import content_gen as cg
    original_client = cg.client

    from openai import AsyncOpenAI
    cg.client = AsyncOpenAI(api_key="sk-invalid-key-for-testing")

    config = ParsedConfig(
        title="Fallback Test",
        duration_days=1,
        items_per_day=1,
        post_time="08:00",
        content_type="custom",
        has_images=False,
        tags=[],
        notes="",
    )
    text = await generate_text(config, day_index=1, post_order=1, max_retries=0)
    print(f"Fallback text: {text}")
    assert "[Content for" in text, f"Expected fallback string, got: {text}"

    cg.client = original_client
    print("PASS\n")


if __name__ == "__main__":
    async def main():
        await test_text_gen()
        await test_batch_gen()
        await test_fallback()
        # Uncomment to test image gen (costs ~$0.04):
        # await test_image_gen()
        print("All tests passed!")

    asyncio.run(main())
