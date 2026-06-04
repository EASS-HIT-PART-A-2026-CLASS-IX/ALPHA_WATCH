from fastapi.testclient import TestClient

from ai_service.main import app


client = TestClient(app)


def brief_payload(symbol: str = "AAPL") -> dict:
    return {
        "symbol": symbol,
        "quote": {"price": 190.0, "change_percent": 1.2},
        "profile": {"company_name": "Apple Inc.", "sector": "Technology"},
        "news_items": [{"title": "Apple product cycle improves", "source": "Mock"}],
        "thesis": "Strong ecosystem and services revenue.",
    }


def test_stock_brief_known_symbol_returns_structured_mock_brief() -> None:
    resp = client.post("/ai/stock-brief", json=brief_payload("AAPL"))

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["source_mode"] == "mock"
    assert data["sentiment"] in {"bullish", "neutral", "bearish"}
    assert "Apple" in data["summary"]
    assert len(data["takeaways"]) >= 2
    assert len(data["risks"]) >= 2


def test_stock_brief_unknown_symbol_returns_generic_brief() -> None:
    payload = brief_payload("XYZ")
    payload["profile"] = {"company_name": "XYZ Corp.", "sector": "Industrials"}

    resp = client.post("/ai/stock-brief", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "XYZ"
    assert data["sentiment"] == "neutral"
    assert "XYZ Corp." in data["summary"]
    assert data["takeaways"]
    assert data["risks"]


def test_ai_health() -> None:
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
