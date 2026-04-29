"""
Manual smoke test for NLU parser.
Run while uvicorn is NOT needed (pure async test):
  python test_nlu.py
Requires OPENAI_API_KEY in .env
"""
import asyncio
from app.services.nlu_parser import parse_command

TEST_CASES = [
    (
        "Tao kich ban hoc tu vung N2 trong 10 ngay, moi ngay 10 tu, co anh",
        {"duration_days": 10, "items_per_day": 10, "has_images": True, "content_type": "vocabulary"},
    ),
    (
        "Create 7 motivational posts about learning Japanese, post at 8pm",
        {"duration_days": 7, "post_time": "20:00", "content_type": "motivation"},
    ),
    (
        "Schedule 5 lifestyle posts with images every morning for 2 weeks",
        {"duration_days": 14, "has_images": True, "post_time": "08:00", "content_type": "lifestyle"},
    ),
    (
        "lam 3 bai",
        {"duration_days": 3},
    ),
]


async def main():
    print("Testing NLU Parser...\n")
    for i, (input_text, checks) in enumerate(TEST_CASES, 1):
        print(f"Test {i}: {input_text[:60]}...")
        result = await parse_command(input_text)
        print(f"  -> title: {result.title}")
        print(f"  -> duration_days: {result.duration_days}, items_per_day: {result.items_per_day}")
        print(f"  -> post_time: {result.post_time}, content_type: {result.content_type}")
        print(f"  -> has_images: {result.has_images}, tags: {result.tags}")

        passed = True
        for key, expected in checks.items():
            actual = getattr(result, key)
            if actual != expected:
                print(f"  FAIL: {key} expected={expected}, got={actual}")
                passed = False
        if passed:
            print(f"  PASS\n")
        else:
            print()


if __name__ == "__main__":
    asyncio.run(main())
