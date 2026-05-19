import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, email: str, password: str = "secret123") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def sample_payload(symbol: str = "AAPL") -> dict:
    return {
        "symbol": symbol,
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "target_price": 210.5,
        "personal_score": 9,
        "thesis": "Strong ecosystem and recurring revenue.",
        "is_favorite": True,
    }


# ── list ─────────────────────────────────────────────────────────────────────

def test_list_stocks_initially_empty(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    resp = client.get("/stocks", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


# ── create ───────────────────────────────────────────────────────────────────

def test_create_stock(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    resp = client.post("/stocks", json=sample_payload(), headers=auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["company_name"] == "Apple Inc."
    assert data["personal_score"] == 9
    assert data["is_favorite"] is True


def test_create_duplicate_symbol_returns_409(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    client.post("/stocks", json=sample_payload("AAPL"), headers=auth(token))
    resp = client.post("/stocks", json=sample_payload("aapl"), headers=auth(token))
    assert resp.status_code == 409


def test_create_stock_with_invalid_score_returns_422(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    payload = sample_payload()
    payload["personal_score"] = 11
    resp = client.post("/stocks", json=payload, headers=auth(token))
    assert resp.status_code == 422


def test_create_stock_with_negative_price_returns_422(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    payload = sample_payload()
    payload["target_price"] = -50.0
    resp = client.post("/stocks", json=payload, headers=auth(token))
    assert resp.status_code == 422


# ── get ──────────────────────────────────────────────────────────────────────

def test_get_stock_by_id(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    created = client.post("/stocks", json=sample_payload(), headers=auth(token)).json()
    resp = client.get(f"/stocks/{created['id']}", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


def test_get_missing_stock_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    resp = client.get("/stocks/999", headers=auth(token))
    assert resp.status_code == 404


# ── update ───────────────────────────────────────────────────────────────────

def test_update_stock(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    created = client.post("/stocks", json=sample_payload(), headers=auth(token)).json()
    updated = {**sample_payload(), "symbol": "MSFT", "company_name": "Microsoft Corporation", "is_favorite": False}
    resp = client.put(f"/stocks/{created['id']}", json=updated, headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "MSFT"
    assert resp.json()["is_favorite"] is False


def test_update_missing_stock_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    resp = client.put("/stocks/999", json=sample_payload(), headers=auth(token))
    assert resp.status_code == 404


# ── delete ───────────────────────────────────────────────────────────────────

def test_delete_stock(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    created = client.post("/stocks", json=sample_payload(), headers=auth(token)).json()
    assert client.delete(f"/stocks/{created['id']}", headers=auth(token)).status_code == 204
    assert client.get(f"/stocks/{created['id']}", headers=auth(token)).status_code == 404


def test_delete_missing_stock_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "alice@test.com")
    resp = client.delete("/stocks/999", headers=auth(token))
    assert resp.status_code == 404


# ── user isolation ───────────────────────────────────────────────────────────

def test_user_cannot_see_another_users_stocks(client: TestClient) -> None:
    token_a = register_and_login(client, "alice@test.com")
    token_b = register_and_login(client, "bob@test.com")

    client.post("/stocks", json=sample_payload("AAPL"), headers=auth(token_a))

    resp = client.get("/stocks", headers=auth(token_b))
    assert resp.json() == []


def test_user_cannot_get_another_users_stock(client: TestClient) -> None:
    token_a = register_and_login(client, "alice@test.com")
    token_b = register_and_login(client, "bob@test.com")

    created = client.post("/stocks", json=sample_payload(), headers=auth(token_a)).json()

    resp = client.get(f"/stocks/{created['id']}", headers=auth(token_b))
    assert resp.status_code == 404


def test_user_cannot_delete_another_users_stock(client: TestClient) -> None:
    token_a = register_and_login(client, "alice@test.com")
    token_b = register_and_login(client, "bob@test.com")

    created = client.post("/stocks", json=sample_payload(), headers=auth(token_a)).json()

    resp = client.delete(f"/stocks/{created['id']}", headers=auth(token_b))
    assert resp.status_code == 404


def test_two_users_can_hold_same_symbol(client: TestClient) -> None:
    token_a = register_and_login(client, "alice@test.com")
    token_b = register_and_login(client, "bob@test.com")

    r_a = client.post("/stocks", json=sample_payload("AAPL"), headers=auth(token_a))
    r_b = client.post("/stocks", json=sample_payload("AAPL"), headers=auth(token_b))

    assert r_a.status_code == 201
    assert r_b.status_code == 201


# ── company lookup ───────────────────────────────────────────────────────────

def test_lookup_stock_company(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"Symbol": "TSLA", "Name": "Tesla, Inc.", "Sector": "Consumer Cyclical"}

    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup.requests.get", lambda *a, **kw: FakeResponse())

    token = register_and_login(client, "alice@test.com")
    resp = client.get("/stocks/lookup/tsla", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json() == {"symbol": "TSLA", "company_name": "Tesla, Inc.", "sector": "Consumer Cyclical"}


def test_lookup_without_api_key_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)
    token = register_and_login(client, "alice@test.com")
    resp = client.get("/stocks/lookup/TSLA", headers=auth(token))
    assert resp.status_code == 503
