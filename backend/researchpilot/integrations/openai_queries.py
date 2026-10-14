"""SDK-free OpenAI Chat Completions adapter for structured query suggestions.

Only this module knows the vendor endpoint/envelope. It never logs or returns the key,
request context, raw bodies, headers, or exception text.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

import httpx
from pydantic import ValidationError

from researchpilot.query_domain import SuggestionBatch
from researchpilot.query_provider import (
    SuggestionMetadata,
    SuggestionProviderError,
    SuggestionResult,
)

ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4.1-mini-2025-04-14"
ALLOWED_MODELS = frozenset({DEFAULT_MODEL})
PROMPT_VERSION = "query_suggestions_v1"
PROMPT = (Path(__file__).resolve().parents[1] / "prompts" / f"{PROMPT_VERSION}.txt"
          ).read_text(encoding="utf-8")
PROMPT_SHA256 = hashlib.sha256(PROMPT.encode()).hexdigest()
MAX_COMPLETION_TOKENS = 512
MAX_BODY_BYTES = 64 * 1024
TOTAL_TIMEOUT_SECONDS = 20
PHASE_TIMEOUT = httpx.Timeout(connect=3, pool=2, write=5, read=15)
LIMITS = httpx.Limits(max_connections=2, max_keepalive_connections=2)
RESPONSE_FORMAT = {"type": "json_schema", "json_schema": {
    "name": "query_suggestions", "strict": True, "schema": {
        "type": "object",
        "properties": {"queries": {"type": "array", "minItems": 3, "maxItems": 6,
                                   "items": {"type": "string"}}},
        "required": ["queries"], "additionalProperties": False}}}

logger = logging.getLogger("researchpilot.suggestions")


def build_client():
    return httpx.AsyncClient(timeout=PHASE_TIMEOUT, limits=LIMITS, verify=True,
                             follow_redirects=False, trust_env=False)


def from_environment(environment):
    """Return a configured adapter, or None so manual-only operation stays available."""
    key = (environment.get("OPENAI_API_KEY") or "").strip()
    model = (environment.get("OPENAI_QUERY_MODEL") or "").strip() or DEFAULT_MODEL
    if not key:
        logger.info("Query suggestions disabled: no API key configured")
        return None
    if model not in ALLOWED_MODELS:
        logger.warning("Query suggestions disabled: unreviewed model configuration")
        return None
    return OpenAIQueryProvider(key, model=model)


def _token(usage, name):
    value = usage.get(name) if isinstance(usage, dict) else None
    return value if type(value) is int and value >= 0 else None


def _parse(body):
    """Accept only one complete, unrefused assistant choice with a valid whole batch."""
    try:
        envelope = json.loads(body)
        choices = envelope["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError
        choice = choices[0]
        message = choice["message"]
        content = message["content"]
        if (choice.get("finish_reason") != "stop" or message.get("role") != "assistant"
                or message.get("refusal") is not None
                or not isinstance(content, str) or not content.strip()):
            raise ValueError
        batch = SuggestionBatch.model_validate(json.loads(content))
    except (ValueError, TypeError, KeyError, ValidationError):
        raise SuggestionProviderError("invalid_output") from None
    return batch, envelope.get("usage")


class OpenAIQueryProvider:
    def __init__(self, api_key, model=DEFAULT_MODEL, client=None,
                 total_timeout=TOTAL_TIMEOUT_SECONDS):
        if model not in ALLOWED_MODELS:
            raise ValueError("Unreviewed suggestion model")
        self._key = api_key
        self.model = model
        self._client = client or build_client()
        self._total_timeout = total_timeout

    def __repr__(self):
        return f"OpenAIQueryProvider(model={self.model!r})"

    async def aclose(self):
        await self._client.aclose()

    def _payload(self, context):
        data = {"researchQuestion": context.question, "keywords": list(context.keywords)}
        return {
            "model": self.model, "store": False, "stream": False, "n": 1,
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
            "messages": [{"role": "system", "content": PROMPT},
                         {"role": "user", "content": json.dumps(data, ensure_ascii=False)}],
            "response_format": RESPONSE_FORMAT,
        }

    async def _request(self, context):
        headers = {"Authorization": f"Bearer {self._key}"}
        async with self._client.stream("POST", ENDPOINT, json=self._payload(context),
                                       headers=headers) as response:
            if response.status_code != 200:
                raise SuggestionProviderError(
                    "busy" if response.status_code == 429 else "unavailable")
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > MAX_BODY_BYTES:
                    raise SuggestionProviderError("invalid_output")
            return bytes(body)

    async def suggest(self, context):
        started = time.monotonic()
        category, usage = "cancelled", None
        try:
            try:
                async with asyncio.timeout(self._total_timeout):
                    body = await self._request(context)
            except (TimeoutError, httpx.TimeoutException):
                raise SuggestionProviderError("timeout") from None
            except httpx.HTTPError:
                raise SuggestionProviderError("unavailable") from None
            batch, usage = _parse(body)
            category = "success"
        except SuggestionProviderError as error:
            category = error.category
            raise
        finally:
            duration = time.monotonic() - started
            logger.info("Suggestion request status=%s model=%s prompt=%s duration=%.3fs "
                        "input_tokens=%s output_tokens=%s total_tokens=%s", category,
                        self.model, PROMPT_VERSION, duration, _token(usage, "prompt_tokens"),
                        _token(usage, "completion_tokens"), _token(usage, "total_tokens"))
        return SuggestionResult(batch=batch, metadata=SuggestionMetadata(
            model=self.model, promptVersion=PROMPT_VERSION, durationSeconds=duration,
            inputTokens=_token(usage, "prompt_tokens"),
            outputTokens=_token(usage, "completion_tokens"),
            totalTokens=_token(usage, "total_tokens")))
