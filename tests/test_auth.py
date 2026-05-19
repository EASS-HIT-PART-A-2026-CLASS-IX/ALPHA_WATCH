from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth import create_access_token, hash_password
from app.models import User


# ── helpers ──────────────────────────────────────────────────────────────────

def register(client: TestClient, email: str, password: str = "secret123") -> dict:
    return client.post("/auth/register", json={"email": email, "password": password}).json()


def login(client: TestClient, email: str, password: str = "secret123") -> str:
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── registration ──────────────────────────────────────────────────────────────

def test_register_creates_user(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "alice@test.com", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@test.com"
    assert data["role"] == "user"
    assert "id" in data


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "alice@test.com", "password": "secret123"})
    resp = client.post("/auth/register", json={"email": "alice@test.com", "password": "other123"})
    assert resp.status_code == 409


def test_register_short_password_returns_422(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "alice@test.com", "password": "abc"})
    assert resp.status_code == 422


# ── login ────────────────────────────────────────────────────────────────────

def test_login_returns_token(client: TestClient) -> None:
    register(client, "alice@test.com")
    resp = client.post("/auth/login", data={"username": "alice@test.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    register(client, "alice@test.com")
    resp = client.post("/auth/login", data={"username": "alice@test.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    resp = client.post("/auth/login", data={"username": "nobody@test.com", "password": "secret123"})
    assert resp.status_code == 401


# ── protected routes ─────────────────────────────────────────────────────────

def test_protected_route_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/stocks")
    assert resp.status_code == 401


def test_protected_route_with_valid_token_succeeds(client: TestClient) -> None:
    register(client, "alice@test.com")
    token = login(client, "alice@test.com")
    resp = client.get("/stocks", headers=auth(token))
    assert resp.status_code == 200


def test_expired_token_returns_401(client: TestClient) -> None:
    token = create_access_token("ghost@test.com", "user", expires_delta=timedelta(minutes=-1))
    resp = client.get("/stocks", headers=auth(token))
    assert resp.status_code == 401


def test_malformed_token_returns_401(client: TestClient) -> None:
    resp = client.get("/stocks", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


# ── role check ────────────────────────────────────────────────────────────────

def test_admin_route_as_regular_user_returns_403(client: TestClient) -> None:
    register(client, "alice@test.com")
    token = login(client, "alice@test.com")
    resp = client.get("/auth/admin/users", headers=auth(token))
    assert resp.status_code == 403


def test_admin_route_as_admin_succeeds(client: TestClient, session: Session) -> None:
    admin = User(email="admin@test.com", hashed_password=hash_password("admin123"), role="admin")
    session.add(admin)
    session.commit()

    resp = client.post("/auth/login", data={"username": "admin@test.com", "password": "admin123"})
    token = resp.json()["access_token"]

    resp = client.get("/auth/admin/users", headers=auth(token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "admin@test.com" in emails


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_me_returns_current_user(client: TestClient) -> None:
    register(client, "alice@test.com")
    token = login(client, "alice@test.com")
    resp = client.get("/auth/me", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@test.com"
