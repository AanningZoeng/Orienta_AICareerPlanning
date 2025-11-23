"""LLM helper utilities.

Provides a thin wrapper that enforces a safe `max_tokens` value on
calls that submit requests to underlying providers. This helps when
an SDK does not persist/validate the passed `max_tokens` at
construction time but the provider rejects requests with an
invalid value at call time.

The wrapper delegates all attributes to the original ChatBot but
intercepts callables named like common chat methods (e.g.:
`chat_with_tools`, `chat`, `call`, `run`) and ensures `max_tokens`
is set to a provider-safe integer.
"""
from typing import Any, Callable
from spoon_ai.chat import ChatBot


class TokenEnforcingChatBot(ChatBot):
    """Wrap a ChatBot-like object and enforce `max_tokens` on calls.

    Usage:
        wrapped = TokenEnforcingChatBot(original_llm, safe_max_tokens)

    The wrapper will attempt to inject `max_tokens` into keyword
    arguments of callables. If the callable already provides a
    `max_tokens` value, the wrapper will leave it as-is.
    """

    def __init__(self, inner: Any, safe_max_tokens: int):
        # Do NOT call ChatBot.__init__ - we are a thin subclass wrapper
        # that delegates to an existing ChatBot instance (`inner`).
        # Subclassing ensures isinstance(..., ChatBot) checks pass
        # (pydantic validation in SpoonReactAI requires that).
        self._inner = inner
        self._safe_max_tokens = int(safe_max_tokens or 1)

    def _wrap_callable(self, fn: Callable) -> Callable:
        def _wrapper(*args, **kwargs):
            # If max_tokens missing or invalid, set to safe value
            try:
                mt = kwargs.get('max_tokens', None)
                if mt is None:
                    kwargs['max_tokens'] = self._safe_max_tokens
                else:
                    # coerce to int and clamp
                    try:
                        mt_int = int(mt)
                    except Exception:
                        mt_int = self._safe_max_tokens
                    if mt_int < 1 or mt_int > self._safe_max_tokens:
                        # clamp into [1, safe_max_tokens]
                        mt_int = max(1, min(mt_int, self._safe_max_tokens))
                    kwargs['max_tokens'] = mt_int
            except Exception:
                # defensive: if anything goes wrong, still call with safe value
                kwargs['max_tokens'] = self._safe_max_tokens

            return fn(*args, **kwargs)

        return _wrapper

    def __getattr__(self, name: str) -> Any:
        # delegate everything to the inner object; wrap callables that
        # look like chat/call functions so we can enforce tokens
        attr = getattr(self._inner, name)
        if callable(attr) and name in ("chat_with_tools", "chat", "call", "run", "send"):
            return self._wrap_callable(attr)
        return attr

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<TokenEnforcingChatBot inner={repr(self._inner)} safe_max_tokens={self._safe_max_tokens}>"
