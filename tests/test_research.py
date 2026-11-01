import json

from app.models.models import DestinationResearchRequest, TripRequest
from app.research import request_from_trip, results_from_text


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


def test_results_from_text_reads_an_activity_list():
    payload = json.dumps(
        [
            {
                "city": " Tokyo ",
                "activity": "Tsukiji outer market",
                "category": "food",
                "description": " Walk the stalls and taste street food. ",
            }
        ]
    )

    results = results_from_text(payload)

    assert len(results) == 1
    assert results[0].city == "Tokyo"
    assert results[0].activity == "Tsukiji outer market"
    assert results[0].category == "food"
    assert results[0].description == "Walk the stalls and taste street food."
