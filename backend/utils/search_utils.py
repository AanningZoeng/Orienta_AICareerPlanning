ddg = None
DDGS = None
try:
    # prefer the renamed package 'ddgs' if installed
    from ddgs import DDGS as _DDGS
    DDGS = _DDGS
except Exception:
    DDGS = None

try:
    # fall back to duckduckgo_search function-based API
    # try to import the module and resolve a usable function dynamically
    import duckduckgo_search as _ddg_mod
    _ddg_func = None
    # common possible entrypoints across versions
    for fname in ("ddg", "search", "ddg_answers", "DuckDuckGo", "ddgs", "query"):
        if hasattr(_ddg_mod, fname):
            _ddg_func = getattr(_ddg_mod, fname)
            break
    # if still None, expose the module for manual use
    if _ddg_func is not None:
        ddg = _ddg_func
    else:
        ddg = _ddg_mod
except Exception:
    ddg = None

def safe_ddg(query: str, max_results: int = 6):
    # Try class-based DDGS first
    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                # DDGS.text may accept different signatures across versions
                try:
                    it = ddgs.text(query, max_results=max_results)
                except TypeError:
                    try:
                        it = ddgs.text(query=query, max_results=max_results)
                    except TypeError:
                        try:
                            it = ddgs.text(keywords=query, max_results=max_results)
                        except Exception:
                            # Last resort: call with single positional arg
                            it = ddgs.text(query)
                res = list(it)
                return res or []
        except Exception:
            pass

    # Then try function-style ddg
    if ddg is not None:
        try:
            # If ddg is a callable function, prefer calling with keyword arg
            if callable(ddg):
                try:
                    return ddg(query, max_results=max_results) or []
                except TypeError:
                    # some versions expect positional max_results
                    try:
                        return ddg(query, max_results) or []
                    except Exception:
                        return ddg(query) or []
            else:
                # ddg might be the module object; try common callables on it
                for fname in ("ddg", "search", "ddg_answers", "query"):
                    fn = getattr(ddg, fname, None)
                    if callable(fn):
                        try:
                            return fn(query, max_results=max_results) or []
                        except TypeError:
                            try:
                                return fn(query, max_results) or []
                            except Exception:
                                return fn(query) or []
        except Exception:
            pass

    return []


async def http_get_text(url: str, timeout: int = 10, retries: int = 2) -> str:
    """Fetch page text with a browser-like User-Agent and simple retry logic.

    This helper is async and intended for use throughout the agents when fetching
    web pages. It centralizes headers and retry behavior to reduce 403s.
    """
    try:
        import httpx
    except Exception:
        raise RuntimeError("httpx is required for http_get_text but is not installed")

    import random

    # A short list of realistic desktop User-Agents to vary requests
    ua_choices = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    ]

    headers = {
        "User-Agent": random.choice(ua_choices),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    last_exc = None
    # Use exponential backoff
    for attempt in range(max(0, retries) + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                # follow redirects to handle sites that redirect (e.g., github.com -> github.com)
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                return resp.text
        except Exception as e:
            last_exc = e
            # backoff with jitter
            import asyncio, math
            backoff = min(2 ** attempt, 8) + random.random() * 0.5
            await asyncio.sleep(backoff)
            continue

    raise last_exc