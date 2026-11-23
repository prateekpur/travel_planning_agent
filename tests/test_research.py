from app.models.models import DestinationResearchRequest, TripRequest
from app.research import request_from_trip, research_destination


def test_request_from_trip_uses_destination_cities_and_interests():
    trip = TripRequest(
        destination="Japan",
        cities=["Tokyo", "Kyoto"],
        requirements={"interests": ["Japanese food", "technology"]},
    )

    request = request_from_trip(trip)

    assert request.destination == "Japan"
    assert request.cities == ["Tokyo", "Kyoto"]
    assert request.interests == ["Japanese food", "technology"]


def test_research_request_drops_blank_names():
    request = DestinationResearchRequest(
        destination=" Italy ",
        cities=[" Rome ", ""],
        interests=[" food "],
    )

    assert request.destination == "Italy"
    assert request.cities == ["Rome"]
    assert request.interests == ["food"]


def test_research_destination_reads_the_catalog():
    request = DestinationResearchRequest(
        destination="Japan",
        cities=["Tokyo"],
        interests=["technology"],
    )

    results = research_destination(request)

    assert [item.activity for item in results] == ["teamLab Planets"]
    assert results[0].matched_interests == ["technology"]
