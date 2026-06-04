from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field


Sentiment = Literal["bullish", "neutral", "bearish"]
SourceMode = Literal["live", "mock"]


class StockBriefRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    quote: dict = Field(default_factory=dict)
    profile: dict = Field(default_factory=dict)
    news_items: list[dict] = Field(default_factory=list)
    thesis: str | None = None


class StockBriefResponse(BaseModel):
    symbol: str
    summary: str
    sentiment: Sentiment
    takeaways: list[str]
    risks: list[str]
    source_mode: SourceMode = "mock"


app = FastAPI(title="AlphaWatch AI Service")


KNOWN_BRIEFS: dict[str, dict] = {
    "AAPL": {
        "sentiment": "bullish",
        "focus": "Apple combines a durable hardware ecosystem with high-margin services revenue.",
        "takeaways": [
            "Services and installed-base loyalty support recurring cash flow.",
            "Balance sheet strength gives Apple room for buybacks and product investment.",
            "The stock often trades on iPhone cycle expectations and margin commentary.",
        ],
        "risks": [
            "iPhone demand weakness can pressure near-term sentiment.",
            "Regulatory pressure on App Store economics remains a watch item.",
        ],
    },
    "MSFT": {
        "sentiment": "bullish",
        "focus": "Microsoft has a balanced mix of cloud, productivity software, and AI platform exposure.",
        "takeaways": [
            "Azure growth remains the key operating signal.",
            "Office and enterprise subscriptions provide resilient baseline revenue.",
            "AI features can lift pricing power across the software stack.",
        ],
        "risks": [
            "Cloud growth deceleration would weigh on valuation.",
            "Large AI infrastructure spending may pressure margins.",
        ],
    },
    "NVDA": {
        "sentiment": "bullish",
        "focus": "NVIDIA remains highly levered to AI infrastructure demand and accelerator supply.",
        "takeaways": [
            "Data center revenue is the primary driver to monitor.",
            "Strong ecosystem lock-in supports premium margins.",
            "Demand visibility depends on hyperscaler and enterprise AI spending.",
        ],
        "risks": [
            "Expectations are high, so any slowdown can hit the multiple quickly.",
            "Customer concentration and export limits can create volatility.",
        ],
    },
    "TSLA": {
        "sentiment": "neutral",
        "focus": "Tesla offers growth optionality, but execution and margin volatility keep the setup balanced.",
        "takeaways": [
            "Delivery trends and automotive gross margin are the first signals to watch.",
            "Energy storage and software optionality can support the long-term story.",
            "The stock is sensitive to price cuts and production commentary.",
        ],
        "risks": [
            "EV competition can pressure pricing and margins.",
            "Valuation depends heavily on future growth assumptions.",
        ],
    },
    "AMZN": {
        "sentiment": "bullish",
        "focus": "Amazon combines retail scale, advertising growth, and AWS cloud profitability.",
        "takeaways": [
            "AWS growth and margin are the most important profit drivers.",
            "Advertising continues to add higher-margin revenue.",
            "Retail efficiency improvements can compound operating leverage.",
        ],
        "risks": [
            "Consumer weakness can slow retail demand.",
            "Cloud competition may pressure AWS growth or pricing.",
        ],
    },
    "META": {
        "sentiment": "bullish",
        "focus": "Meta benefits from massive social distribution, improving ad tools, and AI-driven engagement.",
        "takeaways": [
            "Ad revenue and Reels monetization remain core performance drivers.",
            "AI ranking and ad automation can improve engagement and advertiser ROI.",
            "Cost discipline is important while Reality Labs remains a drag.",
        ],
        "risks": [
            "Privacy and regulatory changes can affect ad targeting.",
            "Metaverse investment losses may weigh on investor confidence.",
        ],
    },
    "GOOGL": {
        "sentiment": "bullish",
        "focus": "Alphabet has strong search economics, YouTube scale, cloud growth, and deep AI assets.",
        "takeaways": [
            "Search advertising remains the cash engine.",
            "Cloud profitability and AI product execution are key swing factors.",
            "YouTube provides a major video and creator ecosystem advantage.",
        ],
        "risks": [
            "AI search disruption could pressure the core business model.",
            "Antitrust scrutiny remains a persistent overhang.",
        ],
    },
    "AMD": {
        "sentiment": "neutral",
        "focus": "AMD has meaningful AI and server CPU opportunities, balanced by intense competition.",
        "takeaways": [
            "Data center GPU traction is the biggest upside catalyst.",
            "Server CPU share gains can support revenue durability.",
            "Execution versus NVIDIA and Intel is central to the thesis.",
        ],
        "risks": [
            "AI accelerator expectations may outrun near-term supply and demand.",
            "Competitive pricing can pressure margins.",
        ],
    },
    "PLTR": {
        "sentiment": "neutral",
        "focus": "Palantir offers strong AI software momentum but carries valuation sensitivity.",
        "takeaways": [
            "Commercial customer growth is the key expansion signal.",
            "Government contracts provide durable but sometimes uneven revenue.",
            "AI platform adoption can improve the long-term growth profile.",
        ],
        "risks": [
            "High valuation increases sensitivity to growth misses.",
            "Large contract timing can make quarterly results lumpy.",
        ],
    },
}


def _to_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def build_mock_brief(payload: StockBriefRequest) -> StockBriefResponse:
    symbol = payload.symbol.strip().upper()
    known = KNOWN_BRIEFS.get(symbol)
    quote = payload.quote or {}
    profile = payload.profile or {}
    news_count = len(payload.news_items or [])
    price = _to_float(quote.get("price"))
    change_pct = _to_float(quote.get("change_percent"))
    sector = profile.get("sector") or "its sector"
    company = profile.get("company_name") or f"{symbol}"

    if known:
        sentiment: Sentiment = known["sentiment"]
        summary = (
            f"{company} is trading around ${price:.2f} with a {change_pct:+.2f}% latest move. "
            f"{known['focus']} Recent context includes {news_count} headline(s) and the user's thesis: "
            f"{payload.thesis or 'not provided'}"
        )
        takeaways = known["takeaways"]
        risks = known["risks"]
    else:
        sentiment = "neutral"
        direction = "positive" if change_pct > 1 else "negative" if change_pct < -1 else "mixed"
        summary = (
            f"{company} is a {sector} watchlist name trading around ${price:.2f}. "
            f"The latest price action looks {direction} at {change_pct:+.2f}%, so the setup is best treated as a "
            "research candidate until stronger company-specific data is available."
        )
        takeaways = [
            "Compare the latest price against the user's target price before acting.",
            "Check whether recent headlines support or weaken the original thesis.",
            "Use the chart timeframe selector to separate intraday noise from longer-term trend.",
        ]
        risks = [
            "Unknown or thinly covered symbols can have less reliable market context.",
            "Mock fallback data should be treated as demo support, not investment advice.",
        ]

    return StockBriefResponse(
        symbol=symbol,
        summary=summary,
        sentiment=sentiment,
        takeaways=takeaways[:4],
        risks=risks[:4],
        source_mode="mock",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ai/stock-brief", response_model=StockBriefResponse)
def stock_brief(payload: StockBriefRequest) -> StockBriefResponse:
    return build_mock_brief(payload)
