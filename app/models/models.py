from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class TravelStyle(str, Enum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    LUXURY = "luxury"


class WalkingLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class BudgetType(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"


class PlanningReadiness(str, Enum):
    READY = "ready"
    NEEDS_INFORMATION = "needs_information"


class DestinationResearchStatus(str, Enum):
    PENDING = "pending"
    DESTINATION_NOT_FOUND = "destination_not_found"
    CITY_NOT_FOUND = "city_not_found"
    NO_INTEREST_MATCH = "no_interest_match"
    NO_ACTIVITIES = "no_activities"
    MATCHED = "matched"
    ERROR = "error"

class Requirements(BaseModel):
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)

    @field_validator("hard_constraints", "soft_preferences", "interests", mode="before")
    @classmethod
    def empty_list(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return value

    @field_validator("hard_constraints", "soft_preferences", "interests")
    @classmethod
    def clean_phrases(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class Budget(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    maximum: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3, description="ISO 4217 code")
    type: BudgetType | None = None
    includes: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        code = value.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return code

    @field_validator("includes", "excludes")
    @classmethod
    def clean_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class DestinationResearchRequest(BaseModel):
    destination: str = Field(min_length=1)
    cities: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)

    @field_validator("destination")
    @classmethod
    def strip_destination_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("destination must not be blank")
        return cleaned

    @field_validator("cities", "interests", mode="before")
    @classmethod
    def empty_names(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return value

    @field_validator("cities", "interests")
    @classmethod
    def clean_names(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class DestinationResearchResult(BaseModel):
    city: str = Field(min_length=1)
    activity: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    matched_interests: list[str] = Field(default_factory=list)
    status: DestinationResearchStatus = Field(default=DestinationResearchStatus.PENDING)

    @field_validator("city", "activity", "category", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def matched_result_has_details(self) -> "DestinationResearchResult":
        if self.status is not DestinationResearchStatus.MATCHED:
            return self
        missing = [
            name
            for name in ("city", "activity", "category", "description")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError("matched activity is missing " + ", ".join(missing))
        return self

    @field_validator("matched_interests", mode="before")
    @classmethod
    def empty_matched_interests(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return value

    @field_validator("matched_interests")
    @classmethod
    def clean_matched_interests(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]


class DestinationResearchOutput(BaseModel):
    status: DestinationResearchStatus
    reason: str = Field(min_length=1)
    activities: list[DestinationResearchResult] = Field(default_factory=list)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("reason must not be blank")
        return cleaned

    @field_validator("activities", mode="before")
    @classmethod
    def empty_activities(cls, value: list[DestinationResearchResult] | None) -> list:
        if value is None:
            return []
        return value


class TripRequest(BaseModel):
    destination: str = Field(min_length=1, description="Country or region")
    days: int | None = Field(default=None, ge=1)
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    budget: Budget | None = None
    cities: list[str] = Field(default_factory=list)
    travel_style: TravelStyle | None = None
    walking_level: WalkingLevel | None = None
    requirements: Requirements = Field(default_factory=Requirements)

    @field_validator("destination")
    @classmethod
    def strip_destination(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("destination must not be blank")
        return cleaned

    @field_validator("cities")
    @classmethod
    def clean_cities(cls, value: list[str]) -> list[str]:
        return [city.strip() for city in value if city.strip()]

    @field_validator("requirements", mode="before")
    @classmethod
    def empty_requirements(cls, value: Requirements | dict | None) -> Requirements | dict:
        if value is None:
            return {}
        return value


class TravelSpecification(BaseModel):
    destination: str = Field(min_length=1, description="Country or region")
    total_days: int | None = Field(default=None, ge=1)
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    budget: Budget | None = None
    cities: list[str] = Field(default_factory=list)
    travel_style: TravelStyle | None = None
    walking_level: WalkingLevel | None = None
    interests: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    planning_readiness: PlanningReadiness = PlanningReadiness.NEEDS_INFORMATION

    @field_validator("destination")
    @classmethod
    def strip_destination_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("destination must not be blank")
        return cleaned

    @field_validator("cities", "interests", "hard_constraints", "soft_preferences", mode="before")
    @classmethod
    def empty_phrases(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return value

    @field_validator("cities", "interests", "hard_constraints", "soft_preferences")
    @classmethod
    def clean_phrases(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]

    @model_validator(mode="after")
    def set_planning_readiness(self) -> "TravelSpecification":
        budget_ready = (
            self.budget is not None
            and self.budget.amount is not None
            and self.budget.currency is not None
        )
        ready = all(
            (
                self.total_days is not None,
                self.adults is not None,
                self.children is not None,
                budget_ready,
                bool(self.cities),
                self.travel_style is not None,
                self.walking_level is not None,
            )
        )
        self.planning_readiness = (
            PlanningReadiness.READY if ready else PlanningReadiness.NEEDS_INFORMATION
        )
        return self

    @classmethod
    def from_trip(cls, trip: TripRequest) -> "TravelSpecification":
        requirements = trip.requirements
        return cls(
            destination=trip.destination,
            total_days=trip.days,
            adults=trip.adults,
            children=trip.children,
            budget=trip.budget,
            cities=list(trip.cities),
            travel_style=trip.travel_style,
            walking_level=trip.walking_level,
            interests=list(requirements.interests),
            hard_constraints=list(requirements.hard_constraints),
            soft_preferences=list(requirements.soft_preferences),
        )
