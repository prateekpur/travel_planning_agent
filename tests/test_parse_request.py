from app.models.models import TravelStyle, WalkingLevel
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
    assert trip.budget == 6000
    assert trip.currency == "CAD"
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
    assert trip.budget == 6000
    assert trip.currency == "CAD"
    assert trip.cities == ["Tokyo", "Kyoto"]
    assert trip.travel_style == TravelStyle.RELAXED
    assert trip.walking_level == WalkingLevel.MODERATE


def test_date_range_request_without_style_names_missing_fields():
    try:
        parse_trip_request(DATE_EXAMPLE)
    except ValueError as exc:
        assert str(exc) == "missing travel_style, walking_level"
    else:
        raise AssertionError("expected ValueError")
