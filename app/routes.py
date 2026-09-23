import json
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .ai_service import (
    ai_status,
    generate_nutrition_tip,
    generate_workout,
    update_workout,
)

from .config import settings

from .database import (
    delete_user,
    get_all_users_with_plans,
    get_latest_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)

from .schemas import (
    FeedbackRequest,
    UserInput,
)


router = APIRouter()


TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "templates"
)


templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


def render_template(
    request: Request,
    template_name: str,
    context: dict,
    status_code: int = 200,
):
    """
    Render a Jinja2 template using the current
    Starlette/FastAPI TemplateResponse syntax.
    """

    context = {
        "request": request,
        **context,
    }

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
        status_code=status_code,
    )


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):

    return render_template(
        request,
        "index.html",
        {
            "ai": ai_status(),
        },
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout_route(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):

    try:

        data = UserInput(
            user_id=user_id,
            name=username,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )

    except Exception as exc:

        return render_template(
            request,
            "index.html",
            {
                "error": str(exc),
                "ai": ai_status(),
            },
            status_code=422,
        )

    user = save_user(
        **data.model_dump()
    )

    workout = generate_workout(
        user
    )

    tip = generate_nutrition_tip(
        user
    )

    plan = save_plan(
        user.id,
        workout,
        tip,
    )

    return render_template(
        request,
        "result.html",
        {
            "user": user,
            "plan": plan,
            "workout": workout,
            "tip": tip,
            "updated": False,
        },
    )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
):

    try:

        payload = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    user = get_user(
        payload.user_id
    )

    plan = get_latest_plan(
        payload.user_id
    )

    if not user or not plan:

        raise HTTPException(
            status_code=404,
            detail="User or workout plan not found.",
        )

    revised = update_workout(
        plan.original_plan,
        payload.feedback,
        user,
    )

    revised_tip = generate_nutrition_tip(
        user
    )

    update_plan(
        plan.id,
        payload.feedback,
        revised,
        revised_tip,
    )

    plan = get_latest_plan(
        payload.user_id
    )

    return render_template(
        request,
        "result.html",
        {
            "user": user,
            "plan": plan,
            "workout": plan.updated_plan,
            "tip": plan.updated_tip,
            "updated": True,
        },
    )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(
    request: Request,
    admin_key: str = "",
):

    if admin_key != settings.admin_key:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key.",
        )

    records = get_all_users_with_plans()

    return render_template(
        request,
        "all_users.html",
        {
            "records": records,
        },
    )


@router.post(
    "/delete-user",
)
def delete_user_route(
    user_id: str = Form(...),
    admin_key: str = Form(...),
):

    if admin_key != settings.admin_key:

        raise HTTPException(
            status_code=403,
            detail="Invalid admin key.",
        )

    delete_user(user_id)

    return RedirectResponse(
        url=(
            "/view-all-users"
            f"?admin_key={admin_key}"
        ),
        status_code=303,
    )


@router.get(
    "/api/health",
)
def health():

    return {
        "status": "ok",
        "service": "FitBuddy",
        "ai": ai_status(),
    }


@router.get(
    "/api/users/{user_id}",
)
def user_api(
    user_id: str,
):

    user = get_user(
        user_id
    )

    plan = get_latest_plan(
        user_id
    )

    if not user or not plan:

        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
        },

        "plan": {
            "original": json.loads(
                plan.original_plan
            ),

            "original_tip": json.loads(
                plan.original_tip
            ),

            "updated": (
                json.loads(
                    plan.updated_plan
                )
                if plan.updated_plan
                else None
            ),

            "updated_tip": (
                json.loads(
                    plan.updated_tip
                )
                if plan.updated_tip
                else None
            ),

            "feedback": plan.feedback,
        },
    }