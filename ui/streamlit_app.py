import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"


# ── API helpers ───────────────────────────────────────────────────────────────

def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def list_stocks() -> list[dict]:
    r = requests.get(f"{API_BASE_URL}/stocks", headers=_auth_headers(), timeout=5)
    r.raise_for_status()
    return r.json()


def create_stock(payload: dict) -> dict:
    r = requests.post(f"{API_BASE_URL}/stocks", json=payload, headers=_auth_headers(), timeout=5)
    r.raise_for_status()
    return r.json()


def update_stock(stock_id: int, payload: dict) -> dict:
    r = requests.put(f"{API_BASE_URL}/stocks/{stock_id}", json=payload, headers=_auth_headers(), timeout=5)
    r.raise_for_status()
    return r.json()


def delete_stock(stock_id: int) -> None:
    r = requests.delete(f"{API_BASE_URL}/stocks/{stock_id}", headers=_auth_headers(), timeout=5)
    r.raise_for_status()


def lookup_company_info(symbol: str) -> dict:
    r = requests.get(
        f"{API_BASE_URL}/stocks/lookup/{symbol.strip().upper()}",
        headers=_auth_headers(),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def api_login(email: str, password: str) -> dict:
    r = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": email, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def api_register(email: str, password: str) -> dict:
    r = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def fetch_market_profile(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/profile/{symbol}", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_market_quote(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/quote/{symbol}", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_market_history(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/history/{symbol}", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_market_news(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/news/{symbol}", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def show_request_error(message: str, error: requests.RequestException) -> None:
    resp = getattr(error, "response", None)
    if resp is None:
        st.error(f"{message} Make sure the FastAPI backend is running at {API_BASE_URL}.")
        return
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    st.error(f"{message} {detail}")


# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="AlphaWatch", page_icon="📈", layout="wide")

# ── session state defaults ────────────────────────────────────────────────────

for key, default in [
    ("token", None),
    ("user_email", None),
    ("selected_stock_id", None),
    ("detail_stock_id", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── auth wall ─────────────────────────────────────────────────────────────────

def show_auth_page() -> None:
    st.title("📈 AlphaWatch")
    st.caption("Your personal stock watchlist")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            try:
                token_data = api_login(email, password)
                st.session_state["token"] = token_data["access_token"]
                st.session_state["user_email"] = email
                st.rerun()
            except requests.RequestException as err:
                show_request_error("Login failed.", err)

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if reg_submitted:
            try:
                api_register(reg_email, reg_password)
                st.success("Account created! Please log in.")
            except requests.RequestException as err:
                show_request_error("Registration failed.", err)


# ── stock details page ────────────────────────────────────────────────────────

def show_stock_details(stock: dict) -> None:
    sym = stock["symbol"]

    if st.button("← Back to Watchlist"):
        st.session_state["detail_stock_id"] = None
        st.rerun()

    st.title(f"📊 {sym} — {stock['company_name']}")
    st.caption(f"Sector: {stock['sector']}")
    st.divider()

    # ── personal notes (always available, no API needed) ─────────────────────
    st.subheader("📝 My Notes")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Target Price", f"${stock['target_price']:.2f}")
    p2.metric("Personal Score", f"{stock['personal_score']}/10")
    p3.metric("Favorite", "⭐ Yes" if stock["is_favorite"] else "No")
    p4.metric("Sector", stock["sector"])
    st.info(f"**Thesis:** {stock['thesis']}")
    st.divider()

    # ── market data (always renders — live or mock) ───────────────────────────
    st.subheader("📡 Market Data")

    # Track whether any section used mock data
    any_mock = False

    # Quote + Profile side by side
    col_quote, col_profile = st.columns([1, 2])

    with col_quote:
        st.markdown("**Current Quote**")
        try:
            quote = fetch_market_quote(sym)
            if quote.get("source_mode") == "mock":
                any_mock = True
            st.metric(
                label="Price",
                value=f"${quote['price']:.2f}",
                delta=f"{quote['change']:+.2f} ({quote['change_percent']:+.2f}%)",
            )
            if quote.get("previous_close"):
                st.caption(f"Previous close: ${quote['previous_close']:.2f}")
        except requests.RequestException as err:
            show_request_error("Could not load quote.", err)

    with col_profile:
        st.markdown("**Company Profile**")
        try:
            profile = fetch_market_profile(sym)
            if profile.get("source_mode") == "mock":
                any_mock = True
            if profile.get("market_cap"):
                cap = profile["market_cap"]
                cap_str = f"${cap / 1e12:.2f}T" if cap >= 1e12 else f"${cap / 1e9:.1f}B"
                st.caption(f"Market Cap: {cap_str} · Industry: {profile.get('industry', '—')}")
            desc = profile.get("description", "")
            if desc:
                st.write(desc[:400] + ("…" if len(desc) > 400 else ""))
        except requests.RequestException as err:
            show_request_error("Could not load profile.", err)

    # Mock data banner — shown once, below both columns
    if any_mock:
        st.info(
            "ℹ️ Showing demo market data. "
            "Set `ALPHAVANTAGE_API_KEY` to see live prices.",
            icon="🔵",
        )

    st.divider()

    # Price chart
    st.subheader("📈 Price History (Last 30 Trading Days)")
    try:
        import pandas as pd  # noqa: PLC0415

        history = fetch_market_history(sym)
        if history.get("source_mode") == "mock":
            st.caption("📋 Demo chart — set API key for real price history")
        series = history.get("series", [])
        if series:
            df = pd.DataFrame(series).set_index("date")
            df.index = pd.to_datetime(df.index)
            st.line_chart(df["close"], use_container_width=True)
        else:
            st.info("No history data available.")
    except requests.RequestException as err:
        show_request_error("Could not load price history.", err)
    except ImportError:
        st.info("Install pandas to enable charts.")

    st.divider()

    # News
    st.subheader("📰 Latest News")
    try:
        news = fetch_market_news(sym)
        if news.get("source_mode") == "mock":
            st.caption("📋 Demo headlines — set API key for real news")
        items = news.get("items", [])
        if not items:
            st.info("No recent news found for this symbol.")
        for item in items:
            with st.container():
                st.markdown(f"**[{item['title']}]({item['url']})**")
                st.caption(f"{item['source']} · {item['published_at']}")
                if item.get("summary"):
                    st.write(item["summary"][:200] + ("…" if len(item["summary"]) > 200 else ""))
                st.divider()
    except requests.RequestException as err:
        show_request_error("Could not load news.", err)


# ── main app ──────────────────────────────────────────────────────────────────

def show_main_app() -> None:
    with st.sidebar:
        st.title("📈 AlphaWatch")
        st.caption(f"Logged in as **{st.session_state['user_email']}**")
        st.divider()

        page = st.radio(
            "Navigate",
            ["Watchlist", "Add Stock"],
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["user_email"] = None
            st.session_state["detail_stock_id"] = None
            st.session_state["selected_stock_id"] = None
            st.rerun()

    try:
        stocks = list_stocks()
    except requests.RequestException as err:
        show_request_error("Could not load watchlist.", err)
        return

    # ── stock details ─────────────────────────────────────────────────────────
    detail_id = st.session_state.get("detail_stock_id")
    if detail_id:
        stock = next((s for s in stocks if s["id"] == detail_id), None)
        if stock:
            show_stock_details(stock)
            return
        st.session_state["detail_stock_id"] = None

    # ── watchlist page ────────────────────────────────────────────────────────
    if page == "Watchlist":
        st.header("My Watchlist")

        if not stocks:
            st.info("Your watchlist is empty. Use **Add Stock** in the sidebar to get started.")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Stocks", len(stocks))
        col2.metric("Favorites", sum(1 for s in stocks if s["is_favorite"]))
        avg_score = sum(s["personal_score"] for s in stocks) / len(stocks)
        col3.metric("Avg Score", f"{avg_score:.1f}")

        st.divider()

        selected_id = st.session_state.get("selected_stock_id")

        for stock in stocks:
            is_fav = "⭐" if stock["is_favorite"] else ""
            with st.expander(
                f"{is_fav} **{stock['symbol']}** — {stock['company_name']} (Score: {stock['personal_score']}/10)"
            ):
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Sector", stock["sector"])
                col_b.metric("Target Price", f"${stock['target_price']:.2f}")
                col_c.metric("Score", f"{stock['personal_score']}/10")
                st.caption(f"**Thesis:** {stock['thesis']}")

                btn1, btn2, btn3 = st.columns(3)
                with btn1:
                    if st.button("🔍 Details", key=f"detail_{stock['id']}", use_container_width=True):
                        st.session_state["detail_stock_id"] = stock["id"]
                        st.session_state["selected_stock_id"] = None
                        st.rerun()
                with btn2:
                    if st.button("✏️ Edit", key=f"edit_{stock['id']}", use_container_width=True):
                        st.session_state["selected_stock_id"] = stock["id"]
                        st.rerun()
                with btn3:
                    if st.button("🗑️ Delete", key=f"del_{stock['id']}", use_container_width=True):
                        try:
                            delete_stock(stock["id"])
                            if st.session_state.get("selected_stock_id") == stock["id"]:
                                st.session_state["selected_stock_id"] = None
                            st.rerun()
                        except requests.RequestException as err:
                            show_request_error("Could not delete stock.", err)

        # Portfolio charts
        st.divider()
        st.subheader("Portfolio Overview")
        try:
            import pandas as pd  # noqa: PLC0415

            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.caption("Personal Score by Symbol")
                scores_df = pd.DataFrame(
                    {"Score": [s["personal_score"] for s in stocks]},
                    index=[s["symbol"] for s in stocks],
                )
                st.bar_chart(scores_df)

            with chart_col2:
                st.caption("Sector Distribution")
                sector_counts = (
                    pd.Series([s["sector"] for s in stocks])
                    .value_counts()
                    .rename("Stocks")
                )
                st.bar_chart(sector_counts)
        except ImportError:
            st.info("Install pandas to enable portfolio charts.")

        # Edit panel
        if selected_id:
            stock = next((s for s in stocks if s["id"] == selected_id), None)
            if stock:
                st.divider()
                st.subheader(f"Edit — {stock['symbol']}")

                with st.form("edit_stock_form"):
                    new_symbol = st.text_input("Symbol", value=stock["symbol"])
                    new_company = st.text_input("Company Name", value=stock["company_name"])
                    new_sector = st.text_input("Sector", value=stock["sector"])
                    new_target = st.number_input(
                        "Target Price ($)",
                        min_value=0.01,
                        value=float(stock["target_price"]),
                        step=1.0,
                        format="%.2f",
                    )
                    new_score = st.slider("Personal Score", 1, 10, value=stock["personal_score"])
                    new_thesis = st.text_area("Thesis", value=stock["thesis"])
                    new_fav = st.checkbox("Favorite", value=stock["is_favorite"])

                    save_col, cancel_col = st.columns(2)
                    save = save_col.form_submit_button("Save Changes", use_container_width=True)
                    cancel = cancel_col.form_submit_button("Cancel", use_container_width=True)

                if cancel:
                    st.session_state["selected_stock_id"] = None
                    st.rerun()

                if save:
                    payload = {
                        "symbol": new_symbol.strip().upper(),
                        "company_name": new_company.strip(),
                        "sector": new_sector.strip(),
                        "target_price": new_target,
                        "personal_score": new_score,
                        "thesis": new_thesis.strip(),
                        "is_favorite": new_fav,
                    }
                    try:
                        update_stock(stock["id"], payload)
                        st.session_state["selected_stock_id"] = None
                        st.success("Stock updated!")
                        st.rerun()
                    except requests.RequestException as err:
                        show_request_error("Could not update stock.", err)

    # ── add stock page ────────────────────────────────────────────────────────
    elif page == "Add Stock":
        st.header("Add Stock to Watchlist")

        with st.expander("🔍 Auto-fill from symbol (requires API key)"):
            lookup_symbol = st.text_input("Enter symbol to look up", placeholder="e.g. AAPL")
            if st.button("Look up"):
                try:
                    info = lookup_company_info(lookup_symbol)
                    st.session_state["lookup_result"] = info
                    st.success(f"Found: {info['company_name']} ({info['sector']})")
                except requests.RequestException as err:
                    show_request_error("Lookup failed.", err)

        lookup = st.session_state.get("lookup_result", {})

        with st.form("add_stock_form"):
            symbol = st.text_input("Symbol *", value=lookup.get("symbol", "")).strip().upper()
            company_name = st.text_input("Company Name *", value=lookup.get("company_name", ""))
            sector = st.text_input("Sector *", value=lookup.get("sector", ""))
            target_price = st.number_input("Target Price ($) *", min_value=0.01, step=1.0, format="%.2f")
            personal_score = st.slider("Personal Score (1–10)", 1, 10, value=7)
            thesis = st.text_area("Investment Thesis *")
            is_favorite = st.checkbox("Mark as Favorite")
            submitted = st.form_submit_button("Add to Watchlist", use_container_width=True)

        if submitted:
            if not symbol or not company_name or not sector or not thesis:
                st.warning("Please fill in all required fields (*).")
            else:
                payload = {
                    "symbol": symbol,
                    "company_name": company_name,
                    "sector": sector,
                    "target_price": target_price,
                    "personal_score": personal_score,
                    "thesis": thesis,
                    "is_favorite": is_favorite,
                }
                try:
                    create_stock(payload)
                    st.session_state.pop("lookup_result", None)
                    st.success(f"{symbol} added to your watchlist!")
                    st.rerun()
                except requests.RequestException as err:
                    show_request_error("Could not add stock.", err)


# ── routing ───────────────────────────────────────────────────────────────────

if st.session_state["token"] is None:
    show_auth_page()
else:
    show_main_app()
