"""Groq LLM client for restaurant recommendations."""

import json
import os
import re

from openai import OpenAI

from src.prompt_builder import NO_RESTAURANTS_MESSAGE

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 1500


def _build_client() -> OpenAI:
    """Create an OpenAI SDK client configured for Groq."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your Groq API key."
        )
    base_url = os.environ.get("GROQ_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


def _parse_response(raw: str) -> list[dict]:
    """Parse LLM response text into a list of recommendation dicts."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value

    return []


def get_recommendations(prompt: str) -> list[dict]:
    """Send prompt to Groq and return parsed recommendation dicts."""
    if prompt.strip() == NO_RESTAURANTS_MESSAGE:
        return []

    client = _build_client()
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
    )

    raw = response.choices[0].message.content or ""
    return _parse_response(raw)


if __name__ == "__main__":
    # Parse response tests (no API key required)
    fenced = '```json\n[{"rank": 1, "name": "Test"}]\n```'
    parsed = _parse_response(fenced)
    assert len(parsed) == 1 and parsed[0]["name"] == "Test"

    wrapped = '{"recommendations": [{"rank": 1, "name": "Wrapped"}]}'
    parsed = _parse_response(wrapped)
    assert len(parsed) == 1 and parsed[0]["name"] == "Wrapped"

    assert _parse_response("not json") == []

    saved_key = os.environ.pop("GROQ_API_KEY", None)
    try:
        try:
            _build_client()
            raise AssertionError("Expected EnvironmentError")
        except EnvironmentError:
            pass
    finally:
        if saved_key:
            os.environ["GROQ_API_KEY"] = saved_key

    if os.environ.get("GROQ_API_KEY"):
        sample = (
            "Return a JSON array with one item: "
            '{"rank": 1, "name": "Test Cafe", "cuisine": "Italian", '
            '"rating": 4.5, "cost_for_two": 500, "explanation": "Great food."}'
        )
        result = get_recommendations(sample)
        assert isinstance(result, list)
        print("Live API test:", len(result), "recommendation(s)")
    else:
        print("Skipping live API test (GROQ_API_KEY not set)")

    print("All llm_client verification checks passed.")
