from app.clarify import apply_answer, clarifying_questions, fill_missing
from app.models.models import TravelStyle, TripRequest, WalkingLevel


def test_complete_request_has_no_questions():
    trip = TripRequest(
        destination="Japan",
        days=7,
        adults=2,
        children=2,
        budget=6000,
        currency="CAD",
        cities=["Tokyo", "Kyoto"],
        travel_style="relaxed",
        walking_level="moderate",
    )

    assert clarifying_questions(trip) == []


def test_missing_fields_become_questions():
    trip = TripRequest(destination="Japan", budget=6000)

    prompts = {question.field: question.prompt for question in clarifying_questions(trip)}

    assert set(prompts) == {
        "days",
        "adults",
        "children",
        "currency",
        "cities",
        "travel_style",
        "walking_level",
    }
    assert "days" in prompts["days"].lower()
    assert "currency" in prompts["currency"].lower()


def test_apply_budget_answer_also_sets_currency():
    trip = apply_answer(TripRequest(destination="Japan"), "budget", "C$6,000")

    assert trip.budget == 6000
    assert trip.currency == "CAD"


def test_apply_city_style_and_walking_answers():
    trip = TripRequest(destination="Japan")
    trip = apply_answer(trip, "cities", "Tokyo and Kyoto")
    trip = apply_answer(trip, "travel_style", "a relaxed trip")
    trip = apply_answer(trip, "walking_level", "moderate walking")

    assert trip.cities == ["Tokyo", "Kyoto"]
    assert trip.travel_style == TravelStyle.RELAXED
    assert trip.walking_level == WalkingLevel.MODERATE


def test_blank_answer_leaves_the_field_empty():
    trip = TripRequest(destination="Japan")

    assert apply_answer(trip, "days", "  ").days is None


def test_fill_missing_retries_an_invalid_answer():
    answers = iter(["zero", "7", "two", "0", "6000 CAD", "Tokyo", "relaxed", "high"])

    trip = fill_missing(TripRequest(destination="Japan"), lambda: next(answers))

    assert trip.days == 7
    assert trip.adults == 2
    assert trip.children == 0
    assert trip.budget == 6000
    assert trip.currency == "CAD"
    assert trip.cities == ["Tokyo"]
    assert trip.travel_style == TravelStyle.RELAXED
    assert trip.walking_level == WalkingLevel.HIGH
