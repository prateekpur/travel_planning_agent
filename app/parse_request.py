import re
from datetime import date

from app.models.models import Budget, BudgetType, Requirements, TravelStyle, TripRequest, WalkingLevel

_NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
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
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_PREFIX_CURRENCY = {
    "c": "CAD",
    "us": "USD",
    "a": "AUD",
    "nz": "NZD",
}

_BUDGET = re.compile(
    r"(?:budget(?:\s+is)?\s+)?"
    r"(?P<hedge>around|about|approximately|roughly)?\s*"
    r"(?P<prefix>[A-Za-z]{1,2})?\$\s*(?P<amount>[\d,]+(?:\.\d+)?)"
    r"(?:\s+(?P<code>[A-Za-z]{3})\b)?",
    re.IGNORECASE,
)
_BUDGET_CODE = re.compile(
    r"(?P<hedge>around|about|approximately|roughly)?\s*"
    r"\b(?P<code>USD|CAD|EUR|GBP|AUD|NZD)\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
_CEILING = re.compile(
    r"\b(?:up to|no more than|not more than|at most|maximum(?:\s+of)?|under|not to exceed)\s+"
    r"(?:(?P<prefix>[A-Za-z]{1,2})\$|(?P<code>USD|CAD|EUR|GBP|AUD|NZD)\s+)?\$?\s*"
    r"(?P<amount>[\d,]+(?:\.\d+)?)",
    re.IGNORECASE,
)
_DAYS = re.compile(r"\b(\d+)\s*-?\s*days?\b", re.IGNORECASE)
_DATE_RANGE = re.compile(
    r"\bfrom\s+(?P<m1>[A-Za-z]+)\s+(?P<d1>\d{1,2})(?:\s*,\s*(?P<y1>\d{4}))?"
    r"\s+to\s+(?P<m2>[A-Za-z]+)\s+(?P<d2>\d{1,2})(?:\s*,\s*(?P<y2>\d{4}))?",
    re.IGNORECASE,
)
_DESTINATION = re.compile(r"\btrip to\s+(.+?)\s+(?:for|from|in)\b", re.IGNORECASE)
_DESTINATION_DAYS = re.compile(r"\bdays\s+in\s+([A-Za-z]+)", re.IGNORECASE)
_TRAVEL_MONTH = re.compile(
    r"\b(?:in|next)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE,
)
_COUPLE = re.compile(
    r"\b(?:my wife and I|I and my wife|my husband and I|I and my husband)\b",
    re.IGNORECASE,
)
_SOLO = re.compile(r"\b(?:I'm|I am)\b", re.IGNORECASE)
_ADULTS = re.compile(rf"\b({_NUMBER})\s+adults?\b", re.IGNORECASE)
_CHILDREN = re.compile(rf"\b({_NUMBER})\s+(?:kids?|children|child)\b", re.IGNORECASE)
_CITIES = re.compile(
    r"\b(?:I|we) want(?:\s+to\s+visit)?\s+(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)
_STYLES = re.compile(
    r"\b(" + "|".join(style.value for style in TravelStyle) + r")\b",
    re.IGNORECASE,
)
_WALKING_WORD = re.compile(r"\b(low|moderate|high)\b", re.IGNORECASE)
_WALKING = re.compile(r"\bwalking\b", re.IGNORECASE)


def parse_trip_request(text: str) -> TripRequest:
    """Turn a short trip sentence into a validated TripRequest."""
    destination = _destination(text)
    days = _days(text)
    adults = _adults(text)
    budget = _budget(text)
    travel_style = _travel_style(text)
    walking_level = _walking_level(text)

    missing = [
        name
        for name, value in (
            ("destination", destination),
        )
        if value is None
    ]
    if missing:
        raise ValueError("missing " + ", ".join(missing))

    return TripRequest(
        destination=destination,
        days=days,
        adults=adults,
        children=_children(text),
        budget=budget,
        cities=_cities(text),
        requirements=_requirements(text),
        travel_style=travel_style,
        walking_level=walking_level,
    )


def _destination(text: str) -> str | None:
    match = _DESTINATION.search(text) or _DESTINATION_DAYS.search(text)
    if match is None:
        return None
    return match.group(1).strip()


def _days(text: str) -> int | None:
    match = _DAYS.search(text)
    if match is not None:
        return int(match.group(1))
    return _days_from_range(text)


def _days_from_range(text: str) -> int | None:
    match = _DATE_RANGE.search(text)
    if match is None:
        return None
    start = _to_date(match, "1")
    end = _to_date(match, "2")
    if start is None or end is None or end < start:
        return None
    return (end - start).days + 1


def _to_date(match: re.Match[str], which: str) -> date | None:
    month = _MONTHS.get(match.group(f"m{which}").lower())
    if month is None:
        return None
    year_raw = match.group(f"y{which}") or match.group("y1") or match.group("y2")
    year = date.today().year if year_raw is None else int(year_raw)
    try:
        return date(year, month, int(match.group(f"d{which}")))
    except ValueError:
        return None


def _count(raw: str) -> int:
    if raw.isdigit():
        return int(raw)
    return _WORD_NUMBERS[raw.lower()]


def _adults(text: str) -> int | None:
    match = _ADULTS.search(text)
    if match is not None:
        return _count(match.group(1))
    if _COUPLE.search(text):
        return 2
    if _SOLO.search(text):
        return 1
    return None


def _children(text: str) -> int | None:
    match = _CHILDREN.search(text)
    if match is not None:
        return _count(match.group(1))
    if _COUPLE.search(text) or _SOLO.search(text):
        return 0
    return None


def _requirements(text: str) -> Requirements:
    match = _TRAVEL_MONTH.search(text)
    if match is None:
        return Requirements()
    month = match.group(1).capitalize()
    return Requirements(hard_constraints=[f"travel in {month}"])


def _budget(text: str) -> Budget | None:
    ceiling = _CEILING.search(text)
    match = _BUDGET.search(text)
    if match is not None:
        amount = float(match.group("amount").replace(",", ""))
        code = match.group("code")
        prefix = match.group("prefix")
        if code is not None:
            currency = code
        elif prefix is not None:
            currency = _PREFIX_CURRENCY.get(prefix.lower())
        else:
            currency = None
        hedge = match.group("hedge")
        amount_at = match.start()
    else:
        coded = _BUDGET_CODE.search(text)
        if coded is None and ceiling is None:
            return None
        if coded is None:
            amount = None
            currency = None
            hedge = None
            amount_at = None
        else:
            amount = float(coded.group("amount").replace(",", ""))
            currency = coded.group("code")
            hedge = coded.group("hedge")
            amount_at = coded.start()
    maximum = None
    if ceiling is not None:
        maximum = float(ceiling.group("amount").replace(",", ""))
        if currency is None:
            currency = ceiling.group("code") or _PREFIX_CURRENCY.get((ceiling.group("prefix") or "").lower())
        if amount is not None and amount == maximum and amount_at is not None and amount_at >= ceiling.start():
            amount = None
    if amount is None and maximum is None:
        return None
    budget_type = BudgetType.APPROXIMATE if hedge else BudgetType.EXACT
    return Budget(amount=amount, maximum=maximum, currency=currency, type=budget_type)


def _cities(text: str) -> list[str]:
    match = _CITIES.search(text)
    if match is None:
        return []
    parts = re.split(r",|\band\b", match.group(1), flags=re.IGNORECASE)
    return [part.strip(" .") for part in parts if part.strip(" .")]


def _travel_style(text: str) -> str | None:
    match = _STYLES.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _walking_level(text: str) -> str | None:
    for match in _WALKING_WORD.finditer(text):
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        if _WALKING.search(text[start:end]):
            return match.group(1).lower()
    return None
