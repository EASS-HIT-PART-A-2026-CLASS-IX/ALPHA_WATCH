import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import MarketSnapshot, Stock, User


def register_and_login(client: TestClient, email: str = "report@test.com") -> str:
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    resp = client.post("/auth/login", data={"username": email, "password": "secret123"})
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_weekly_report_includes_watchlist_and_latest_snapshot(
    client: TestClient,
    session: Session,
) -> None:
    token = register_and_login(client)
    user = session.exec(select(User).where(User.email == "report@test.com")).one()
    stock = Stock(
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        target_price=225.0,
        personal_score=9,
        thesis="High quality business with durable demand.",
        is_favorite=True,
        user_id=user.id,
    )
    session.add(stock)
    session.add(
        MarketSnapshot(
            symbol="AAPL",
            quote_source_mode="mock",
            profile_source_mode="mock",
            history_source_mode="mock",
            news_source_mode="mock",
            quote_json=json.dumps({"price": 190.0, "change_percent": 1.25, "source_mode": "mock"}),
            profile_json=json.dumps({"industry": "Consumer Electronics"}),
        )
    )
    session.commit()

    resp = client.get("/reports/weekly", headers=auth(token))

    assert resp.status_code == 200
    report = resp.text
    assert "# AlphaWatch Weekly Stock Summary" in report
    assert "AAPL - Apple Inc." in report
    assert "Latest price: $190.00" in report
    assert "EX3 Enhancement" in report
