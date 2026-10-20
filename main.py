import json
import os
import re
import sys
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions
from dotenv import load_dotenv
from pydantic import ValidationError

from app.models.models import TripRequest

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "parse_trip_request.txt"
_FENCE_BLOCK = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def main() -> None:
    query = read_user_query()
    trip = trip_request_from_query(query)
    print(trip.model_dump_json(indent=2))


def read_user_query() -> str:
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:]).strip()
    elif sys.stdin.isatty():
        print("Describe your trip. Submit a blank line when you are done.")
        lines: list[str] = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        text = "\n".join(lines).strip()
    else:
        text = sys.stdin.read().strip()
    if not text:
        raise SystemExit("A trip description is required")
    return text


def trip_request_from_query(query: str) -> TripRequest:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("CURSOR_API_KEY is required")

    prompt = PROMPT_PATH.read_text(encoding="utf-8").replace("{user_query}", query)
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
        raise SystemExit(f"Prompt failed to start: {exc.message}") from exc

    if result.status != "finished":
        raise SystemExit(f"Prompt failed: {result.status}")

    content = _model_text(result.result)
    if not content:
        raise SystemExit("Prompt returned an empty response")
    return trip_request_from_text(content)


def trip_request_from_text(content: str) -> TripRequest:
    payload = _extract_json_object(content)
    if payload.get("cities") is None:
        payload["cities"] = []
    try:
        return TripRequest.model_validate(payload)
    except ValidationError as exc:
        raise SystemExit(f"Response is not a TripRequest:\n{exc}") from exc


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


def _extract_json_object(content: str) -> dict:
    text = content.strip()
    fenced = _FENCE_BLOCK.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            raise SystemExit("Prompt response is not a JSON object")
        try:
            payload, _ = json.JSONDecoder().raw_decode(text[start:])
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Prompt response is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Prompt response is not a JSON object")
    return payload


if __name__ == "__main__":
    main()
