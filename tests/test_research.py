from app.models.models import DestinationResearchRequest, DestinationResearchStatus, TripRequest
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

    output = research_destination(request)

    assert output.status == DestinationResearchStatus.MATCHED
    assert output.reason == "Catalog activities matched Japan."
    assert [item.activity for item in output.activities] == ["teamLab Planets"]
    assert output.activities[0].matched_interests == ["technology"]
    assert output.activities[0].status == DestinationResearchStatus.MATCHED


def test_research_status_when_nothing_matches():
    missing = research_destination(DestinationResearchRequest(destination="Mars"))
    filtered = research_destination(
        DestinationResearchRequest(
            destination="Japan",
            cities=["Tokyo"],
            interests=["scuba"],
        )
    )

    assert missing.status == DestinationResearchStatus.DESTINATION_NOT_FOUND
    assert missing.activities == []
    assert filtered.status == DestinationResearchStatus.NO_INTEREST_MATCH
    assert filtered.activities
    assert {item.status for item in filtered.activities} == {DestinationResearchStatus.NO_INTEREST_MATCH}
