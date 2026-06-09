import json
import os
import re
import logging
from dataclasses import dataclass
from typing import Any
import warnings
# Suppress transformers __path__ messages (they use logging, not warnings)
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*Accessing __path__ from.*")

from llm.prompt import load_verifier_prompt

try:
    from groq import Groq
except ImportError:  # pragma: no cover - handled at runtime
    Groq = None

try:
    from mistralai.client import Mistral
except ImportError:  # pragma: no cover - handled at runtime
    Mistral = None


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model_id: str
    temperature: float = 0.3
    max_tokens: int | None = None
    fallback_task: str | None = None


TASK_MODEL_ROUTES = {
    "query_rewriting": ModelRoute(
        provider="groq",
        model_id="llama-3.1-8b-instant",
        temperature=0.0,
        max_tokens=256,
    ),
    "core_qa": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.3,
        max_tokens=1200,
    ),
    "flashcards": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.4,
        max_tokens=4000,
        fallback_task="feature_fallback",
    ),
    "quiz_generation": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.4,
        max_tokens=4000,
        fallback_task="feature_fallback",
    ),
    "viva_generation": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.4,
        max_tokens=1800,
        fallback_task="feature_fallback",
    ),
    "notes_generation": ModelRoute(
        provider="mistral",
        model_id="open-mistral-nemo",
        temperature=0.35,
        max_tokens=8000,
        fallback_task="feature_fallback",
    ),
    "report_generation": ModelRoute(
        provider="mistral",
        model_id="open-mistral-nemo",
        temperature=0.3,
        max_tokens=3200,
        fallback_task="feature_fallback",
    ),
    "summary_generation": ModelRoute(
        provider="mistral",
        model_id="open-mistral-nemo",
        temperature=0.25,
        max_tokens=2200,
        fallback_task="feature_fallback",
    ),
    "verifier_layer": ModelRoute(
        provider="groq",
        model_id="openai/gpt-oss-120b",
        temperature=0.0,
        max_tokens=1200,
    ),
    "web_research": ModelRoute(
        provider="groq",
        model_id="groq/compound",
        temperature=0.2,
        max_tokens=1200,
    ),
    "feature_fallback": ModelRoute(
        provider="groq",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.35,
        max_tokens=4000,
    ),
}


class StudyAssistantRouter:
    """Routes each study workflow to the configured provider/model pair."""

    def __init__(self, task_model_routes: dict[str, ModelRoute] | None = None):
        self.task_model_routes = task_model_routes or TASK_MODEL_ROUTES
        self._groq_client = None
        self._mistral_client = None

    def get_model_for_task(self, task_name: str) -> ModelRoute:
        route = self.task_model_routes.get(task_name)
        if route is None:
            available = ", ".join(sorted(self.task_model_routes))
            raise KeyError(
                f"Unknown task '{task_name}'. Available tasks: {available}"
            )
        return route

    def get_model_label(self, task_name: str) -> str:
        route = self.get_model_for_task(task_name)
        return f"{route.model_id} via {route.provider.title()}"

    def complete(
        self,
        task_name: str,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        allow_fallback: bool = True,
    ) -> str:
        route = self.get_model_for_task(task_name)

        try:
            return self._dispatch(
                route,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            if allow_fallback and route.fallback_task:
                fallback = self.get_model_for_task(route.fallback_task)
                return self._dispatch(
                    fallback,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise RuntimeError(
                f"Model call failed for task '{task_name}' using "
                f"{route.model_id} via {route.provider}."
            ) from exc

    def verify_answer(self, query: str, context: str, draft_answer: str) -> dict[str, Any]:
        verifier_prompt = load_verifier_prompt()
        raw_response = self.complete(
            "verifier_layer",
            [{
                "role": "user",
                "content": verifier_prompt.format(
                    query=query,
                    content=context,
                    answer=draft_answer,
                ),
            }],
            temperature=0.0,
        )
        return _parse_verifier_response(raw_response, draft_answer)

    def _dispatch(
        self,
        route: ModelRoute,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        temperature = route.temperature if temperature is None else temperature
        max_tokens = route.max_tokens if max_tokens is None else max_tokens

        if route.provider == "groq":
            client = self._get_groq_client()
            payload = {
                "model": route.model_id,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                payload["max_completion_tokens"] = max_tokens
            response = client.chat.completions.create(**payload)
            return _extract_text(response.choices[0].message.content)

        if route.provider == "mistral":
            client = self._get_mistral_client()
            payload = {
                "model": route.model_id,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            response = client.chat.complete(**payload)
            return _extract_text(response.choices[0].message.content)

        raise ValueError(f"Unsupported provider '{route.provider}'.")

    def _get_groq_client(self):
        if self._groq_client is None:
            if Groq is None:
                raise ImportError(
                    "The 'groq' package is not installed. Add it to requirements "
                    "or install it in the active environment."
                )
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "Missing GROQ_API_KEY. Add it to your environment or .env file."
                )
            self._groq_client = Groq(api_key=api_key)
        return self._groq_client

    def _get_mistral_client(self):
        if self._mistral_client is None:
            if Mistral is None:
                raise ImportError(
                    "The 'mistralai' package is not installed. Add it to "
                    "requirements or install it in the active environment."
                )
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "Missing MISTRAL_API_KEY. Add it to your environment or .env file."
                )
            self._mistral_client = Mistral(api_key=api_key)
        return self._mistral_client


def load_model_router() -> StudyAssistantRouter:
    return StudyAssistantRouter()


def answer_question(
    router: StudyAssistantRouter,
    prompt,
    query: str,
    context: str,
) -> dict[str, Any]:
    draft_answer = router.complete(
        "core_qa",
        [{
            "role": "user",
            "content": prompt.format(query=query, content=context),
        }],
    )
    verification = router.verify_answer(query, context, draft_answer)
    verification["draft_answer"] = draft_answer
    return verification


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "content" in item:
                    parts.append(str(item["content"]))
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    parts.append(text_value)
        return "\n".join(part for part in parts if part).strip()

    text_value = getattr(content, "text", None)
    if text_value:
        return str(text_value).strip()

    return str(content).strip()


def _parse_verifier_response(raw_response: str, draft_answer: str) -> dict[str, Any]:
    parsed = _extract_json_object(raw_response)
    if not parsed:
        return {
            "answer": draft_answer,
            "hallucination_score": None,
            "reason": "Verifier returned non-JSON output; using the draft answer.",
        }

    answer = parsed.get("answer") or draft_answer
    score = parsed.get("hallucination_score")
    try:
        score = int(score) if score is not None else None
    except (TypeError, ValueError):
        score = None

    return {
        "answer": answer,
        "hallucination_score": score,
        "reason": parsed.get("reason", ""),
    }


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
