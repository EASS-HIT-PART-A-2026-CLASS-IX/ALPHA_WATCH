import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import repository


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repository() -> None:
    repository.reset()


def sample_stock_payload() -> dict:
    return {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "target_price": 210.5,
        "personal_score": 9,
        "thesis": "Strong ecosystem and recurring revenue.",
        "is_favorite": True,
    }


def test_list_stocks_initially_empty() -> None:
    response = client.get("/stocks")

    assert response.status_code == 200
    assert response.json() == []


def test_create_stock() -> None:
    response = client.post("/stocks", json=sample_stock_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["symbol"] == "AAPL"
    assert data["company_name"] == "Apple Inc."
    assert data["sector"] == "Technology"
    assert data["target_price"] == 210.5
    assert data["personal_score"] == 9
    assert data["thesis"] == "Strong ecosystem and recurring revenue."
    assert data["is_favorite"] is True


def test_get_stock_by_id() -> None:
    created = client.post("/stocks", json=sample_stock_payload())

    response = client.get(f"/stocks/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"


def test_update_stock() -> None:
    created = client.post("/stocks", json=sample_stock_payload())
    updated_payload = {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "target_price": 455.0,
        "personal_score": 10,
        "thesis": "Cloud growth and diversified business lines.",
        "is_favorite": False,
    }

    response = client.put(f"/stocks/{created.json()['id']}", json=updated_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created.json()["id"]
    assert data["symbol"] == "MSFT"
    assert data["company_name"] == "Microsoft Corporation"
    assert data["is_favorite"] is False


def test_delete_stock() -> None:
    created = client.post("/stocks", json=sample_stock_payload())

    delete_response = client.delete(f"/stocks/{created.json()['id']}")
    get_response = client.get(f"/stocks/{created.json()['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_get_missing_stock_returns_404() -> None:
    response = client.get("/stocks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found"


def test_update_missing_stock_returns_404() -> None:
    response = client.put("/stocks/999", json=sample_stock_payload())

    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found"


def test_delete_missing_stock_returns_404() -> None:
    response = client.delete("/stocks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found"


def test_create_stock_with_invalid_score_returns_422() -> None:
    invalid_payload = sample_stock_payload()
    invalid_payload["personal_score"] = 11

    response = client.post("/stocks", json=invalid_payload)

    assert response.status_code == 422


def test_create_stock_with_negative_target_price_returns_422() -> None:
    invalid_payload = sample_stock_payload()
    invalid_payload["target_price"] = -50.0

    response = client.post("/stocks", json=invalid_payload)

    assert response.status_code == 422


def test_lookup_stock_company(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "Symbol": "TSLA",
                "Name": "Tesla, Inc.",
                "Sector": "Consumer Cyclical",
            }

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setenv("ALPHAVANTAGE_API_KEY", "test-key")
    monkeypatch.setattr("app.company_lookup.requests.get", fake_get)

    response = client.get("/stocks/lookup/tsla")

    assert response.status_code == 200
    assert response.json() == {
        "symbol": "TSLA",
        "company_name": "Tesla, Inc.",
        "sector": "Consumer Cyclical",
    }


def test_lookup_stock_company_without_api_key_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    response = client.get("/stocks/lookup/TSLA")

    assert response.status_code == 503
    assert response.json()["detail"] == "ALPHAVANTAGE_API_KEY is not configured"
