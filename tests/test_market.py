"""
Tests for the /market/* endpoints.
All external Alpha Vantage calls are mocked — no live network needed.
Covers both the live-data path and the mock-fallback path.
"""
import pytest
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, email: str = "alice@test.com") -> str:
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    resp = client.post("/auth/login", data={"username": email, "password": "secret123"})
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── shared fake Alpha Vantage responses ───────────────────────────────────────

FAKE_OVERVIEW = {
    "Symbol": "AAPL",
    "Name": "Apple Inc.",
    "Sector": "Technology",
    "Industry": "Consumer Electronics",
    "Description": "Apple designs and sells consumer electronics.",
    "MarketCapitalization": "2800000000000",
}

FAKE_GLOBAL_QUOTE = {
    "Global Quote": {
        "01. symbol": "AAPL",
        "05. price": "189.50",
        "08. previous close": "187.00",
        "09. change": "2.50",
        "10. change percent": "1.3369%",
    }
}

FAKE_TIME_SERIES = {
    "Time Series (Daily)": {
        "2024-01-03": {"4. close": "185.00"},
        "2024-01-02": {"4. close": "183.00"},
        "2024-01-01": {"4. close": "182.00"},
    }
}

FAKE_NEWS = {
    "feed": [
        {
            "title": "Apple hits record high",
            "source": "Reuters",
            "time_published": "20240103T120000",
            "url": "https://example.com/apple-record",
            "summary": "Apple stock surged today.",
        }
    ]
}


# ── /market/profile — live path ───────────────────────────────────────────────

def test_profile_returns_live_data(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup._av_get", lambda params: FAKE_OVERVIEW)

    token = register_and_login(client)
    resp = client.get("/market/profile/aapl", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["company_name"] == "Apple Inc."
    assert data["sector"] == "Technology"
    assert data["industry"] == "Consumer Electronics"
    assert data["source_mode"] == "live"


def test_profile_normalises_symbol_to_uppercase(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup._av_get", lambda params: FAKE_OVERVIEW)

    token = register_and_login(client)
    resp = client.get("/market/profile/aapl", headers=auth(token))
    assert resp.json()["symbol"] == "AAPL"


# ── /market/profile — fallback path ──────────────────────────────────────────

def test_profile_falls_back_to_mock_when_key_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/profile/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["source_mode"] == "mock"
    assert data["company_name"]   # not empty
    assert data["description"]


def test_profile_falls_back_to_mock_on_api_failure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup._av_get", lambda params: {})  # empty = not found

    token = register_and_login(client)
    resp = client.get("/market/profile/TSLA", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["source_mode"] == "mock"


def test_profile_mock_for_unknown_symbol(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/profile/XYZ", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "XYZ"
    assert data["source_mode"] == "mock"


def test_profile_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/profile/AAPL")
    assert resp.status_code == 401


# ── /market/quote — live path ─────────────────────────────────────────────────

def test_quote_returns_live_data(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_GLOBAL_QUOTE)

    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["price"] == pytest.approx(189.50)
    assert data["source_mode"] == "live"


# ── /market/quote — fallback path ─────────────────────────────────────────────

def test_quote_falls_back_to_mock_when_key_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] > 0
    assert data["source_mode"] == "mock"


def test_quote_mock_for_unknown_symbol(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/quote/XYZ", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "XYZ"
    assert data["price"] > 0
    assert data["source_mode"] == "mock"


def test_quote_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/quote/AAPL")
    assert resp.status_code == 401


# ── /market/history — live path ───────────────────────────────────────────────

def test_history_returns_live_series(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_TIME_SERIES)

    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["source_mode"] == "live"
    assert len(data["series"]) == 3
    assert data["series"][0]["date"] < data["series"][-1]["date"]


# ── /market/history — fallback path ──────────────────────────────────────────

def test_history_falls_back_to_mock_when_key_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["source_mode"] == "mock"
    assert len(data["series"]) == 30
    # must be ascending for charting
    assert data["series"][0]["date"] < data["series"][-1]["date"]
    assert all(p["close"] > 0 for p in data["series"])


def test_history_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/history/AAPL")
    assert resp.status_code == 401


# ── /market/news — live path ──────────────────────────────────────────────────

def test_news_returns_live_items(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_NEWS)

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["source_mode"] == "live"
    assert data["items"][0]["title"] == "Apple hits record high"


def test_news_empty_live_feed_returns_empty_list(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: {"feed": []})

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["source_mode"] == "live"


# ── /market/news — fallback path ──────────────────────────────────────────────

def test_news_falls_back_to_mock_when_key_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["source_mode"] == "mock"
    assert len(data["items"]) > 0
    assert data["items"][0]["title"]
    assert data["items"][0]["source"]


def test_news_mock_contains_symbol_in_titles(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/news/NVDA", headers=auth(token))

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("NVDA" in item["title"] for item in items)


def test_news_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/news/AAPL")
    assert resp.status_code == 401
