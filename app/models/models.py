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


class TripRequest(BaseModel):
    destination: str = Field(min_length=1, description="Country or region")
    days: int | None = Field(default=None, ge=1)
    adults: int | None = Field(default=None, ge=1)
    children: int | None = Field(default=None, ge=0)
    budget: float | None = Field(default=None, gt=0)
    currency: str | None = Field(
        default=None, min_length=3, max_length=3, description="ISO 4217 code"
    )
    cities: list[str] = Field(default_factory=list)
    travel_style: TravelStyle | None = None
    walking_level: WalkingLevel | None = None

    @field_validator("destination")
    @classmethod
    def strip_destination(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("destination must not be blank")
        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        code = value.strip().upper()
        if len(code) != 3 or not code.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return code

    @field_validator("cities")
    @classmethod
    def clean_cities(cls, value: list[str]) -> list[str]:
        return [city.strip() for city in value if city.strip()]
