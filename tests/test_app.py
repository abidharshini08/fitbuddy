from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    assert "FitBuddy" in response.text


def test_health():

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "ok"
    )


def test_generate_without_api_key():

    response = client.post(
        "/generate-workout",
        data={
            "username": "Test User",
            "user_id": "test-user-001",
            "age": "21",
            "weight": "70",
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )

    assert response.status_code == 200

    assert "Workout Plan" in response.text

    assert "Test User" in response.text