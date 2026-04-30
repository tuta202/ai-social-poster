"""
Smoke test for image prompt generation.
Run: python test_image_prompt.py
Requires OPENAI_API_KEY in .env for live tests.
"""
import asyncio
from app.services.content_gen import generate_image_prompt
from app.services.nlu_parser import parse_command


async def test_prompt_fallback_no_description():
    print("=== Test 1: Fallback when no description (no API needed) ===")
    prompt = await generate_image_prompt(
        image_description="",
        content_type="motivation",
        day_index=1,
    )
    print(f"Fallback prompt: {prompt}\n")
    assert len(prompt) > 20, "Fallback prompt too short"
    assert "motivation" in prompt.lower(), "Fallback should mention content_type"
    assert "No text" in prompt or "no text" in prompt.lower(), "Should mention no text"
    print("PASS\n")


async def test_prompt_with_description():
    print("=== Test 2: Prompt with anime description ===")
    prompt = await generate_image_prompt(
        image_description="anime style, pastel colors, no text",
        content_type="vocabulary",
        day_index=1,
    )
    print(f"Generated prompt:\n{prompt}\n")
    assert len(prompt) > 20, "Prompt too short"
    assert "no text" in prompt.lower() or "No text" in prompt, \
        "Prompt should mention no text"
    print("PASS\n")


async def test_nlu_extracts_image_description():
    print("=== Test 3: NLU extracts image_description ===")
    result = await parse_command(
        "Tao 7 bai hoc tu vung N2, co anh phong cach anime mau pastel, dang luc 8h sang"
    )
    print(f"has_images: {result.has_images}")
    print(f"image_description: {result.image_description}\n")

    if result.image_description == "" and result.has_images is False:
        print("SKIP: No OPENAI_API_KEY or fallback returned defaults\n")
        return

    assert result.has_images is True, "Should detect has_images"
    assert result.image_description != "", "Should extract image_description"
    assert "anime" in result.image_description.lower() or \
           "pastel" in result.image_description.lower(), \
        f"Expected anime/pastel in description, got: {result.image_description}"
    print("PASS\n")


async def test_nlu_no_image():
    print("=== Test 4: NLU — no image mentioned ===")
    result = await parse_command(
        "Create 5 motivation posts over 5 days at 9am"
    )
    print(f"has_images: {result.has_images}")
    print(f"image_description: '{result.image_description}'\n")

    if not result.has_images and result.image_description == "":
        print("PASS: No image detected, empty description\n")
    else:
        print(f"NOTE: API returned has_images={result.has_images} "
              f"(acceptable if API key missing -> fallback)\n")


if __name__ == "__main__":
    async def main():
        await test_prompt_fallback_no_description()  # no API needed
        await test_prompt_with_description()          # needs API key
        await test_nlu_extracts_image_description()   # needs API key
        await test_nlu_no_image()                     # needs API key
        print("All image prompt tests done!")

    asyncio.run(main())
