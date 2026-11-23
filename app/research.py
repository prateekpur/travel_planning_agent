from app.models.models import (
    DestinationResearchOutput,
    DestinationResearchRequest,
    TripRequest,
)
from app.tools.destination_search import search_destination


def request_from_trip(trip: TripRequest) -> DestinationResearchRequest:
    """Build a research request from the cities and interests on a trip."""
    return DestinationResearchRequest(
        destination=trip.destination,
        cities=trip.cities,
        interests=trip.requirements.interests,
    )


def research_destination(request: DestinationResearchRequest) -> DestinationResearchOutput:
    """Look up catalog activities that match the destination request."""
    return search_destination(
        destination=request.destination,
        cities=request.cities,
        interests=request.interests,
    )
