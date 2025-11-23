"""Bulk HTTP fetch test using backend.utils.search_utils.http_get_text.

Run with `python tests/http_fetch_bulk_test.py` from project root.
"""
import asyncio
import sys
import os

# Ensure project root on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.search_utils import http_get_text


URLS = [
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/403",
    "https://example.com/",
    "https://www.wikipedia.org/",
    "https://en.wikipedia.org/wiki/Computer_science",
    "https://www.google.com/",
    "https://www.bbc.com/",
    "https://www.github.com/",
]


async def fetch_one(url: str):
    try:
        text = await http_get_text(url, timeout=10, retries=1)
        length = len(text or "")
        print(f"[OK] {url} -> {length} bytes")
    except Exception as e:
        # Print exception type and short message
        tname = type(e).__name__
        msg = str(e)
        print(f"[ERROR] {url} -> {tname}: {msg[:300]}")


async def main():
    print("Starting bulk fetch test...")
    for url in URLS:
        await fetch_one(url)


if __name__ == '__main__':
    asyncio.run(main())
