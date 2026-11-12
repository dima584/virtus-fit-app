"""Cloudflare Workers AI adapter for Virtus Fit.

Uses:
- Gemma 4 26B A4B for text and image understanding.
- Whisper for audio transcription.

Secrets are read from environment variables and are never sent to the frontend.
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
from dataclasses import dataclass
from typing import Any

import aiohttp
from PIL import Image


logger = logging.getLogger(__name__)


class CloudflareAIError(RuntimeError):
    """Raised when Cloudflare Workers AI returns an unusable response."""


@dataclass(slots=True)
class AIResponse:
    text: str


class CloudflareAI:
    def __init__(self) -> None:
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        self.model_id = os.getenv(
            "CLOUDFLARE_GEMMA_MODEL",
            "@cf/google/gemma-4-26b-a4b-it",
        ).strip()
        self.whisper_model_id = os.getenv(
            "CLOUDFLARE_WHISPER_MODEL",
            "@cf/openai/whisper",
        ).strip()
        self.timeout_seconds = float(os.getenv("CLOUDFLARE_AI_TIMEOUT", "90"))
        self.max_concurrency = max(
            1, int(os.getenv("CLOUDFLARE_AI_MAX_CONCURRENCY", "6"))
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self._session: aiohttp.ClientSession | None = None

    def _validate_config(self) -> None:
        missing = []
        if not self.account_id:
            missing.append("CLOUDFLARE_ACCOUNT_ID")
        if not self.api_token:
            missing.append("CLOUDFLARE_API_TOKEN")
        if missing:
            raise CloudflareAIError(
                "Missing Cloudflare configuration: " + ", ".join(missing)
            )

    @property
    def _api_base(self) -> str:
        return (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai"
        )

    async def start(self) -> None:
        self._validate_config()
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            connector = aiohttp.TCPConnector(
                limit=max(20, self.max_concurrency * 3),
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Accept": "application/json",
                },
            )
            logger.info(
                "Cloudflare Workers AI ready (model=%s, concurrency=%s)",
                self.model_id,
                self.max_concurrency,
            )

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._session is None or self._session.closed:
            await self.start()

        assert self._session is not None
        url = f"{self._api_base}/{endpoint.lstrip('/')}"
        last_error: Exception | None = None

        async with self._semaphore:
            for attempt in range(3):
                try:
                    async with self._session.post(url, json=payload) as response:
                        try:
                            body = await response.json(content_type=None)
                        except (aiohttp.ContentTypeError, ValueError):
                            raw_body = (await response.text())[:1000]
                            body = {"raw": raw_body}

                        if response.status < 400:
                            if isinstance(body, dict) and body.get("success") is False:
                                errors = body.get("errors") or []
                                detail = "; ".join(
                                    str(item.get("message", item))
                                    for item in errors
                                ) or str(body)
                                raise CloudflareAIError(detail)
                            if isinstance(body, dict) and "result" in body:
                                return body["result"] or {}
                            return body if isinstance(body, dict) else {"result": body}

                        detail = self._error_detail(body)
                        is_daily_limit = (
                            "3036" in detail
                            or "10,000 neurons" in detail.lower()
                            or "daily free allocation" in detail.lower()
                        )
                        transient = response.status in {429, 500, 502, 503, 504}
                        if not transient or is_daily_limit or attempt == 2:
                            raise CloudflareAIError(
                                f"Cloudflare Workers AI HTTP {response.status}: {detail}"
                            )

                        retry_after = response.headers.get("Retry-After")
                        try:
                            delay = min(12.0, max(1.0, float(retry_after)))
                        except (TypeError, ValueError):
                            delay = min(8.0, 1.5 * (2 ** attempt))
                        logger.warning(
                            "Cloudflare AI temporarily unavailable (HTTP %s); retry in %.1fs",
                            response.status,
                            delay,
                        )
                        await asyncio.sleep(delay)

                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    last_error = exc
                    if attempt == 2:
                        break
                    await asyncio.sleep(1.0 * (2 ** attempt))

        if last_error:
            raise CloudflareAIError(
                f"Cloudflare Workers AI request failed: {last_error}"
            ) from last_error
        raise CloudflareAIError("Cloudflare Workers AI request failed without a response")

    @staticmethod
    def _error_detail(body: Any) -> str:
        if isinstance(body, dict):
            errors = body.get("errors") or []
            if errors:
                return "; ".join(
                    str(item.get("message", item)) for item in errors
                )
            return str(body)[:1500]
        return str(body)[:1500]

    @staticmethod
    def _encode_image(image: Image.Image) -> str:
        image = image.convert("RGB")
        max_side = 2048
        if max(image.size) > max_side:
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            image.thumbnail((max_side, max_side), resampling)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=88, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def _message_content(self, contents: Any) -> str | list[dict[str, Any]]:
        if isinstance(contents, str):
            return contents
        if not isinstance(contents, (list, tuple)):
            return str(contents)

        parts: list[dict[str, Any]] = []
        for item in contents:
            if isinstance(item, str):
                parts.append({"type": "text", "text": item})
            elif isinstance(item, Image.Image):
                parts.append({
                    "type": "image_url",
                    "image_url": {"url": self._encode_image(item)},
                })
            elif isinstance(item, dict):
                mime_type = str(
                    item.get("mime_type") or item.get("mimeType") or ""
                ).lower()
                raw_data = item.get("data")
                if mime_type.startswith("image/") and isinstance(
                    raw_data, (bytes, bytearray)
                ):
                    encoded = base64.b64encode(raw_data).decode("ascii")
                    parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded}"
                        },
                    })
                elif mime_type.startswith("audio/"):
                    raise CloudflareAIError(
                        "Audio must be transcribed with transcribe_audio() before chat completion."
                    )
                else:
                    raise CloudflareAIError(
                        f"Unsupported multimodal content type: {mime_type or 'unknown'}"
                    )
            else:
                raise CloudflareAIError(
                    f"Unsupported content item: {type(item).__name__}"
                )

        return parts or ""

    async def generate_content_async(
        self,
        contents: Any,
        generation_config: dict[str, Any] | None = None,
    ) -> AIResponse:
        """Compatibility method replacing google-generativeai calls."""
        message_content = self._message_content(contents)
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": message_content}],
            "temperature": 0.35,
            "max_completion_tokens": 4096,
        }

        generation_config = generation_config or {}
        if generation_config.get("response_mime_type") == "application/json":
        if generation_config.get("response_mime_type") == "application/json":
            instruction = (
                "Return ONLY valid JSON. Do not add markdown fences or explanations."
            )
            if isinstance(message_content, str):
                payload["messages"][0]["content"] += "\n\n" + instruction
            else:
                payload["messages"].append({"role": "user", "content": instruction})

        data = await self._post_json(f"run/{self.model_id}", {
            "messages": payload["messages"],
            "temperature": payload["temperature"],
            "max_tokens": 4096,
        })
        content = data.get("response") or data.get("text")
        if not content:
            raise CloudflareAIError(
                "Gemma returned an empty response: " + str(data)[:1000]
            )
        if isinstance(content, list):
            content = "\n".join(
                str(part.get("text", ""))
                for part in content if isinstance(part, dict)
            )
        if not isinstance(content, str) or not content.strip():
            raise CloudflareAIError("Gemma returned an empty text response.")

        if generation_config.get("response_mime_type") == "application/json":
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3].strip()
            try:
                import json
                json.loads(content)
            except ValueError:
                start = min(
                    [p for p in (content.find("{"), content.find("[")) if p >= 0],
                    default=-1,
                )
                end = max(content.rfind("}"), content.rfind("]"))
                if start >= 0 and end > start:
                    candidate = content[start:end + 1]
                    try:
                        json.loads(candidate)
                        content = candidate
                    except ValueError:
                        pass

        return AIResponse(text=content.strip())

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe Telegram voice bytes using Cloudflare Whisper."""
        if not audio_bytes:
            raise CloudflareAIError("The voice message is empty.")
        if len(audio_bytes) > 20 * 1024 * 1024:
            raise CloudflareAIError("The voice message is larger than 20 MB.")

        if self._session is None or self._session.closed:
            await self.start()

        assert self._session is not None
        url = f"{self._api_base}/run/{self.whisper_model_id}"
        async with self._semaphore:
            async with self._session.post(
                url,
                data=audio_bytes,
                headers={"Content-Type": "application/octet-stream"},
            ) as response:
                try:
                    body = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    body = {"raw": (await response.text())[:1000]}
                if response.status >= 400:
                    raise CloudflareAIError(
                        f"Whisper HTTP {response.status}: {self._error_detail(body)}"
                    )
                if isinstance(body, dict) and body.get("success") is False:
                    raise CloudflareAIError(self._error_detail(body))
                data = body.get("result", body) if isinstance(body, dict) else {}
        transcript = data.get("text", "")
        if not isinstance(transcript, str) or not transcript.strip():
            raise CloudflareAIError("Whisper could not recognize speech.")
        return transcript.strip()
