import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"


# ── API helpers ───────────────────────────────────────────────────────────────

def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def list_stocks() -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/stocks", headers=_auth_headers(), timeout=5)
    response.raise_for_status()
    return response.json()


def create_stock(payload: dict) -> dict:
    response = requests.post(f"{API_BASE_URL}/stocks", json=payload, headers=_auth_headers(), timeout=5)
    response.raise_for_status()
    return response.json()


def update_stock(stock_id: int, payload: dict) -> dict:
    response = requests.put(f"{API_BASE_URL}/stocks/{stock_id}", json=payload, headers=_auth_headers(), timeout=5)
    response.raise_for_status()
    return response.json()


def delete_stock(stock_id: int) -> None:
    response = requests.delete(f"{API_BASE_URL}/stocks/{stock_id}", headers=_auth_headers(), timeout=5)
    response.raise_for_status()


def lookup_company_info(symbol: str) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/stocks/lookup/{symbol.strip().upper()}",
        headers=_auth_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def api_login(email: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def api_register(email: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


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


# ── auth gate ─────────────────────────────────────────────────────────────────

if "token" not in st.session_state:
    st.title("📈 AlphaWatch")
    st.caption("Personal Stock Watchlist — please log in or register to continue.")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="you@example.com")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)

        if login_submitted:
            try:
                token_data = api_login(login_email, login_password)
                st.session_state["token"] = token_data["access_token"]
                st.session_state["user_email"] = login_email
                st.rerun()
            except requests.RequestException as err:
                show_request_error("Login failed.", err)

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
            reg_password = st.text_input("Password (min 6 chars)", type="password", key="reg_password")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if reg_submitted:
            try:
                api_register(reg_email, reg_password)
                token_data = api_login(reg_email, reg_password)
                st.session_state["token"] = token_data["access_token"]
                st.session_state["user_email"] = reg_email
                st.rerun()
            except requests.RequestException as err:
                show_request_error("Registration failed.", err)

    st.stop()


# ── sidebar (shown only when logged in) ───────────────────────────────────────

st.sidebar.title("📈 AlphaWatch")
st.sidebar.caption(f"Logged in as **{st.session_state.get('user_email', '')}**")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Add Stock", "Watchlist", "Stock Details"],
    label_visibility="collapsed",
)

st.sidebar.divider()
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.caption(f"Backend: {API_BASE_URL}")

# ── load stocks (shared) ──────────────────────────────────────────────────────

try:
    stocks = list_stocks()
    backend_ok = True
    backend_error = None
except requests.RequestException as _err:
    resp = getattr(_err, "response", None)
    if resp is not None and resp.status_code == 401:
        st.session_state.clear()
        st.rerun()
    stocks = []
    backend_ok = False
    backend_error = _err


# ═══════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════

if page == "Dashboard":
    st.title("Dashboard")

    if not backend_ok:
        show_request_error("Could not connect to backend.", backend_error)

    total = len(stocks)
    favorites = sum(1 for s in stocks if s.get("is_favorite"))
    avg_score = (sum(s["personal_score"] for s in stocks) / total) if total > 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stocks", total)
    col2.metric("Favorites", favorites)
    col3.metric("Avg Personal Score", f"{avg_score:.1f} / 10")

    if not stocks:
        st.info("No stocks yet. Head to **Add Stock** to get started.")
    else:
        import pandas as pd

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Sector Distribution")
            sector_counts = (
                pd.Series([s["sector"] for s in stocks])
                .value_counts()
                .rename("Stocks")
            )
            st.bar_chart(sector_counts)

        with chart_col2:
            st.subheader("Personal Scores")
            scores_df = pd.DataFrame(
                {"Score": [s["personal_score"] for s in stocks]},
                index=[s["symbol"] for s in stocks],
            )
            st.bar_chart(scores_df)

        st.subheader("Current Watchlist")
        display_df = pd.DataFrame(stocks)[
            ["symbol", "company_name", "sector", "target_price", "personal_score", "is_favorite"]
        ].rename(
            columns={
                "symbol": "Symbol",
                "company_name": "Company",
                "sector": "Sector",
                "target_price": "Target ($)",
                "personal_score": "Score",
                "is_favorite": "Fav",
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════
# ADD STOCK
# ═══════════════════════════════════════════════

elif page == "Add Stock":
    st.title("Add Stock")

    if st.session_state.get("stock_added_msg"):
        st.success(st.session_state.pop("stock_added_msg"))

    if "autofill_company_name" not in st.session_state:
        st.session_state["autofill_company_name"] = ""
    if "autofill_sector" not in st.session_state:
        st.session_state["autofill_sector"] = ""

    symbol_input = st.text_input("Stock Symbol", placeholder="AAPL", key="add_symbol")

    if st.button("Auto-fill Company Info"):
        if not symbol_input.strip():
            st.error("Enter a symbol first.")
        else:
            with st.spinner("Looking up company..."):
                try:
                    info = lookup_company_info(symbol_input)
                    st.session_state["autofill_company_name"] = info["company_name"]
                    st.session_state["autofill_sector"] = info["sector"]
                    st.success(f"Found: **{info['company_name']}** — {info['sector']}")
                except requests.RequestException as err:
                    show_request_error("Auto-fill failed.", err)

    with st.form("add_stock_form"):
        company_name = st.text_input(
            "Company Name",
            value=st.session_state["autofill_company_name"],
            placeholder="Apple Inc.",
        )
        sector = st.text_input(
            "Sector",
            value=st.session_state["autofill_sector"],
            placeholder="Technology",
        )
        target_price = st.number_input("Target Price ($)", min_value=0.01, step=1.0, format="%.2f")
        personal_score = st.slider("Personal Score", 1, 10, 5)
        thesis = st.text_area("Investment Thesis", placeholder="Why is this stock on your watchlist?")
        is_favorite = st.checkbox("Mark as Favorite")
        submitted = st.form_submit_button("Add Stock", use_container_width=True)

    if submitted:
        if not symbol_input.strip():
            st.error("Symbol is required.")
        elif not company_name.strip():
            st.error("Company name is required.")
        elif not sector.strip():
            st.error("Sector is required.")
        elif not thesis.strip():
            st.error("Thesis is required.")
        else:
            payload = {
                "symbol": symbol_input.strip().upper(),
                "company_name": company_name.strip(),
                "sector": sector.strip(),
                "target_price": target_price,
                "personal_score": personal_score,
                "thesis": thesis.strip(),
                "is_favorite": is_favorite,
            }
            try:
                create_stock(payload)
                st.session_state["stock_added_msg"] = f"**{symbol_input.upper()}** was added to your watchlist."
                st.session_state["autofill_company_name"] = ""
                st.session_state["autofill_sector"] = ""
                st.rerun()
            except requests.RequestException as err:
                resp = getattr(err, "response", None)
                if resp is not None and resp.status_code == 409:
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except ValueError:
                        detail = resp.text
                    st.error(f"Duplicate stock: {detail}")
                else:
                    show_request_error("Could not add stock.", err)


# ═══════════════════════════════════════════════
# WATCHLIST
# ═══════════════════════════════════════════════

elif page == "Watchlist":
    st.title("Watchlist")

    if not stocks:
        st.info("No stocks yet. Head to **Add Stock** to get started.")
    else:
        import pandas as pd

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            show_favorites_only = st.checkbox("Favorites only")
        with filter_col2:
            sectors = ["All"] + sorted(set(s["sector"] for s in stocks))
            sector_filter = st.selectbox("Filter by sector", sectors)
        with filter_col3:
            sort_by = st.selectbox("Sort by", ["symbol", "personal_score", "target_price"])

        filtered = [s for s in stocks if not show_favorites_only or s["is_favorite"]]
        if sector_filter != "All":
            filtered = [s for s in filtered if s["sector"] == sector_filter]
        filtered = sorted(filtered, key=lambda s: s[sort_by], reverse=(sort_by != "symbol"))

        if not filtered:
            st.info("No stocks match the current filters.")
        else:
            display_df = pd.DataFrame(filtered)[
                ["symbol", "company_name", "sector", "target_price", "personal_score", "is_favorite"]
            ].rename(
                columns={
                    "symbol": "Symbol",
                    "company_name": "Company",
                    "sector": "Sector",
                    "target_price": "Target ($)",
                    "personal_score": "Score",
                    "is_favorite": "Fav",
                }
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Delete a Stock")
        stock_options = {f"{s['symbol']} — {s['company_name']}": s["id"] for s in stocks}
        to_delete_label = st.selectbox("Select stock to delete", list(stock_options.keys()))
        if st.button("Delete Selected Stock", type="secondary"):
            try:
                delete_stock(stock_options[to_delete_label])
                st.success(f"Deleted **{to_delete_label}**.")
                st.rerun()
            except requests.RequestException as err:
                show_request_error("Could not delete stock.", err)


# ═══════════════════════════════════════════════
# STOCK DETAILS
# ═══════════════════════════════════════════════

elif page == "Stock Details":
    st.title("Stock Details")

    if not stocks:
        st.info("No stocks yet. Head to **Add Stock** to get started.")
    else:
        import pandas as pd

        stock_options = {f"{s['symbol']} — {s['company_name']}": s for s in stocks}
        selected_label = st.selectbox("Select a stock", list(stock_options.keys()))
        stock = stock_options[selected_label]

        st.divider()

        info_col, thesis_col = st.columns(2)
        with info_col:
            st.markdown(f"### {stock['symbol']} — {stock['company_name']}")
            st.markdown(f"**Sector:** {stock['sector']}")
            st.markdown(f"**Target Price:** ${stock['target_price']:.2f}")
            st.markdown(f"**Personal Score:** {stock['personal_score']} / 10")
            st.markdown(f"**Status:** {'⭐ Favorite' if stock['is_favorite'] else 'Not a favorite'}")
        with thesis_col:
            st.markdown("**Investment Thesis:**")
            st.info(stock["thesis"])

        st.divider()
        st.subheader("Charts")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.caption("Personal Scores — All Stocks")
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

        st.divider()
        st.subheader("Edit This Stock")

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
            save = st.form_submit_button("Save Changes", use_container_width=True)

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
                st.success("Stock updated successfully!")
                st.rerun()
            except requests.RequestException as err:
                show_request_error("Could not update stock.", err)
