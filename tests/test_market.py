"""
Tests for the /market/* endpoints.
All external Alpha Vantage calls are mocked — no live network needed.
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


# ── /market/profile ───────────────────────────────────────────────────────────

def test_profile_returns_data(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
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
    assert "Apple" in data["description"]
    assert data["market_cap"] == 2_800_000_000_000


def test_profile_normalises_symbol_to_uppercase(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup._av_get", lambda params: FAKE_OVERVIEW)

    token = register_and_login(client)
    resp = client.get("/market/profile/aapl", headers=auth(token))
    assert resp.json()["symbol"] == "AAPL"


def test_profile_unknown_symbol_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup._av_get", lambda params: {})

    token = register_and_login(client)
    resp = client.get("/market/profile/FAKE", headers=auth(token))
    assert resp.status_code == 404


def test_profile_missing_api_key_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/profile/AAPL", headers=auth(token))
    assert resp.status_code == 503


def test_profile_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/profile/AAPL")
    assert resp.status_code == 401


# ── /market/quote ─────────────────────────────────────────────────────────────

def test_quote_returns_data(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_GLOBAL_QUOTE)

    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] == pytest.approx(189.50)
    assert data["change"] == pytest.approx(2.50)
    assert data["change_percent"] == pytest.approx(1.3369)
    assert data["previous_close"] == pytest.approx(187.00)


def test_quote_unknown_symbol_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: {"Global Quote": {}})

    token = register_and_login(client)
    resp = client.get("/market/quote/FAKE", headers=auth(token))
    assert resp.status_code == 404


def test_quote_missing_api_key_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))
    assert resp.status_code == 503


def test_quote_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/quote/AAPL")
    assert resp.status_code == 401


# ── /market/history ───────────────────────────────────────────────────────────

def test_history_returns_series(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_TIME_SERIES)

    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert isinstance(data["series"], list)
    assert len(data["series"]) == 3
    # series must be ascending (oldest first) for charting
    assert data["series"][0]["date"] < data["series"][-1]["date"]
    assert data["series"][0]["close"] == pytest.approx(182.00)


def test_history_unknown_symbol_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: {})

    token = register_and_login(client)
    resp = client.get("/market/history/FAKE", headers=auth(token))
    assert resp.status_code == 404


def test_history_missing_api_key_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))
    assert resp.status_code == 503


def test_history_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/history/AAPL")
    assert resp.status_code == 401


# ── /market/news ──────────────────────────────────────────────────────────────

def test_news_returns_items(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: FAKE_NEWS)

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["title"] == "Apple hits record high"
    assert item["source"] == "Reuters"
    assert item["published_at"] == "2024-01-03 12:00"
    assert item["url"] == "https://example.com/apple-record"
    assert "surged" in item["summary"]


def test_news_empty_feed_returns_empty_list(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.market_routes._av_get", lambda params: {"feed": []})

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_news_missing_api_key_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))
    assert resp.status_code == 503


def test_news_requires_auth(client: TestClient) -> None:
    resp = client.get("/market/news/AAPL")
    assert resp.status_code == 401
