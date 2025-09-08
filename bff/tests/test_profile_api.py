import pytest
from fastapi.testclient import TestClient

import bff.main as bff_main


@pytest.fixture
def client():
    return TestClient(bff_main.app)


def test_get_profile_unauthorized(client):
    resp = client.get("/api/volunteer/00000000-0000-0000-0000-000000000000/profile")
    assert resp.status_code == 401


def test_get_profile_success(monkeypatch, client):
    sample_profile = {
        "id": "11111111-1111-1111-1111-111111111111",
        "userId": "11111111-1111-1111-1111-111111111111",
        "name": "Test User",
        "email": "test@example.com",
        "phone": None,
        "location": "Remote",
        "skills": ["Python"],
        "interests": ["Research"],
        "availability": {"weekdays": True, "weekends": False, "evenings": False},
        "profileImageUrl": None,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": None,
    }

    async def fake_get_profile(auth_header):
        assert auth_header.startswith("Bearer ")
        return sample_profile

    monkeypatch.setattr(bff_main.auth_adapter, "get_profile", fake_get_profile)

    resp = client.get(
        "/api/volunteer/11111111-1111-1111-1111-111111111111/profile",
        headers={"Authorization": "Bearer dummy"},
    )
    assert resp.status_code == 200
    assert resp.json() == sample_profile


def test_put_profile_success(monkeypatch, client):
    call = {"args": None}

    async def fake_update_profile(auth_header, data):
        call["args"] = {"auth_header": auth_header, "data": data}
        # Echo back as saved profile payload
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            "userId": "22222222-2222-2222-2222-222222222222",
            "name": data.get("name", ""),
            "email": data.get("email", "test@example.com"),
            "phone": data.get("phone"),
            "location": data.get("location"),
            "skills": data.get("skills", []),
            "interests": data.get("interests", []),
            "availability": data.get("availability"),
            "profileImageUrl": data.get("profileImageUrl"),
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
        }

    monkeypatch.setattr(bff_main.auth_adapter, "update_profile", fake_update_profile)

    payload = {
        "name": "Updated User",
        "email": "updated@example.com",
        "location": "Amman, Jordan",
        "skills": ["Python", "FastAPI"],
        "interests": ["Research"],
        "availability": {"weekdays": True},
    }

    resp = client.put(
        "/api/volunteer/22222222-2222-2222-2222-222222222222/profile",
        headers={"Authorization": "Bearer dummy"},
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "22222222-2222-2222-2222-222222222222"
    assert data["profile"]["name"] == "Updated User"
    assert data["message"].lower().startswith("profile updated")

    # Ensure BFF forwarded Authorization and payload
    assert call["args"]["auth_header"] == "Bearer dummy"
    assert call["args"]["data"]["name"] == "Updated User"
