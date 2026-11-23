from app.models.models import Requirements, TripRequest
from app.parse_request import parse_trip_request
from app.planner import plan_trip
from app.tools.destination_search import Tool


def test_plan_presents_catalog_activities():
    trip = TripRequest(
        destination="Japan",
        cities=["Tokyo"],
        requirements={"interests": ["technology"]},
    )

    plan = plan_trip(trip)

    assert plan.research_required is True
    assert plan.next_action == "present_activities"
    assert plan.reason == "Catalog activities matched Japan."
    assert [item.activity for item in plan.activities] == ["teamLab Planets"]
    assert plan.activities[0].matched_interests == ["technology"]


def test_plan_asks_for_a_new_destination_when_the_catalog_has_no_match():
    trip = TripRequest(destination="Mars")

    plan = plan_trip(trip)

    assert plan.research_required is True
    assert plan.next_action == "request_alternative_destination"
    assert plan.reason == "No catalog activities matched Mars."
    assert plan.activities == []


def test_plan_reason_when_catalog_destination_has_no_matching_activities():
    trip = TripRequest(
        destination="Japan",
        cities=["Tokyo"],
        requirements={"interests": ["scuba"]},
    )

    plan = plan_trip(trip)

    assert plan.research_required is True
    assert plan.next_action == "ask_interests"
    assert plan.activities == []
    assert plan.reason == "No activities matched the request for Japan."


def test_plan_sets_status_when_the_named_city_is_not_in_the_country():
    trip = parse_trip_request(
        "I want to visit Japan, specifically Atlantis City, for 5 days in December 2026.\n"
        "My interest is Japanese food."
    )

    plan = plan_trip(trip)

    assert trip.destination == "Japan"
    assert trip.cities == ["Atlantis City"]
    assert trip.requirements.interests == ["Japanese food"]
    assert plan.next_action == "request_alternative_city"
    assert plan.activities == []


def test_plan_does_not_call_the_tool_without_a_destination():
    trip = TripRequest.model_construct(
        destination="",
        cities=[],
        requirements=Requirements(),
    )

    def fail(_arguments: dict) -> list:
        raise AssertionError("destination_search was called")

    plan = plan_trip(trip, tool=Tool(name="destination_search", description="", execute=fail))

    assert plan.research_required is False
    assert plan.next_action == "skip_research"
    assert plan.activities == []
