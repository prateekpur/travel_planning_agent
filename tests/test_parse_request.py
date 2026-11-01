from app.models.models import BudgetType, TravelStyle, WalkingLevel
from app.parse_request import parse_trip_request

EXAMPLE = """Plan a 7-day trip to Japan for 2 adults and 2 kids.
Budget is $6000 CAD.
I want Tokyo and Kyoto.
I prefer a relaxed trip with moderate walking."""


def test_parse_japan_example():
    trip = parse_trip_request(EXAMPLE)

    assert trip.destination == "Japan"
    assert trip.days == 7
    assert trip.adults == 2
    assert trip.children == 2
    assert trip.budget is not None
    assert trip.budget.amount == 6000
    assert trip.budget.currency == "CAD"
    assert trip.budget.type == BudgetType.EXACT
    assert trip.budget.includes == []
    assert trip.budget.excludes == []
    assert trip.cities == ["Tokyo", "Kyoto"]
    assert trip.travel_style == TravelStyle.RELAXED
    assert trip.walking_level == WalkingLevel.MODERATE


DATE_EXAMPLE = """We're planning a trip to Japan from March 15 to March 22, 2027.
There will be 4 of us, two adults and two children.
Our budget is around C$6,000.
We want to visit Tokyo and Kyoto."""


def test_date_range_request_reads_stated_fields():
    trip = parse_trip_request(
        DATE_EXAMPLE + "\nI prefer a relaxed trip with moderate walking."
    )

    assert trip.destination == "Japan"
    assert trip.days == 8
    assert trip.adults == 2
    assert trip.children == 2
    assert trip.budget is not None
    assert trip.budget.amount == 6000
    assert trip.budget.currency == "CAD"
    assert trip.budget.type == BudgetType.APPROXIMATE
    assert trip.cities == ["Tokyo", "Kyoto"]
    assert trip.travel_style == TravelStyle.RELAXED
    assert trip.walking_level == WalkingLevel.MODERATE


def test_date_range_request_allows_missing_style_and_walking():
    trip = parse_trip_request(DATE_EXAMPLE)

    assert trip.destination == "Japan"
    assert trip.days == 8
    assert trip.adults == 2
    assert trip.children == 2
    assert trip.budget is not None
    assert trip.budget.amount == 6000
    assert trip.budget.currency == "CAD"
    assert trip.budget.type == BudgetType.APPROXIMATE
    assert trip.cities == ["Tokyo", "Kyoto"]
    assert trip.travel_style is None
    assert trip.walking_level is None


def test_request_without_budget_or_currency():
    trip = parse_trip_request(
        "Plan a 7-day trip to Japan for 2 adults. I want Tokyo."
    )

    assert trip.destination == "Japan"
    assert trip.days == 7
    assert trip.adults == 2
    assert trip.children is None
    assert trip.budget is None
    assert trip.cities == ["Tokyo"]


def test_simple_couple():
    trip = parse_trip_request(
        "My wife and I want to spend 7 days in Italy in June. "
        "We have about C$5,000 to spend."
    )

    assert trip.destination == "Italy"
    assert trip.days == 7
    assert trip.adults == 2
    assert trip.children == 0
    assert trip.budget is not None
    assert trip.budget.amount == 5000
    assert trip.budget.currency == "CAD"
    assert trip.budget.type == BudgetType.APPROXIMATE
    assert trip.requirements.hard_constraints == ["travel in June"]


def test_budget_ceiling_is_separate_from_the_amount():
    trip = parse_trip_request(
        "Plan a 7-day trip to Japan for 2 adults. "
        "Budget is about C$5,000, no more than C$6,000."
    )

    assert trip.budget is not None
    assert trip.budget.amount == 5000
    assert trip.budget.maximum == 6000
    assert trip.budget.currency == "CAD"
    assert trip.budget.type == BudgetType.APPROXIMATE


def test_budget_ceiling_without_a_target_amount():
    trip = parse_trip_request("Plan a trip to Japan for sightseeing. Budget is up to C$4,000.")

    assert trip.budget is not None
    assert trip.budget.amount is None
    assert trip.budget.maximum == 4000
    assert trip.budget.currency == "CAD"


def test_solo_traveler():
    trip = parse_trip_request(
        "I'm planning a 5-day trip to New York in September with a budget of USD 2,000."
    )

    assert trip.adults == 1
    assert trip.children == 0
    assert trip.days == 5
    assert trip.destination == "New York"
    assert trip.budget is not None
    assert trip.budget.amount == 2000
    assert trip.budget.currency == "USD"
    assert trip.budget.type == BudgetType.EXACT


def test_request_without_days_or_people():
    trip = parse_trip_request("Plan a trip to Japan for sightseeing. I want Tokyo.")

    assert trip.destination == "Japan"
    assert trip.days is None
    assert trip.adults is None
    assert trip.children is None
    assert trip.cities == ["Tokyo"]
