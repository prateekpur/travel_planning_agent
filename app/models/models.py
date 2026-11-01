from enum import Enum

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("city", "activity", "category", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


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
