from datetime import date
from fastapi import status
from fastapi.testclient import TestClient


def auth_header(client: TestClient):
    payload = {
        "id": 0,
        "username": "cuser",
        "email": "cuser@example.com",
        "avatar": "",
        "password": "secret12345"
    }
    client.post("/api/v1/auth/signup", json=payload)
    # confirm email
    from jose import jwt
    from app.conf.config import app_settings
    token = jwt.encode({"sub": payload["email"]}, app_settings.SECRET_KEY)
    client.get(f"/api/v1/auth/confirmed_email/{token}")
    # login
    resp = client.post("/api/v1/auth/login", data={"username": payload["email"], "password": payload["password"]})
    tokens = resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_contacts_crud(client: TestClient):
    headers = auth_header(client)

    c = {
        "first_name": "Rick",
        "last_name": "Sanchez",
        "email": "rick@example.com",
        "phone": "111",
        "birthday": date(1980,1,1).isoformat(),
        "extra": None,
        "user_id": 1
    }
    r = client.post("/api/v1/contacts/", json=c, headers=headers)
    assert r.status_code == status.HTTP_201_CREATED
    created = r.json()

    r = client.get(f"/api/v1/contacts/{created['id']}", headers=headers)
    assert r.status_code == status.HTTP_200_OK

    r = client.put(f"/api/v1/contacts/{created['id']}", json={"phone": "222"}, headers=headers)
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["phone"] == "222"

    r = client.get("/api/v1/contacts/", headers=headers)
    assert r.status_code == status.HTTP_200_OK
    assert len(r.json()) >= 1

    r = client.delete(f"/api/v1/contacts/{created['id']}", headers=headers)
    assert r.status_code == status.HTTP_204_NO_CONTENT


def test_update_avatar_forbidden_for_non_admin(client: TestClient):
    headers = auth_header(client)
    # Try to update avatar as regular user; expect 403
    files = {"file": ("avatar.png", b"fake-bytes", "image/png")}
    r = client.patch("/api/v1/users/avatar", headers=headers, files=files)
    assert r.status_code == status.HTTP_403_FORBIDDEN 