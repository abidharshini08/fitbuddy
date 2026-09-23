import json
from typing import Any

from google import genai
from pydantic import BaseModel

from .config import settings


class DayPlan(BaseModel):

    day: str
    focus: str
    warm_up: str
    exercises: list[str]
    cooldown: str


class WorkoutResponse(BaseModel):

    summary: str
    days: list[DayPlan]


class TipResponse(BaseModel):

    tip: str
    recovery_note: str


def _client():

    if not settings.gemini_api_key:
        return None

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def _generate_json(
    model: str,
    prompt: str,
    schema: dict[str, Any]
) -> str:

    client = _client()

    if client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )

    return response.text


def _fallback_plan(
    goal: str,
    intensity: str
) -> WorkoutResponse:

    level = {
        "low": "gentle",
        "medium": "moderate",
        "high": "challenging",
    }[intensity]

    focuses = [
        "Full Body",
        "Cardio",
        "Upper Body",
        "Recovery & Mobility",
        "Lower Body",
        "Core & Conditioning",
        "Active Recovery",
    ]

    exercise_sets = [

        [
            "Bodyweight squats: 3 x 10",
            "Incline push-ups: 3 x 8",
            "Glute bridges: 3 x 12",
        ],

        [
            "Brisk walk: 25 min",
            "Step-ups: 3 x 10/leg",
            "Easy cycling: 15 min",
        ],

        [
            "Push-ups or incline push-ups: 3 x 8",
            "Backpack rows: 3 x 10",
            "Shoulder taps: 3 x 10/side",
        ],

        [
            "Cat-cow: 2 x 8",
            "Hip flexor stretch: 2 x 30 sec/side",
            "Easy walk: 20 min",
        ],

        [
            "Squats: 3 x 10",
            "Reverse lunges: 3 x 8/leg",
            "Calf raises: 3 x 15",
        ],

        [
            "Dead bug: 3 x 8/side",
            "Mountain climbers: 3 x 20 sec",
            "Plank: 3 x 20 sec",
        ],

        [
            "Easy walk: 25 min",
            "Full-body stretching: 10 min",
            "Breathing: 5 min",
        ],
    ]

    days = []

    for i in range(7):

        days.append(
            DayPlan(
                day=f"Day {i + 1}",
                focus=focuses[i],
                warm_up=(
                    "5–10 min easy movement and "
                    "dynamic mobility."
                ),
                exercises=[
                    f"{exercise} ({level})"
                    for exercise in exercise_sets[i]
                ],
                cooldown=(
                    "5–10 min gentle stretching "
                    "and easy breathing."
                ),
            )
        )

    return WorkoutResponse(
        summary=(
            f"Starter {intensity}-intensity plan "
            f"for {goal}. Increase load or duration "
            "gradually as fitness improves."
        ),
        days=days,
    )


def generate_workout(user) -> str:

    schema = WorkoutResponse.model_json_schema()

    prompt = f"""
You are FitBuddy, a fitness-planning assistant.

Create a safe and practical 7-day workout plan.

User:
- Name: {user.name}
- Age: {user.age}
- Weight: {user.weight} kg
- Goal: {user.goal}
- Preferred intensity: {user.intensity}

Requirements:

- Return ONLY valid JSON.
- Follow the supplied schema exactly.
- Create exactly 7 days.
- Every day needs:
  - focus
  - warm-up
  - exercises
  - cooldown
- Include sets/repetitions or duration.
- Include recovery.
- Vary the workouts.
- Do not diagnose medical conditions.
- Do not prescribe medication.
- Do not encourage dangerous weight loss.
- Do not recommend extreme calorie restriction.
- Do not recommend training through serious pain.
- Keep recommendations general because no medical history is available.
"""

    try:

        raw = _generate_json(
            settings.workout_model,
            prompt,
            schema
        )

        validated = WorkoutResponse.model_validate_json(
            raw
        )

        return validated.model_dump_json(
            indent=2
        )

    except Exception:

        return _fallback_plan(
            user.goal,
            user.intensity
        ).model_dump_json(
            indent=2
        )


def generate_nutrition_tip(user) -> str:

    schema = TipResponse.model_json_schema()

    prompt = f"""
Create one concise nutrition or recovery recommendation
for this FitBuddy user.

Goal: {user.goal}
Intensity: {user.intensity}
Age: {user.age}
Weight: {user.weight} kg

Return ONLY valid JSON matching the supplied schema.

Keep it practical and general.

Do not:
- make medical claims
- prescribe supplements as necessities
- recommend extreme diets
- prescribe exact calorie targets
"""

    fallback = TipResponse(
        tip=(
            "Prioritize balanced meals with a protein source, "
            "vegetables or fruit, whole-food carbohydrates, "
            "and enough fluids."
        ),
        recovery_note=(
            "Sleep consistently and allow recovery days "
            "so training remains sustainable."
        ),
    )

    try:

        raw = _generate_json(
            settings.tip_model,
            prompt,
            schema
        )

        validated = TipResponse.model_validate_json(
            raw
        )

        return validated.model_dump_json(
            indent=2
        )

    except Exception:

        return fallback.model_dump_json(
            indent=2
        )


def update_workout(
    original_plan: str,
    feedback: str,
    user
) -> str:

    schema = WorkoutResponse.model_json_schema()

    prompt = f"""
You are revising an existing FitBuddy 7-day workout plan.

User goal:
{user.goal}

User intensity:
{user.intensity}

Original plan:
{original_plan}

User feedback:
{feedback}

Return ONLY valid JSON matching the supplied schema.

Requirements:

- Keep exactly 7 days.
- Apply the user's feedback.
- Preserve useful parts of the original plan.
- Maintain reasonable recovery.
- Avoid unsafe recommendations.
- Do not diagnose medical conditions.
"""

    try:

        raw = _generate_json(
            settings.workout_model,
            prompt,
            schema
        )

        validated = WorkoutResponse.model_validate_json(
            raw
        )

        return validated.model_dump_json(
            indent=2
        )

    except Exception:

        try:

            data = json.loads(
                original_plan
            )

            data["summary"] = (
                data.get("summary", "")
                + f" Revision requested: {feedback}"
            )

            return json.dumps(
                data,
                indent=2
            )

        except Exception:

            return original_plan


def ai_status():

    configured = bool(
        settings.gemini_api_key
    )

    return {
        "configured": configured,
        "workout_model": settings.workout_model,
        "tip_model": settings.tip_model,
        "mode": (
            "Gemini API"
            if configured
            else "Local fallback demo mode"
        ),
    }