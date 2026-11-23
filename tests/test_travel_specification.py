from app.models.models import (
    Budget,
    PlanningReadiness,
    TravelSpecification,
    TravelStyle,
    TripRequest,
    WalkingLevel,
)


def test_trip_request_becomes_a_ready_specification():
    trip = TripRequest(
        destination=" Japan ",
        days=7,
        adults=2,
        children=0,
        budget=Budget(amount=6000, currency="cad", type="exact"),
        cities=["Tokyo", "Kyoto"],
        travel_style="relaxed",
        walking_level="moderate",
        requirements={
            "interests": [" Japanese food ", ""],
            "hard_constraints": [" travel in December "],
            "soft_preferences": [" prefer trains "],
        },
    )

    specification = TravelSpecification.from_trip(trip)

    assert specification.destination == "Japan"
    assert specification.total_days == 7
    assert specification.adults == 2
    assert specification.children == 0
    assert specification.budget is not None
    assert specification.budget.amount == 6000
    assert specification.budget.currency == "CAD"
    assert specification.cities == ["Tokyo", "Kyoto"]
    assert specification.travel_style == TravelStyle.RELAXED
    assert specification.walking_level == WalkingLevel.MODERATE
    assert specification.interests == ["Japanese food"]
    assert specification.hard_constraints == ["travel in December"]
    assert specification.soft_preferences == ["prefer trains"]
    assert specification.planning_readiness == PlanningReadiness.READY


def test_missing_trip_details_need_information():
    specification = TravelSpecification.from_trip(TripRequest(destination="Japan"))

    assert specification.total_days is None
    assert specification.interests == []
    assert specification.hard_constraints == []
    assert specification.soft_preferences == []
    assert specification.planning_readiness == PlanningReadiness.NEEDS_INFORMATION
