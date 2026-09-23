from pydantic import BaseModel, Field, field_validator


ALLOWED_GOALS = {
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
    "strength",
}


ALLOWED_INTENSITIES = {
    "low",
    "medium",
    "high",
}


class UserInput(BaseModel):

    user_id: str = Field(
        min_length=1,
        max_length=80
    )

    name: str = Field(
        min_length=1,
        max_length=120
    )

    age: int = Field(
        ge=13,
        le=100
    )

    weight: float = Field(
        gt=20,
        lt=400
    )

    goal: str

    intensity: str

    @field_validator("goal")
    @classmethod
    def normalize_goal(cls, value: str) -> str:

        value = value.strip().lower()

        if value not in ALLOWED_GOALS:
            raise ValueError(
                "Invalid fitness goal."
            )

        return value

    @field_validator("intensity")
    @classmethod
    def normalize_intensity(cls, value: str) -> str:

        value = value.strip().lower()

        if value not in ALLOWED_INTENSITIES:
            raise ValueError(
                "Intensity must be low, medium, or high."
            )

        return value


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=1,
        max_length=80
    )

    feedback: str = Field(
        min_length=3,
        max_length=2000
    )