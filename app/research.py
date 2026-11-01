import json
import os
import re
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
from dotenv import load_dotenv
from pydantic import TypeAdapter, ValidationError

from app.models.models import (
    DestinationResearchRequest,
    DestinationResearchResult,
    TripRequest,
)

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "destination_research.txt"
_FENCE_BLOCK = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
_RESULTS = TypeAdapter(list[DestinationResearchResult])


def request_from_trip(trip: TripRequest) -> DestinationResearchRequest:
    """Build a research request from the cities and interests on a trip."""
    return DestinationResearchRequest(
        destination=trip.destination,
        cities=trip.cities,
        interests=trip.requirements.interests,
    )


def research_destination(request: DestinationResearchRequest) -> list[DestinationResearchResult]:
    """Ask the model for activities that match the destination request."""
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if not api_key:
        raise ValueError("CURSOR_API_KEY is required")

    prompt = PROMPT_PATH.read_text(encoding="utf-8").replace(
        "{request_json}",
        request.model_dump_json(indent=2),
    )
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=os.getenv("CURSOR_MODEL", "composer-2.5"),
                local=LocalAgentOptions(cwd=str(ROOT)),
                tools=[],
            ),
        )
    except CursorAgentError as exc:
        raise ValueError(f"Research failed to start: {exc.message}") from exc

    if result.status != "finished":
        raise ValueError(f"Research failed: {result.status}")
    content = _model_text(result.result)
    if not content:
        raise ValueError("Research returned an empty response")
    return results_from_text(content)


def results_from_text(content: str) -> list[DestinationResearchResult]:
    payload = _extract_json_array(content)
    try:
        return _RESULTS.validate_python(payload)
    except ValidationError as exc:
        raise ValueError(f"Response is not a list of destination research results:\n{exc}") from exc


def _model_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def _extract_json_array(content: str) -> list:
    text = content.strip()
    fenced = _FENCE_BLOCK.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        if start < 0:
            start = text.find("{")
        if start < 0:
            raise ValueError("Research response is not JSON")
        try:
            payload, _ = json.JSONDecoder().raw_decode(text[start:])
        except json.JSONDecodeError as exc:
            raise ValueError(f"Research response is not valid JSON: {exc}") from exc
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        payload = payload["results"]
    if not isinstance(payload, list):
        raise ValueError("Research response is not a JSON array")
    return payload
