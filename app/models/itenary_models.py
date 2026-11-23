from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.models import DestinationResearchOutput, TravelSpecification

class PlannedActivity(BaseModel):
    activity: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    city: str = Field(min_length=1)
    matched_interests: list[str] = Field(default_factory=list)

    @field_validator("activity", "category", "description", "city")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("matched_interests", mode="before")
    @classmethod
    def empty_matched_interests(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return value


class ItineraryDay(BaseModel):
    day: int = Field(ge=1)
    city: str = Field(min_length=1)
    theme: str = Field(min_length=1)
    activities: list[PlannedActivity] = Field(default_factory=list)

    @field_validator("day", mode="before")
    @classmethod
    def positive_day(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("day must be positive")
        return value


class TravelItinerary(BaseModel):
    destination: str = Field(min_length=1)
    total_days: int = Field(ge=1)
    days: list[ItineraryDay] = Field(default_factory=list)


class ItineraryPlanningRequest(BaseModel):
    specification: TravelSpecification
    research_results: DestinationResearchOutput