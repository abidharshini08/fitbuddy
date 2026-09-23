from pathlib import Path

from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routes import router


BASE_DIR = Path(
    __file__
).resolve().parent

PROJECT_DIR = BASE_DIR.parent


app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description=(
        "AI-powered personalized fitness "
        "planning application."
    ),
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=PROJECT_DIR / "static"
    ),
    name="static",
)


app.include_router(
    router
)


@app.on_event("startup")
def startup():

    init_db()