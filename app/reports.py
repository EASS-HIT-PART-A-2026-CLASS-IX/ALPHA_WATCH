import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, col, select

from app.auth import get_current_user
from app.database import get_session
from app.models import MarketSnapshot, Stock, User

router = APIRouter(prefix="/reports", tags=["reports"])


def _latest_snapshot(session: Session, symbol: str) -> MarketSnapshot | None:
    return session.exec(
        select(MarketSnapshot)
        .where(MarketSnapshot.symbol == symbol)
        .order_by(col(MarketSnapshot.refreshed_at).desc())
    ).first()


def build_weekly_stock_report(user: User, stocks: list[Stock], session: Session) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# AlphaWatch Weekly Stock Summary",
        "",
        f"Generated: {generated_at}",
        f"Account: {user.email}",
        "",
    ]

    if not stocks:
        lines.extend([
            "No saved stocks yet.",
            "",
            "Add stocks to your watchlist to generate a useful weekly summary.",
        ])
        return "\n".join(lines)

    favorites = sum(1 for stock in stocks if stock.is_favorite)
    average_score = sum(stock.personal_score for stock in stocks) / len(stocks)
    lines.extend([
        "## Watchlist Overview",
        "",
        f"- Saved stocks: {len(stocks)}",
        f"- Favorites: {favorites}",
        f"- Average personal score: {average_score:.1f}/10",
        "",
        "## Stocks",
        "",
    ])

    for stock in stocks:
        snapshot = _latest_snapshot(session, stock.symbol)
        quote = {}
        profile = {}
        if snapshot and snapshot.quote_json:
            quote = json.loads(snapshot.quote_json)
        if snapshot and snapshot.profile_json:
            profile = json.loads(snapshot.profile_json)

        price = quote.get("price")
        change_percent = quote.get("change_percent")
        source_mode = quote.get("source_mode") or (snapshot.quote_source_mode if snapshot else "not refreshed")
        refreshed_at = snapshot.refreshed_at.strftime("%Y-%m-%d %H:%M UTC") if snapshot else "not refreshed yet"
        industry = profile.get("industry") or "Unknown"
        favorite_marker = " yes" if stock.is_favorite else " no"

        lines.extend([
            f"### {stock.symbol} - {stock.company_name}",
            "",
            f"- Sector: {stock.sector}",
            f"- Industry: {industry}",
            f"- Favorite:{favorite_marker}",
            f"- Personal score: {stock.personal_score}/10",
            f"- Target price: ${stock.target_price:.2f}",
            f"- Last refreshed: {refreshed_at}",
            f"- Data source: {source_mode}",
        ])
        if price is not None:
            lines.append(f"- Latest price: ${float(price):.2f}")
        if change_percent is not None:
            lines.append(f"- Daily move: {float(change_percent):+.2f}%")
        lines.extend([
            f"- Thesis: {stock.thesis}",
            "",
        ])

    lines.extend([
        "## EX3 Enhancement",
        "",
        "This markdown report is the documented AlphaWatch EX3 enhancement. It combines the user's saved watchlist with the latest background refresh snapshot so a weekly review can be saved, shared, or submitted locally.",
    ])
    return "\n".join(lines)


@router.get("/weekly", response_class=PlainTextResponse)
def weekly_report(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> str:
    stocks = session.exec(
        select(Stock)
        .where(Stock.user_id == current_user.id)
        .order_by(col(Stock.symbol))
    ).all()
    return build_weekly_stock_report(current_user, stocks, session)
