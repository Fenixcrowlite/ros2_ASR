from __future__ import annotations

import json
import urllib.error
import urllib.request

from docsbot.indexer.models import ProjectIndex
from docsbot.planner.models import Task

from .prompts import SYSTEM_PROMPT, build_prompt
from .provider import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def name(self) -> str:
        return f"openai:{self._model}"

    def generate_markdown(
        self,
        *,
        task: Task,
        index: ProjectIndex,
        entity_payload: dict,
        existing_content: str | None,
    ) -> str:
        prompt = build_prompt(
            task=task, index=index, entity_payload=entity_payload, existing_content=existing_content
        )
        body = {
            "model": self._model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
            ],
            "temperature": 0.1,
        }
        req = urllib.request.Request(
            url="https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            # Constant HTTPS endpoint; request URL is not user-controlled.
            with urllib.request.urlopen(req, timeout=60) as response:  # nosec B310
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"openai request failed: {exc}") from exc

        # Responses API can return output_text directly or inside output content.
        if isinstance(payload, dict):
            text = payload.get("output_text")
            if isinstance(text, str) and text.strip():
                return text
            output = payload.get("output", [])
            for item in output:
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        return str(content["text"])

        raise RuntimeError("openai provider returned empty response")
