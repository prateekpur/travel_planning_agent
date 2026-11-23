from app.models.models import (
    DestinationResearchRequest,
    DestinationResearchResult,
    TripRequest,
)
from app.tools.destination_search import destination_search


def request_from_trip(trip: TripRequest) -> DestinationResearchRequest:
    """Build a research request from the cities and interests on a trip."""
    return DestinationResearchRequest(
        destination=trip.destination,
        cities=trip.cities,
        interests=trip.requirements.interests,
    )


def research_destination(request: DestinationResearchRequest) -> list[DestinationResearchResult]:
    """Look up catalog activities that match the destination request."""
    return destination_search(
        destination=request.destination,
        cities=request.cities,
        interests=request.interests,
    )
