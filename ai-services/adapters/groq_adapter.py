"""
COGNARC — Groq API Adapter
ai-services/adapters/groq_adapter.py

T2.1: Direct Groq SDK client — raw HTTP call only.
T2.2: Round-robin rotation across GROQ_API_KEYS.
T2.3: httpx.Timeout(connect=5.0, read=15.0) wrapper.
T2.4: Langfuse trace logging per call (tokens_in, tokens_out, latency_ms, success).

§07: NO LangChain, NO LangGraph. Raw Groq SDK only.
§16: All keys loaded from env vars — never hardcoded.
§16: Groq failure logged but never fatal — caller handles fallback.

Retries: max 2 attempts via tenacity (covers transient 429 / 5xx).
"""
from __future__ import annotations

import itertools
import logging
import os
import time
from typing import Iterator, Optional

import httpx
from groq import Groq
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("ai_services.groq_adapter")

# ── Constants ─────────────────────────────────────────────────

_DEFAULT_MODEL = "mixtral-8x7b-32768"
_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

# XP / difficulty constraints
_MAX_TOKENS = 1500
_TEMPERATURE = 0.7


# ── Key Rotation ──────────────────────────────────────────────


def _load_api_keys() -> list[str]:
    """
    T2.2: Load comma-separated keys from GROQ_API_KEYS.
    Falls back to GROQ_API_KEY for single-key setups.
    Raises RuntimeError if no key is configured.
    §16: Never log key values.
    """
    multi = os.environ.get("GROQ_API_KEYS", "").strip()
    if multi:
        keys = [k.strip() for k in multi.split(",") if k.strip()]
        if keys:
            return keys

    single = os.environ.get("GROQ_API_KEY", "").strip()
    if single:
        return [single]

    raise RuntimeError(
        "No Groq API key configured. Set GROQ_API_KEY or GROQ_API_KEYS env var."
    )


class _KeyRotator:
    """Stateless round-robin iterator over API keys — thread-safe for single process."""

    def __init__(self, keys: list[str]) -> None:
        self._cycle: Iterator[str] = itertools.cycle(keys)
        self._count = len(keys)

    def next(self) -> str:
        return next(self._cycle)

    @property
    def key_count(self) -> int:
        return self._count


# ── Langfuse Tracer ───────────────────────────────────────────


class _LangfuseTracer:
    """
    T2.4: Lightweight Langfuse trace wrapper.
    No-op if Langfuse is not configured — never blocks quest generation.
    §19: Log tokens_in, tokens_out, latency_ms, success per call.
    """

    def __init__(self) -> None:
        self._client: Optional[object] = None
        self._enabled = False
        self._init()

    def _init(self) -> None:
        pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
        host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not (pk and sk):
            logger.debug("Langfuse not configured — tracing disabled.")
            return

        try:
            from langfuse import Langfuse  # type: ignore[import]

            self._client = Langfuse(
                public_key=pk,
                secret_key=sk,
                host=host,
            )
            self._enabled = True
            logger.debug("Langfuse tracer initialised.", extra={"host": host})
        except ImportError:
            logger.warning("langfuse package not installed — tracing disabled.")

    def trace(
        self,
        *,
        name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Fire-and-forget trace to Langfuse.
        §19: Required fields — provider, tokens, latency, success.
        §16: Never log full prompt/completion text (> 500 chars = secret risk).
        """
        if not self._enabled or self._client is None:
            return

        try:
            from langfuse import Langfuse  # type: ignore[import]

            client: Langfuse = self._client  # type: ignore[assignment]
            trace = client.trace(name=name)
            trace.generation(
                name=name,
                model=model,
                usage={
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                    "unit": "TOKENS",
                },
                metadata={
                    "latency_ms": latency_ms,
                    "success": success,
                    **(metadata or {}),
                },
            )
            client.flush()
        except Exception as exc:
            # Langfuse failure must NEVER break quest generation
            logger.warning(f"Langfuse trace failed (non-fatal): {exc}")


# ── Groq Adapter ──────────────────────────────────────────────


class GroqAdapter:
    """
    T2.1: Single synchronous Groq API adapter.
    §07 MVP: One prompt template. No chains. No agents. No streaming.
    §16: API keys from env only. Langfuse trace on every call.

    Thread safety: _KeyRotator is cycle-based; fine for single-process FastAPI.
    """

    def __init__(self) -> None:
        keys = _load_api_keys()
        self._rotator = _KeyRotator(keys)
        self._model = os.environ.get("GROQ_MODEL", _DEFAULT_MODEL)
        self._tracer = _LangfuseTracer()
        logger.info(
            f"GroqAdapter initialised: model={self._model}, "
            f"key_count={self._rotator.key_count}"
        )

    def _build_client(self) -> Groq:
        """
        T2.3: Build Groq client with httpx timeout wrapper.
        httpx.Timeout(connect=5s, read=15s) per T2.3 spec.
        """
        api_key = self._rotator.next()
        http_client = httpx.Client(timeout=_TIMEOUT)
        return Groq(api_key=api_key, http_client=http_client)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = _MAX_TOKENS,
        temperature: float = _TEMPERATURE,
    ) -> str:
        """
        T2.1: Make a synchronous Groq chat.completions.create() call.
        T2.2: Round-robins API keys per request.
        T2.3: httpx 15s read timeout applied via _build_client().
        T2.4: Langfuse trace emitted on completion (tokens, latency, success).

        Returns the raw string content from choices[0].message.content.
        Raises on all errors — caller (quest_service) handles fallback.

        §16: Prompt injection mitigation: caller sanitizes user strings
             before passing here. Never sanitize here (separation of concerns).
        §19: Log truncated (≤500 chars) for debugging — never full output.
        """
        t0 = time.monotonic()
        success = False
        prompt_tokens = 0
        completion_tokens = 0

        try:
            client = self._build_client()
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content or ""
            usage = response.usage

            if usage:
                prompt_tokens = usage.prompt_tokens or 0
                completion_tokens = usage.completion_tokens or 0

            latency_ms = (time.monotonic() - t0) * 1000
            success = True

            logger.info(
                "Groq call succeeded",
                extra={
                    "model": self._model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": round(latency_ms, 1),
                    "output_preview": content[:500],  # §19: truncate at 500
                },
            )

            # T2.4: Langfuse trace
            self._tracer.trace(
                name="groq.quest_generation",
                model=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                success=True,
            )

            return content

        except Exception as exc:
            latency_ms = (time.monotonic() - t0) * 1000

            logger.error(
                f"Groq call failed: {type(exc).__name__}: {exc}",
                extra={"latency_ms": round(latency_ms, 1)},
            )

            # T2.4: Trace failure
            self._tracer.trace(
                name="groq.quest_generation",
                model=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                success=False,
                metadata={"error": str(exc)[:200]},
            )

            raise
