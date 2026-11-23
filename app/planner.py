from pydantic import BaseModel, Field

from app.models.models import DestinationResearchResult, DestinationResearchStatus, TripRequest
from app.tools.destination_search import Tool, destination_search_tool


class TripPlan(BaseModel):
    research_required: bool
    next_action: str
    reason: str = ""
    activities: list[DestinationResearchResult] = Field(default_factory=list)


def plan_trip(trip: TripRequest, tool: Tool = destination_search_tool) -> TripPlan:
    """Decide whether research is required, then invoke the destination_search tool."""
    if tool.name != "destination_search":
        raise ValueError("The planner calls the destination_search tool.")

    destination = (trip.destination or "").strip()
    if not destination:
        return TripPlan(
            research_required=False,
            next_action="skip_research",
            reason="A destination is required before research.",
        )

    requirements = trip.requirements
    interests = list(requirements.interests) if requirements is not None else []
    outcome = tool.execute(
        {
            "destination": destination,
            "cities": list(trip.cities or []),
            "interests": interests,
        }
    )
    activities = _activities_for_plan(outcome.activities, interests)
    if outcome.status is DestinationResearchStatus.DESTINATION_NOT_FOUND:
        return TripPlan(
            research_required=True,
            next_action="request_alternative_destination",
            reason=outcome.reason,
            activities=activities,
        )
    if outcome.status is DestinationResearchStatus.CITY_NOT_FOUND:
        return TripPlan(
            research_required=True,
            next_action="request_alternative_city",
            reason=outcome.reason,
            activities=activities,
        )
    if outcome.status is DestinationResearchStatus.NO_INTEREST_MATCH:
        return TripPlan(
            research_required=True,
            next_action="ask_interests",
            reason=f"No activities matched the request for {destination}.",
            activities=activities,
        )
    if outcome.status is not DestinationResearchStatus.MATCHED:
        return TripPlan(
            research_required=True,
            next_action="skip_research",
            reason=outcome.reason,
            activities=activities,
        )

    return TripPlan(
        research_required=True,
        next_action="present_activities",
        reason=outcome.reason,
        activities=activities,
    )


def _activities_for_plan(
    activities: list[DestinationResearchResult],
    interests: list[str],
) -> list[DestinationResearchResult]:
    if not interests:
        return activities
    return [
        activity
        for activity in activities
        if activity.status is not DestinationResearchStatus.NO_INTEREST_MATCH
    ]
