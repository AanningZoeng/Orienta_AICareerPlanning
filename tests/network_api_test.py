"""Simple integration tests for network and API helpers.

Run this script with `python tests/network_api_test.py` from the
project root. It does two checks:

- `http_get_text` against httpbin endpoints to ensure success and
  expected failure handling (403).
- `/api/analyze` endpoint via Flask `test_client` to ensure the
  API route is wired and returns JSON (mock or real orchestrator).

This script is intentionally lightweight and does not require
third-party test frameworks.
"""
import asyncio
import sys
import os
import json

# Ensure project root is on sys.path so `backend` package imports work when
# running this script directly from the project root.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.utils.search_utils import http_get_text


async def test_http_get_text():
    ok_url = "https://httpbin.org/status/200"
    forbidden_url = "https://httpbin.org/status/403"

    print("[NetworkTest] http_get_text success case...", end=" ")
    try:
        text = await http_get_text(ok_url, timeout=10, retries=1)
        print("OK (received {} bytes)".format(len(text or "")))
    except Exception as e:
        print("FAIL")
        print("  error:", e)
        return False

    print("[NetworkTest] http_get_text 403 case (expect exception)...", end=" ")
    try:
        await http_get_text(forbidden_url, timeout=10, retries=1)
        print("FAIL - expected exception but call succeeded")
        return False
    except Exception as e:
        print("OK (caught exception)")
        print("  exception:", type(e).__name__, str(e)[:200])

    return True


def test_api_analyze():
    print("[API] POST /api/analyze test...", end=" ")
    try:
        # Import the Flask app directly and use test_client
        from backend.api import server as srv

        client = srv.app.test_client()
        resp = client.post('/api/analyze', json={"query": "test query"})
        if resp.status_code != 200:
            print("FAIL - status", resp.status_code)
            print("  body:", resp.get_data(as_text=True)[:400])
            return False

        data = resp.get_json()
        # Basic sanity checks
        if not isinstance(data, dict) or 'majors' not in data and 'recommended_majors' not in data:
            print("FAIL - unexpected JSON structure")
            print("  json:", json.dumps(data)[:400])
            return False

        print("OK")
        return True
    except Exception as e:
        print("FAIL - exception:", type(e).__name__, str(e))
        return False


def main():
    ok = True
    ok &= asyncio.run(test_http_get_text())
    ok &= test_api_analyze()

    if ok:
        print("\nAll tests passed.")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(2)


if __name__ == '__main__':
    main()
