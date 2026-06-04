"""
mock_data.py — Realistic fallback market data for demo/offline use.

Used by market_routes.py when:
  - ALPHAVANTAGE_API_KEY is not set, or
  - the external API call fails for any reason.

Each function accepts a symbol string and returns a plain dict
in the same shape as the real API response schemas.
"""
import random
from datetime import date, datetime, time, timedelta

# ── Per-symbol profiles ───────────────────────────────────────────────────────

_PROFILES: dict[str, dict] = {
    "AAPL": {
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "description": (
            "Apple Inc. designs, manufactures, and markets smartphones, personal computers, "
            "tablets, wearables, and accessories worldwide. Its flagship products include the "
            "iPhone, Mac, iPad, Apple Watch, and AirPods, supported by a growing services "
            "segment including the App Store, Apple Music, iCloud, and Apple TV+."
        ),
        "market_cap": 2_950_000_000_000,
        "base_price": 189.50,
    },
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software—Infrastructure",
        "description": (
            "Microsoft Corporation develops and supports software, services, devices, and "
            "solutions worldwide. Its segments include Productivity and Business Processes, "
            "Intelligent Cloud, and More Personal Computing. Key products include Windows, "
            "Office 365, Azure, LinkedIn, and Xbox."
        ),
        "market_cap": 3_100_000_000_000,
        "base_price": 415.20,
    },
    "NVDA": {
        "company_name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "description": (
            "NVIDIA Corporation provides graphics, computing and networking solutions. "
            "Its platforms are used in gaming, professional visualization, data centers, "
            "and automotive markets. NVIDIA's GPUs power the majority of AI model training "
            "workloads globally."
        ),
        "market_cap": 2_200_000_000_000,
        "base_price": 875.00,
    },
    "TSLA": {
        "company_name": "Tesla, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers",
        "description": (
            "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, "
            "energy generation and storage systems, and related services. Its vehicle lineup "
            "includes the Model S, Model 3, Model X, Model Y, and Cybertruck."
        ),
        "market_cap": 780_000_000_000,
        "base_price": 245.00,
    },
    "AMZN": {
        "company_name": "Amazon.com, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail",
        "description": (
            "Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions "
            "through online and physical stores, and through its Amazon Web Services (AWS) cloud "
            "computing platform. AWS is the world's largest cloud infrastructure provider."
        ),
        "market_cap": 1_950_000_000_000,
        "base_price": 185.30,
    },
    "META": {
        "company_name": "Meta Platforms, Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "description": (
            "Meta Platforms, Inc. engages in the development of products that enable people to "
            "connect and share through mobile devices, personal computers, and other surfaces. "
            "It operates Facebook, Instagram, WhatsApp, and Messenger, and is investing heavily "
            "in the metaverse through its Reality Labs division."
        ),
        "market_cap": 1_250_000_000_000,
        "base_price": 490.00,
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "description": (
            "Alphabet Inc. provides online advertising services, cloud computing, software, "
            "and hardware. Its Google segment includes Search, YouTube, Android, Chrome, "
            "Google Cloud, and hardware products. DeepMind and Waymo are among its Other Bets."
        ),
        "market_cap": 2_100_000_000_000,
        "base_price": 170.00,
    },
}

_GENERIC_PROFILE = {
    "company_name": "{symbol} Corp.",
    "sector": "Technology",
    "industry": "Diversified Technology",
    "description": (
        "This company operates across multiple technology verticals including software, "
        "hardware, and digital services. It serves enterprise and consumer markets globally."
    ),
    "market_cap": 50_000_000_000,
    "base_price": 100.00,
}

_NEWS_TEMPLATES = [
    ("{sym} Beats Quarterly Earnings Expectations", "Reuters"),
    ("{sym} Announces New Product Line for Next Year", "Bloomberg"),
    ("Analysts Raise Price Target for {sym} After Strong Results", "CNBC"),
    ("{sym} Expands Into New International Markets", "Financial Times"),
    ("Institutional Investors Increase Stakes in {sym}", "MarketWatch"),
    ("{sym} CEO Outlines Five-Year Strategic Vision", "Wall Street Journal"),
    ("{sym} Reports Record Revenue in Latest Quarter", "Forbes"),
    ("Short Interest in {sym} Drops to Six-Month Low", "Barron's"),
]


# ── Public helpers ────────────────────────────────────────────────────────────

def _profile_for(symbol: str) -> dict:
    """Return the known profile dict or a filled-in generic one."""
    if symbol in _PROFILES:
        return _PROFILES[symbol]
    generic = _GENERIC_PROFILE.copy()
    generic["company_name"] = f"{symbol} Corp."
    return generic


def mock_profile(symbol: str) -> dict:
    p = _profile_for(symbol)
    return {
        "symbol": symbol,
        "company_name": p["company_name"],
        "sector": p["sector"],
        "industry": p["industry"],
        "description": p["description"],
        "market_cap": p["market_cap"],
        "source_mode": "mock",
    }


def mock_quote(symbol: str) -> dict:
    """
    Generate a deterministic-looking quote based on the symbol.
    Uses a seeded random so the same symbol always gives the same base numbers,
    but adds a tiny time-based jitter so it looks 'live' on repeated calls.
    """
    p = _profile_for(symbol)
    base = p["base_price"]

    # Seeded per symbol for stable base, plus small daily drift
    seed = sum(ord(c) for c in symbol) + date.today().toordinal()
    rng = random.Random(seed)
    change = round(rng.uniform(-base * 0.03, base * 0.03), 2)
    price = round(base + change, 2)
    previous_close = round(base, 2)
    change_percent = round((change / previous_close) * 100, 4)

    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "change_percent": change_percent,
        "previous_close": previous_close,
        "source_mode": "mock",
    }


def mock_history(symbol: str, history_range: str = "1mo") -> dict:
    """
    Generate plausible close prices for the selected chart range using a
    deterministic random walk seeded by symbol and range.
    """
    p = _profile_for(symbol)
    base = p["base_price"]

    rng = random.Random(sum(ord(c) for c in f"{symbol}:{history_range}"))
    series = []
    price = base * 0.94
    today = date.today()

    if history_range == "1d":
        start = datetime.combine(today, time(hour=9, minute=30))
        for i in range(78):
            timestamp = start + timedelta(minutes=5 * i)
            price = round(price * (1 + rng.uniform(-0.0025, 0.0025)), 2)
            series.append({"timestamp": timestamp.isoformat(), "close": price})
        interval = "5m"
    elif history_range == "5d":
        trading_days = []
        offset = 0
        while len(trading_days) < 5:
            day = today - timedelta(days=offset)
            offset += 1
            if day.weekday() < 5:
                trading_days.append(day)
        for day in reversed(trading_days):
            start = datetime.combine(day, time(hour=10))
            for i in range(13):
                timestamp = start + timedelta(minutes=30 * i)
                price = round(price * (1 + rng.uniform(-0.004, 0.004)), 2)
                series.append({"timestamp": timestamp.isoformat(), "close": price})
        interval = "30m"
    else:
        target_points = {"1mo": 30, "ytd": min(260, max(30, today.timetuple().tm_yday)), "1y": 260}.get(history_range, 30)
        trading_days = 0
        offset = 0
        while trading_days < target_points:
            day = today - timedelta(days=offset)
            offset += 1
            if day.weekday() >= 5:
                continue
            drift = {"1mo": 0.001, "ytd": 0.0006, "1y": 0.0004}.get(history_range, 0.001)
            price = round(price * (1 + drift + rng.uniform(-0.014, 0.014)), 2)
            series.append({"date": day.isoformat(), "close": price})
            trading_days += 1
        series.reverse()
        interval = "1day"

    return {
        "symbol": symbol,
        "interval": interval,
        "range": history_range,
        "series": series,
        "source_mode": "mock",
    }


def mock_news(symbol: str) -> dict:
    """Generate a short list of plausible news headlines for the symbol."""
    today = date.today()
    items = []
    for i, (title_tpl, source) in enumerate(_NEWS_TEMPLATES[:5]):
        published = today - timedelta(days=i)
        items.append({
            "title": title_tpl.format(sym=symbol),
            "source": source,
            "published_at": f"{published.isoformat()} 09:30",
            "url": f"https://example.com/news/{symbol.lower()}-{i + 1}",
            "summary": (
                f"Market observers are closely watching {symbol} as it continues to show "
                f"resilience amid broader market volatility. Analysts remain broadly positive."
            ),
        })
    return {
        "symbol": symbol,
        "items": items,
        "source_mode": "mock",
    }
