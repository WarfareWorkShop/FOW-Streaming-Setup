from __future__ import annotations

import base64
import io

import pytest

from backend.models import MatchStatus


@pytest.fixture
def auth_header(user_factory):
    user = user_factory("commander", "commander@example.com")
    token = user.get_token()
    return {"Authorization": f"Bearer {token}"}, user


def test_create_ai_match_and_execute_turn(client, auth_header, monkeypatch):
    headers, user = auth_header

    response = client.post(
        "/api/matches",
        json={"name": "Escaramuza", "opponent_type": "ai"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    match_id = data["match"]["id"]
    assert data["match"]["status"] == MatchStatus.ACTIVE.value

    # Force deterministic AI behaviour
    monkeypatch.setattr("backend.game_engine.random.randint", lambda *args, **kwargs: 2)
    monkeypatch.setattr("backend.game_engine.random.choice", lambda seq: seq[0])

    action_response = client.post(
        f"/api/matches/{match_id}/actions",
        json={"action": {"type": "attack", "intensity": 3}},
        headers=headers,
    )

    assert action_response.status_code == 200
    payload = action_response.get_json()
    assert payload["state"]["turn"] in {"player", "completed"}
    assert payload["match"]["events"]


def test_invitation_flow(client, user_factory):
    host = user_factory("host", "host@example.com")
    guest = user_factory("guest", "guest@example.com")
    host_headers = {"Authorization": f"Bearer {host.get_token()}"}
    guest_headers = {"Authorization": f"Bearer {guest.get_token()}"}

    create_resp = client.post(
        "/api/matches",
        json={"name": "Batalla", "opponent_type": "human", "invitee_username": "guest"},
        headers=host_headers,
    )
    assert create_resp.status_code == 201
    match_id = create_resp.get_json()["match"]["id"]

    accept_resp = client.post(
        f"/api/matches/{match_id}/accept",
        headers=guest_headers,
    )
    assert accept_resp.status_code == 200
    match_data = accept_resp.get_json()["match"]
    assert match_data["status"] == MatchStatus.ACTIVE.value
    assert any(p["user"]["username"] == "guest" for p in match_data["participants"])


def test_dice_scan_endpoint(client, auth_header, monkeypatch):
    headers, _ = auth_header

    fake_preview = base64.b64encode(b"preview").decode("ascii")
    monkeypatch.setattr(
        "backend.app.analyse_dice_image",
        lambda _: {"pip_count": 4, "bounding_boxes": [], "preview_image": fake_preview},
    )

    response = client.post(
        "/api/dice/scan",
        data={"image": (io.BytesIO(b"fake"), "test.jpg")},
        content_type="multipart/form-data",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.get_json()["pip_count"] == 4
