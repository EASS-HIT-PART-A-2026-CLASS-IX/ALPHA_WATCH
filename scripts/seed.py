from sqlmodel import Session, select

from app.auth import hash_password
from app.database import engine, init_db
from app.models import Stock, User

DEMO_EMAIL = "demo@alphawatch.local"
DEMO_PASSWORD = "password123"

DEMO_STOCKS = [
    {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "target_price": 225.0,
        "personal_score": 9,
        "thesis": "Strong ecosystem, services revenue, and capital return.",
        "is_favorite": True,
    },
    {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "target_price": 475.0,
        "personal_score": 8,
        "thesis": "Cloud, productivity software, and AI platform depth.",
        "is_favorite": True,
    },
    {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "sector": "Technology",
        "target_price": 150.0,
        "personal_score": 8,
        "thesis": "AI accelerator demand remains the key growth driver.",
        "is_favorite": False,
    },
]


def seed() -> None:
    init_db()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == DEMO_EMAIL)).first()
        if user is None:
            user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
            session.add(user)
            session.commit()
            session.refresh(user)

        existing_symbols = set(
            session.exec(select(Stock.symbol).where(Stock.user_id == user.id)).all()
        )
        for item in DEMO_STOCKS:
            if item["symbol"] not in existing_symbols:
                session.add(Stock(**item, user_id=user.id))
        session.commit()

    print("AlphaWatch database is initialized.")
    print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
