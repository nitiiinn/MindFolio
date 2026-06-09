"""
model.py — The AI Model Router.

This is the brain of the application. It decides WHICH AI model to use
for EACH task (e.g., answering questions, generating quizzes, etc.).

We use two AI providers:
  - Groq  (fast, free tier) — for query rewriting, verification, fallback
  - Mistral (accurate) — for Q&A, notes, quizzes, flashcards

The router also handles:
  - Automatic fallback: if Mistral fails, it retries with Groq
  - Answer verification: a second AI checks the first AI's answer for accuracy
"""

import json
import os
import re
import logging
from dataclasses import dataclass
from typing import Any
import warnings

# Suppress noisy library warnings
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*Accessing __path__ from.*")

from llm.prompt import load_verifier_prompt

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from mistralai.client import Mistral
except ImportError:
    Mistral = None


# ── Model Configuration ─────────────────────────────────────────────────────
# Each task maps to a specific AI model. This makes it easy to swap models
# for any task without changing the rest of the code.

@dataclass(frozen=True)
class ModelRoute:
    """Configuration for a single AI model."""
    provider: str            # "groq" or "mistral"
    model_id: str            # The specific model name (e.g., "ministral-8b-2512")
    temperature: float = 0.3 # Higher = more creative, Lower = more factual
    max_tokens: int | None = None     # Max length of the AI's response
    fallback_task: str | None = None  # If this model fails, try this task's model instead


# ── Task → Model Mapping ────────────────────────────────────────────────────
TASK_MODEL_ROUTES = {
    # Rewrites user questions into better search queries for the vector DB
    "query_rewriting": ModelRoute(
        provider="groq",
        model_id="llama-3.1-8b-instant",
        temperature=0.0,
        max_tokens=256,
    ),

    # Answers user questions using retrieved document context
    "core_qa": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.3,
        max_tokens=None,
    ),

    # Generates Q&A flashcards from documents
    "flashcards": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.4,
        max_tokens=None,
        fallback_task="feature_fallback",
    ),

    # Generates MCQ quiz questions from documents
    "quiz_generation": ModelRoute(
        provider="mistral",
        model_id="ministral-8b-2512",
        temperature=0.4,
        max_tokens=None,
        fallback_task="feature_fallback",
    ),

    # Generates comprehensive study notes from documents
    "notes_generation": ModelRoute(
        provider="mistral",
        model_id="open-mistral-nemo",
        temperature=0.35,
        max_tokens=None,
        fallback_task="feature_fallback",
    ),

    # Checks if the Q&A answer is actually supported by the document
    "verifier_layer": ModelRoute(
        provider="groq",
        model_id="openai/gpt-oss-120b",
        temperature=0.0,
        max_tokens=None,
    ),

    # Backup model — used when Mistral models fail
    "feature_fallback": ModelRoute(
        provider="groq",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.35,
        max_tokens=None,
    ),
}


# ── The Router Class ─────────────────────────────────────────────────────────

class StudyAssistantRouter:
    """Routes each task to the right AI model and handles API calls.

    Usage:
        router = StudyAssistantRouter()
        answer = router.complete("core_qa", [{"role": "user", "content": "..."}])
    """

    def __init__(self, task_model_routes: dict[str, ModelRoute] | None = None):
        self.task_model_routes = task_model_routes or TASK_MODEL_ROUTES
        self._groq_client = None     # Lazy-loaded (created on first use)
        self._mistral_client = None  # Lazy-loaded (created on first use)

    def get_model_for_task(self, task_name: str) -> ModelRoute:
        """Look up which model is assigned to a task."""
        route = self.task_model_routes.get(task_name)
        if route is None:
            available = ", ".join(sorted(self.task_model_routes))
            raise KeyError(f"Unknown task '{task_name}'. Available: {available}")
        return route

    def get_model_label(self, task_name: str) -> str:
        """Human-readable label like 'ministral-8b-2512 via Mistral'."""
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
        """Send messages to the AI model for a given task. Returns the response text.

        If the primary model fails and a fallback is configured, it automatically
        retries with the fallback model.
        """
        route = self.get_model_for_task(task_name)

        try:
            return self._dispatch(route, messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as exc:
            # If this task has a fallback model, try that instead
            if allow_fallback and route.fallback_task:
                fallback = self.get_model_for_task(route.fallback_task)
                return self._dispatch(fallback, messages, temperature=temperature, max_tokens=max_tokens)
            raise RuntimeError(
                f"Model call failed for '{task_name}' using {route.model_id} via {route.provider}."
            ) from exc

    def verify_answer(self, query: str, context: str, draft_answer: str) -> dict[str, Any]:
        """Use a second AI model to check if the answer is grounded in the context.

        Returns a dict with:
          - answer: the corrected/confirmed answer
          - hallucination_score: 0 (fully accurate) to 100 (completely made up)
          - reason: why it was corrected or confirmed
        """
        verifier_prompt = load_verifier_prompt()
        raw_response = self.complete(
            "verifier_layer",
            [{"role": "user", "content": verifier_prompt.format(
                query=query, content=context, answer=draft_answer,
            )}],
            temperature=0.0,
        )
        return _parse_verifier_response(raw_response, draft_answer)

    def _dispatch(self, route, messages, *, temperature=None, max_tokens=None) -> str:
        """Internal: send the API request to the correct provider."""
        temperature = route.temperature if temperature is None else temperature
        max_tokens = route.max_tokens if max_tokens is None else max_tokens

        if route.provider == "groq":
            client = self._get_groq_client()
            payload = {"model": route.model_id, "messages": messages, "temperature": temperature}
            if max_tokens is not None:
                payload["max_completion_tokens"] = max_tokens
            response = client.chat.completions.create(**payload)
            return _extract_text(response.choices[0].message.content)

        if route.provider == "mistral":
            client = self._get_mistral_client()
            payload = {"model": route.model_id, "messages": messages, "temperature": temperature}
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            response = client.chat.complete(**payload)
            return _extract_text(response.choices[0].message.content)

        raise ValueError(f"Unsupported provider '{route.provider}'.")

    def _get_groq_client(self):
        """Create the Groq client on first use (lazy initialization)."""
        if self._groq_client is None:
            if Groq is None:
                raise ImportError("The 'groq' package is not installed.")
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise EnvironmentError("Missing GROQ_API_KEY in your .env file.")
            self._groq_client = Groq(api_key=api_key)
        return self._groq_client

    def _get_mistral_client(self):
        """Create the Mistral client on first use (lazy initialization)."""
        if self._mistral_client is None:
            if Mistral is None:
                raise ImportError("The 'mistralai' package is not installed.")
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise EnvironmentError("Missing MISTRAL_API_KEY in your .env file.")
            self._mistral_client = Mistral(api_key=api_key)
        return self._mistral_client


# ── Public Helper Functions ──────────────────────────────────────────────────

def load_model_router() -> StudyAssistantRouter:
    """Create a fresh router instance. Called once at app startup."""
    return StudyAssistantRouter()


def answer_question(router, prompt, query: str, context: str) -> dict[str, Any]:
    """Full Q&A pipeline: generate an answer, then verify it for accuracy."""
    # Step 1: Get a draft answer from the primary Q&A model
    draft_answer = router.complete(
        "core_qa",
        [{"role": "user", "content": prompt.format(query=query, content=context)}],
    )
    # Step 2: Verify the answer with a separate model
    verification = router.verify_answer(query, context, draft_answer)
    verification["draft_answer"] = draft_answer
    return verification


# ── Private Helper Functions ─────────────────────────────────────────────────

def _extract_text(content: Any) -> str:
    """Safely extract plain text from an AI response.

    AI APIs can return strings, lists, or objects — this handles all cases.
    """
    if isinstance(content, str):
        return content.strip()

    # Some APIs return a list of content blocks
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text", item.get("content", "")))
            else:
                parts.append(getattr(item, "text", str(item)))
        return "\n".join(str(p) for p in parts if p).strip()

    # Fallback: try .text attribute, then just stringify
    return str(getattr(content, "text", content)).strip()


def _parse_verifier_response(raw_response: str, draft_answer: str) -> dict[str, Any]:
    """Parse the JSON output from the verifier model."""
    parsed = _extract_json_object(raw_response)

    # If the verifier didn't return valid JSON, just use the draft answer as-is
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
    """Find and parse the first JSON object {...} in a string."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
