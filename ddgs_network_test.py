#!/usr/bin/env python3
"""Simple test for DuckDuckGo packages and network connectivity.

Checks for:
- `ddgs.DDGS` (preferred) or `duckduckgo_search.ddg` fallback
- HTTP connectivity to https://duckduckgo.com using `httpx`

Usage:
    python ddgs_network_test.py --query "python programming" --max 3
"""
import sys
import argparse
import traceback


def test_ddgs(query: str, max_results: int) -> bool:
    """Try ddgs.DDGS then duckduckgo_search.ddg and print results."""
    try:
        from ddgs import DDGS
        print("[INFO] Using ddgs.DDGS")
        try:
            with DDGS() as ddgs:
                # DDGS.text has differing signatures across versions; try common ones
                try:
                    it = ddgs.text(query, max_results=max_results)
                except TypeError:
                    try:
                        it = ddgs.text(query=query, max_results=max_results)
                    except TypeError:
                        try:
                            it = ddgs.text(keywords=query, max_results=max_results)
                        except Exception:
                            raise
                results = list(it)
                print(f"[ddgs] results: {len(results)}")
                for i, r in enumerate(results[:5], 1):
                    print(i, r)
                return True
        except Exception as e:
            print("[ddgs] runtime error:", e)
            traceback.print_exc()
    except Exception as e:
        print("[INFO] ddgs package not available or import failed:", e)

    # Fallback to duckduckgo_search
    try:
        from duckduckgo_search import ddg
        print("[INFO] Using duckduckgo_search.ddg")
        try:
            res = ddg(query, max_results=max_results) or []
            print(f"[duckduckgo_search] results: {len(res)}")
            for i, r in enumerate(res[:5], 1):
                print(i, r)
            return True
        except Exception as e:
            print("[duckduckgo_search] runtime error:", e)
            traceback.print_exc()
    except Exception as e:
        print("[INFO] duckduckgo_search not available or import failed:", e)

    return False


def test_http() -> bool:
    """Simple httpx GET to duckduckgo.com to validate network reachability."""
    try:
        import httpx
    except Exception as e:
        print("[httpx] httpx not installed:", e)
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://duckduckgo.com/"
    }

    try:
        r = httpx.get("https://duckduckgo.com", headers=headers, timeout=10.0)
        print(f"[httpx] duckduckgo.com status: {r.status_code}")
        if r.status_code == 200:
            print(f"[httpx] fetched {len(r.text)} bytes")
            return True
        else:
            return False
    except Exception as e:
        print("[httpx] fetch failed:", e)
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", default="python programming")
    parser.add_argument("--max", "-m", type=int, default=3)
    args = parser.parse_args()

    print("== ddgs / duckduckgo connectivity test ==")
    ok_search = test_ddgs(args.query, args.max)
    print()
    print("== httpx network test ==")
    ok_http = test_http()

    if ok_search and ok_http:
        print("\nRESULT: OK - search package and network reachable")
        sys.exit(0)
    else:
        print("\nRESULT: FAIL - check dependencies or network (see above)")
        sys.exit(2)


if __name__ == "__main__":
    main()
