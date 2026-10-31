import re
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import ValidationError

from app.models.models import Budget, BudgetType, TravelStyle, TripRequest, WalkingLevel

_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
_PREFIX_CURRENCY = {
    "c": "CAD",
    "us": "USD",
    "a": "AUD",
    "nz": "NZD",
}
_NUMBER = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b",
    re.IGNORECASE,
)
_PREFIX_AMOUNT = re.compile(
    r"\b([A-Za-z]{1,2})\$\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
_AMOUNT = re.compile(r"([\d,]+(?:\.\d+)?)")
_CODE = re.compile(r"\b([A-Za-z]{3})\b")
_HEDGE = re.compile(r"\b(around|about|approximately|roughly)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ClarifyingQuestion:
    field: str
    prompt: str


def clarifying_questions(trip: TripRequest) -> list[ClarifyingQuestion]:
    """Questions for trip details that were not in the original request."""
    questions: list[ClarifyingQuestion] = []
    if trip.days is None:
        questions.append(ClarifyingQuestion("days", "How many days is the trip?"))
    if trip.adults is None:
        questions.append(ClarifyingQuestion("adults", "How many adults are traveling?"))
    if trip.children is None:
        questions.append(ClarifyingQuestion("children", "How many children are traveling?"))
    if trip.budget is None or trip.budget.amount is None:
        questions.append(
            ClarifyingQuestion(
                "budget",
                "What is your total budget, including the currency?",
            )
        )
    elif trip.budget.currency is None:
        questions.append(ClarifyingQuestion("currency", "Which currency is the budget in?"))
    if not trip.cities:
        questions.append(ClarifyingQuestion("cities", "Which cities do you want to visit?"))
    if trip.travel_style is None:
        questions.append(
            ClarifyingQuestion(
                "travel_style",
                "What travel style do you prefer: relaxed, balanced, adventure, cultural, or luxury?",
            )
        )
    if trip.walking_level is None:
        questions.append(
            ClarifyingQuestion(
                "walking_level",
                "What walking level do you want: low, moderate, or high?",
            )
        )
    return questions


def apply_answer(trip: TripRequest, field: str, answer: str) -> TripRequest:
    """Fill one missing field from the user's reply."""
    text = answer.strip()
    if not text:
        return trip
    updates = _updates(trip, field, text)
    try:
        return trip.model_copy(update=updates)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"]
        raise ValueError(message) from exc


def fill_missing(trip: TripRequest, read_line: Callable[[], str]) -> TripRequest:
    """Ask each clarifying question once, and again when an answer is invalid."""
    asked: set[str] = set()
    while True:
        pending = [question for question in clarifying_questions(trip) if question.field not in asked]
        if not pending:
            return trip
        question = pending[0]
        print(question.prompt)
        answer = read_line()
        if not answer.strip():
            asked.add(question.field)
            continue
        try:
            trip = apply_answer(trip, question.field, answer)
        except ValueError as exc:
            print(exc)
            continue
        asked.add(question.field)
        if question.field == "budget":
            asked.discard("currency")


def _updates(trip: TripRequest, field: str, text: str) -> dict:
    if field == "days":
        return {"days": _whole_number(text, "Enter the number of days, such as 7.")}
    if field == "adults":
        return {"adults": _whole_number(text, "Enter the number of adults, such as 2.")}
    if field == "children":
        return {"children": _whole_number(text, "Enter the number of children, such as 0.")}
    if field == "budget":
        amount, currency = _budget(text)
        return {
            "budget": Budget(
                amount=amount,
                currency=currency,
                type=_budget_type(text),
            )
        }
    if field == "currency":
        current = trip.budget or Budget()
        return {"budget": current.model_copy(update={"currency": _currency(text)})}
    if field == "cities":
        return {"cities": _cities(text)}
    if field == "travel_style":
        return {"travel_style": _choice(text, TravelStyle, "Choose relaxed, balanced, adventure, cultural, or luxury.")}
    if field == "walking_level":
        return {"walking_level": _choice(text, WalkingLevel, "Choose low, moderate, or high.")}
    raise ValueError(f"Unknown field: {field}")


def _whole_number(text: str, error: str) -> int:
    match = _NUMBER.search(text)
    if match is None:
        raise ValueError(error)
    raw = match.group(1)
    if raw.isdigit():
        return int(raw)
    return _WORD_NUMBERS[raw.lower()]


def _budget_type(text: str) -> BudgetType:
    if _HEDGE.search(text):
        return BudgetType.APPROXIMATE
    return BudgetType.EXACT


def _budget(text: str) -> tuple[float, str | None]:
    prefixed = _PREFIX_AMOUNT.search(text)
    if prefixed:
        amount = float(prefixed.group(2).replace(",", ""))
        return amount, _PREFIX_CURRENCY.get(prefixed.group(1).lower())
    amount_match = _AMOUNT.search(text)
    if amount_match is None:
        raise ValueError("Enter a budget amount, such as 6000 CAD.")
    amount = float(amount_match.group(1).replace(",", ""))
    code = _CODE.search(text)
    return amount, None if code is None else code.group(1)


def _currency(text: str) -> str:
    prefixed = _PREFIX_AMOUNT.search(text)
    if prefixed:
        code = _PREFIX_CURRENCY.get(prefixed.group(1).lower())
        if code is not None:
            return code
    code = _CODE.search(text)
    if code is None:
        raise ValueError("Enter a 3-letter currency code, such as CAD.")
    return code.group(1)


def _cities(text: str) -> list[str]:
    parts = re.split(r",|\band\b", text, flags=re.IGNORECASE)
    cities = [part.strip(" .") for part in parts if part.strip(" .")]
    if not cities:
        raise ValueError("Enter at least one city.")
    return cities


def _choice(text: str, enum_type: type[TravelStyle] | type[WalkingLevel], error: str) -> str:
    pattern = re.compile(
        r"\b(" + "|".join(item.value for item in enum_type) + r")\b",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match is None:
        raise ValueError(error)
    return match.group(1).lower()
