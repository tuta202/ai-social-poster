"""
Smoke test for AI provider abstraction.
Run: python test_providers.py
Tests 1-4 require no API key. Tests 5-7 need OPENAI_API_KEY / GEMINI_API_KEY.
"""
import asyncio
import json as json_lib
from app.services.ai.factory import get_text_provider, get_image_provider, reset_providers
from app.core.config import settings


async def test_factory_openai():
    print("=== Test 1: Factory returns OpenAI provider ===")
    reset_providers()
    original = settings.AI_TEXT_PROVIDER
    settings.AI_TEXT_PROVIDER = "openai"

    try:
        provider = get_text_provider()
        from app.services.ai.openai_provider import OpenAITextProvider
        assert isinstance(provider, OpenAITextProvider), f"Expected OpenAI, got {type(provider)}"
        print("PASS: get_text_provider() returns OpenAITextProvider\n")
    finally:
        settings.AI_TEXT_PROVIDER = original
        reset_providers()


async def test_factory_gemini():
    print("=== Test 2: Factory returns Gemini provider ===")
    reset_providers()
    original_provider = settings.AI_TEXT_PROVIDER
    original_key = settings.GEMINI_API_KEY
    settings.AI_TEXT_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "fake-key-for-type-check"

    try:
        provider = get_text_provider()
        from app.services.ai.gemini_provider import GeminiTextProvider
        assert isinstance(provider, GeminiTextProvider), f"Expected Gemini, got {type(provider)}"
        print("PASS: get_text_provider() returns GeminiTextProvider\n")
    finally:
        settings.AI_TEXT_PROVIDER = original_provider
        settings.GEMINI_API_KEY = original_key
        reset_providers()


async def test_factory_unknown_provider():
    print("=== Test 3: Unknown provider raises ValueError ===")
    reset_providers()
    original = settings.AI_TEXT_PROVIDER
    settings.AI_TEXT_PROVIDER = "anthropic"

    try:
        try:
            get_text_provider()
            print("FAIL: Should have raised ValueError")
        except ValueError as e:
            assert "anthropic" in str(e).lower() or "unknown" in str(e).lower()
            print(f"PASS: ValueError raised correctly: {e}\n")
    finally:
        settings.AI_TEXT_PROVIDER = original
        reset_providers()


async def test_singleton():
    print("=== Test 4: Provider is singleton ===")
    reset_providers()
    p1 = get_text_provider()
    p2 = get_text_provider()
    assert p1 is p2, "Provider should be singleton"
    print("PASS: Same instance returned on second call\n")
    reset_providers()


async def test_openai_completion():
    print("=== Test 5: OpenAI completion (live) ===")
    if not settings.OPENAI_API_KEY:
        print("SKIP: OPENAI_API_KEY not set\n")
        return

    reset_providers()
    settings.AI_TEXT_PROVIDER = "openai"
    provider = get_text_provider()

    result = await provider.complete(
        system="You are a helpful assistant. Reply in one sentence.",
        user="Say hello in Vietnamese.",
        model=settings.AI_TEXT_MODEL,
        temperature=0.5,
        max_tokens=50,
    )
    print(f"Response: {result}")
    assert len(result) > 5
    print("PASS\n")
    reset_providers()


async def test_gemini_completion():
    print("=== Test 6: Gemini completion (live) ===")
    if not settings.GEMINI_API_KEY:
        print("SKIP: GEMINI_API_KEY not set\n")
        return

    reset_providers()
    settings.AI_TEXT_PROVIDER = "gemini"
    provider = get_text_provider()

    result = await provider.complete(
        system="You are a helpful assistant. Reply in one sentence.",
        user="Say hello in Vietnamese.",
        model=settings.AI_TEXT_MODEL,
        temperature=0.5,
        max_tokens=50,
    )
    print(f"Response: {result}")
    assert len(result) > 5
    print("PASS\n")
    reset_providers()


async def test_gemini_json_mode():
    print("=== Test 7: Gemini JSON mode ===")
    if not settings.GEMINI_API_KEY:
        print("SKIP: GEMINI_API_KEY not set\n")
        return

    reset_providers()
    settings.AI_TEXT_PROVIDER = "gemini"
    provider = get_text_provider()

    result = await provider.complete(
        system='Return ONLY valid JSON: {"greeting": "hello in Vietnamese"}',
        user="Give me the greeting.",
        model=settings.AI_MINI_MODEL,
        temperature=0.1,
        max_tokens=100,
        json_mode=True,
    )
    print(f"Raw result: {result}")
    parsed = json_lib.loads(result)
    assert "greeting" in parsed
    print(f"PASS: JSON parsed correctly: {parsed}\n")
    reset_providers()


if __name__ == "__main__":
    async def main():
        await test_factory_openai()
        await test_factory_gemini()
        await test_factory_unknown_provider()
        await test_singleton()
        await test_openai_completion()
        await test_gemini_completion()
        await test_gemini_json_mode()
        print("All provider tests done!")

    asyncio.run(main())
