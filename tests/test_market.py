"""
Tests for /market/* endpoints — yfinance is the provider.
yfinance calls are mocked via monkeypatching the Ticker class.
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


# ── fake yfinance Ticker ──────────────────────────────────────────────────────

FAKE_INFO = {
    "longName": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "website": "https://www.apple.com",
    "country": "United States",
    "longBusinessSummary": "Apple designs and sells consumer electronics worldwide.",
    "marketCap": 2_950_000_000_000,
    "currentPrice": 189.50,
    "previousClose": 187.00,
    "open": 188.00,
    "dayHigh": 191.50,
    "dayLow": 187.20,
    "volume": 52_000_000,
}


class FakeFastInfo(dict):
    """Mimics yfinance's fast_info object."""
    def __init__(self, empty=False):
        if empty:
            super().__init__({})
        else:
            super().__init__({
                "last_price": 189.50,
                "previous_close": 187.00,
                "open": 188.00,
                "day_high": 191.50,
                "day_low": 187.20,
                "last_volume": 52_000_000,
            })


class FakeHistory:
    """Mimics a pandas DataFrame returned by yfinance .history()."""
    def __init__(self, rows):
        self._rows = rows  # list of (date_str, close_price)
        self.empty = len(rows) == 0

    def iterrows(self):
        import datetime as dt
        for date_str, close in self._rows:
            d = dt.date.fromisoformat(date_str)
            yield d, {"Close": close}


class FakeTicker:
    """Mimics yfinance.Ticker."""
    def __init__(self, symbol, info=None, history_rows=None, news=None, raise_on=None, fast_empty=False):
        self.symbol = symbol
        self._info = info if info is not None else FAKE_INFO
        self._history_rows = history_rows if history_rows is not None else [
            ("2024-01-01", 182.00),
            ("2024-01-02", 183.00),
            ("2024-01-03", 185.00),
        ]
        self._news = news if news is not None else [
            {
                "title": "Apple hits record high",
                "publisher": "Reuters",
                "link": "https://example.com/apple-record",
                "providerPublishTime": 1704240000,
                "content": {"summary": "Apple stock surged today."},
            }
        ]
        self._raise_on = raise_on or set()
        self._fast_empty = fast_empty

    @property
    def info(self):
        if "info" in self._raise_on:
            raise RuntimeError("simulated yfinance error")
        return self._info

    @property
    def fast_info(self):
        if "fast_info" in self._raise_on:
            raise RuntimeError("simulated yfinance error")
        return FakeFastInfo(empty=self._fast_empty)

    def history(self, period="1mo", auto_adjust=False):
        if "history" in self._raise_on:
            raise RuntimeError("simulated yfinance error")
        return FakeHistory(self._history_rows)

    @property
    def news(self):
        if "news" in self._raise_on:
            raise RuntimeError("simulated yfinance error")
        return self._news


def _patch_yf(monkeypatch, **kwargs):
    """Patch yfinance.Ticker to return a FakeTicker."""
    def factory(sym):
        return FakeTicker(sym, **kwargs)
    # Patch both modules that use yfinance
    monkeypatch.setattr("app.market_routes._yf_ticker", factory)


# ── /market/profile ───────────────────────────────────────────────────────────

def test_profile_live_returns_correct_shape(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch)
    token = register_and_login(client)
    resp = client.get("/market/profile/aapl", headers=auth(token))

    assert resp.status_code == 200
    d = resp.json()
    assert d["symbol"] == "AAPL"
    assert d["company_name"] == "Apple Inc."
    assert d["sector"] == "Technology"
    assert d["industry"] == "Consumer Electronics"
    assert d["source_mode"] == "live"
    assert "website" in d
    assert "country" in d
    assert d["market_cap"] == 2_950_000_000_000


def test_profile_normalises_to_uppercase(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch)
    token = register_and_login(client)
    resp = client.get("/market/profile/aapl", headers=auth(token))
    assert resp.json()["symbol"] == "AAPL"


def test_profile_fallback_when_yf_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, raise_on={"info"})
    token = register_and_login(client)
    resp = client.get("/market/profile/AAPL", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "mock"
    assert d["company_name"]
    assert d["description"]


def test_profile_fallback_on_empty_info(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, info={})
    token = register_and_login(client)
    resp = client.get("/market/profile/FAKE", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["source_mode"] == "mock"


def test_profile_mock_for_unknown_symbol(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, info={})
    token = register_and_login(client)
    resp = client.get("/market/profile/XYZ", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["symbol"] == "XYZ"
    assert d["source_mode"] == "mock"


def test_profile_requires_auth(client: TestClient) -> None:
    assert client.get("/market/profile/AAPL").status_code == 401


# ── /market/quote ─────────────────────────────────────────────────────────────

def test_quote_live_returns_full_shape(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch)
    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))

    assert resp.status_code == 200
    d = resp.json()
    assert d["symbol"] == "AAPL"
    assert d["price"] == pytest.approx(189.50)
    assert d["previous_close"] == pytest.approx(187.00)
    assert d["open"] == pytest.approx(188.00)
    assert d["day_high"] == pytest.approx(191.50)
    assert d["day_low"] == pytest.approx(187.20)
    assert d["volume"] == 52_000_000
    assert d["source_mode"] == "live"


def test_quote_fallback_when_yf_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, raise_on={"fast_info"})
    token = register_and_login(client)
    resp = client.get("/market/quote/AAPL", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["price"] > 0
    assert d["source_mode"] == "mock"


def test_quote_mock_for_unknown_symbol(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, fast_empty=True)
    token = register_and_login(client)
    resp = client.get("/market/quote/XYZ", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["source_mode"] == "mock"
    assert resp.json()["price"] > 0


def test_quote_requires_auth(client: TestClient) -> None:
    assert client.get("/market/quote/AAPL").status_code == 401


# ── /market/history ───────────────────────────────────────────────────────────

def test_history_live_returns_ascending_series(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch)
    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))

    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "live"
    assert d["interval"] == "1day"
    assert len(d["series"]) == 3
    assert d["series"][0]["timestamp"] == "2024-01-01"
    assert d["series"][0]["close"] == pytest.approx(182.00)


def test_history_fallback_returns_30_points(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, raise_on={"history"})
    token = register_and_login(client)
    resp = client.get("/market/history/AAPL", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "mock"
    assert len(d["series"]) == 30
    assert all(p["close"] > 0 for p in d["series"])


def test_history_fallback_on_empty_history(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, history_rows=[])
    token = register_and_login(client)
    resp = client.get("/market/history/FAKE", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["source_mode"] == "mock"


def test_history_requires_auth(client: TestClient) -> None:
    assert client.get("/market/history/AAPL").status_code == 401


# ── /market/news ──────────────────────────────────────────────────────────────

def test_news_live_returns_items(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch)
    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))

    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "live"
    assert len(d["items"]) >= 1
    assert d["items"][0]["title"] == "Apple hits record high"


def test_news_fallback_when_yf_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, raise_on={"news"})
    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "mock"
    assert len(d["items"]) > 0


def test_news_fallback_on_empty_feed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, news=[])
    token = register_and_login(client)
    resp = client.get("/market/news/AAPL", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["source_mode"] == "mock"


def test_news_mock_symbol_in_titles(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, news=[])
    token = register_and_login(client)
    resp = client.get("/market/news/NVDA", headers=auth(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("NVDA" in item["title"] for item in items)


def test_news_mock_for_iren(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_yf(monkeypatch, news=[])
    token = register_and_login(client)
    resp = client.get("/market/news/IREN", headers=auth(token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["source_mode"] == "mock"
    assert any("IREN" in item["title"] for item in d["items"])


def test_news_requires_auth(client: TestClient) -> None:
    assert client.get("/market/news/AAPL").status_code == 401
