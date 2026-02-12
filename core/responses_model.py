from __future__ import annotations

from typing import Any

from openai import OpenAI
from smolagents.models import ChatMessage, MessageRole, TokenUsage


class ResponsesModel:
    """
    Minimal wrapper to use OpenAI Responses API with the smolagents generate() interface.
    Optionally falls back to a chat model on failure.
    """

    def __init__(self, model_id: str, api_key: str, client: Any | None = None, fallback: Any | None = None):
        self.model_id = model_id
        self.client = client or OpenAI(api_key=api_key)
        self.fallback = fallback

    def _messages_to_text(self, messages) -> str:
        parts = []
        for m in messages:
            role = None
            content = None
            if isinstance(m, dict):
                role = m.get("role")
                content = m.get("content")
            else:
                role = getattr(m, "role", None)
                content = getattr(m, "content", None)

            text = ""
            if isinstance(content, list):
                # content is list of {"type": "text", "text": "..."} blocks
                for el in content:
                    if isinstance(el, dict):
                        if el.get("type") in ("text", "input_text"):
                            text += el.get("text", "")
            elif isinstance(content, str):
                text = content

            role = role or "user"
            if text:
                parts.append(f"{role}: {text}")

        return "\n".join(parts) if parts else ""

    def _extract_text(self, response) -> str:
        # New SDK convenience
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        # Generic fallback
        try:
            for output in response.output:
                if getattr(output, "type", None) == "message":
                    for c in output.content:
                        if getattr(c, "type", None) in ("output_text", "text"):
                            return c.text
        except Exception:
            pass
        return ""

    def generate(self, messages, response_format: dict | None = None, **kwargs) -> ChatMessage:
        """
        Use Responses API; fall back to chat-completions on failure.
        We avoid passing response_format to Responses API because some SDKs/models
        don't support it yet. We keep it for fallback.
        """
        # Prepare kwargs for responses vs fallback
        kwargs_responses = dict(kwargs)
        kwargs_fallback = dict(kwargs)

        # Map max_completion_tokens -> max_output_tokens for responses API
        if "max_completion_tokens" in kwargs_responses:
            kwargs_responses["max_output_tokens"] = kwargs_responses.pop("max_completion_tokens")

        # Do NOT pass response_format to Responses API (compatibility)
        # Keep response_format for fallback (chat-completions)

        prompt = self._messages_to_text(messages)
        try:
            resp = self.client.responses.create(
                model=self.model_id,
                input=prompt,
                **kwargs_responses,
            )
            content = self._extract_text(resp)
            token_usage = None
            try:
                usage = resp.usage
                token_usage = TokenUsage(
                    input_tokens=getattr(usage, "input_tokens", None),
                    output_tokens=getattr(usage, "output_tokens", None),
                )
            except Exception:
                pass
            return ChatMessage(
                role=MessageRole.ASSISTANT,
                content=content,
                tool_calls=None,
                raw=resp,
                token_usage=token_usage,
            )
        except Exception:
            if self.fallback:
                # Ensure fallback doesn't receive max_output_tokens
                kwargs_fallback.pop("max_output_tokens", None)
                return self.fallback.generate(
                    messages=messages,
                    response_format=response_format,
                    **kwargs_fallback,
                )
            raise
