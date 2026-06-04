"""
AlphaWatch — Stock Research Dashboard
A personal stock watchlist with live/mock market data.
"""
import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AlphaWatch",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — dark terminal-inspired theme
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── fonts & base ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── metric cards ── */
[data-testid="metric-container"] {
    background: #0f1117;
    border: 1px solid #1e2130;
    border-radius: 8px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; }
[data-testid="stMetricDelta"] { font-size: 0.85rem; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #080b10;
    border-right: 1px solid #1a1f2e;
}

/* ── expanders ── */
details { border: 1px solid #1e2130 !important; border-radius: 8px !important; }

/* ── stock cards ── */
.stock-card {
    background: #0f1117;
    border: 1px solid #1e2130;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.stock-card:hover { border-color: #3a7bd5; }

.sym { font-family: 'IBM Plex Mono', monospace; font-size: 1.15rem; font-weight: 600; color: #e8eaf0; }
.co-name { font-size: 0.82rem; color: #6b7280; margin-top: 2px; }
.price { font-family: 'IBM Plex Mono', monospace; font-size: 1.25rem; font-weight: 600; }
.up   { color: #22c55e; }
.down { color: #ef4444; }
.flat { color: #9ca3af; }
.badge-fav   { background: #78350f; color: #fcd34d; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; }
.badge-sector{ background: #1e3a5f; color: #93c5fd; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; }
.badge-mock  { background: #1e2130; color: #6b7280; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; }
.badge-live  { background: #052e16; color: #4ade80; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; }
.stat-label  { font-size: 0.72rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value  { font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem; color: #e8eaf0; }
.divider-line { border: none; border-top: 1px solid #1e2130; margin: 10px 0; }
.news-card { background: #0f1117; border: 1px solid #1e2130; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; }
.news-title { font-size: 0.95rem; font-weight: 600; color: #e8eaf0; text-decoration: none; }
.news-meta  { font-size: 0.78rem; color: #6b7280; margin-top: 4px; }
.news-summary { font-size: 0.83rem; color: #9ca3af; margin-top: 8px; line-height: 1.5; }
.page-title { font-size: 1.8rem; font-weight: 700; color: #e8eaf0; margin-bottom: 4px; }
.page-sub   { font-size: 0.9rem; color: #6b7280; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

for _k, _v in [
    ("token", None),
    ("user_email", None),
    ("page", "Dashboard"),
    ("detail_stock_id", None),
    ("edit_stock_id", None),
    ("lookup_result", {}),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# API LAYER — all calls go through the backend, never directly to Alpha Vantage
# ─────────────────────────────────────────────────────────────────────────────

def _h() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def _err(msg: str, exc: requests.RequestException) -> None:
    resp = getattr(exc, "response", None)
    if resp is None:
        st.error(f"{msg} Backend not reachable at {API_BASE_URL}.")
        return
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    st.error(f"{msg} {detail}")


def api_login(email: str, password: str) -> dict:
    r = requests.post(f"{API_BASE_URL}/auth/login", data={"username": email, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()


def api_register(email: str, password: str) -> dict:
    r = requests.post(f"{API_BASE_URL}/auth/register", json={"email": email, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()


def api_stocks() -> list[dict]:
    r = requests.get(f"{API_BASE_URL}/stocks", headers=_h(), timeout=5)
    r.raise_for_status()
    return r.json()


def api_create_stock(payload: dict) -> dict:
    r = requests.post(f"{API_BASE_URL}/stocks", json=payload, headers=_h(), timeout=5)
    r.raise_for_status()
    return r.json()


def api_update_stock(sid: int, payload: dict) -> dict:
    r = requests.put(f"{API_BASE_URL}/stocks/{sid}", json=payload, headers=_h(), timeout=5)
    r.raise_for_status()
    return r.json()


def api_delete_stock(sid: int) -> None:
    r = requests.delete(f"{API_BASE_URL}/stocks/{sid}", headers=_h(), timeout=5)
    r.raise_for_status()


def api_lookup(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/stocks/lookup/{symbol.upper()}", headers=_h(), timeout=10)
    r.raise_for_status()
    return r.json()


def api_quote(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/quote/{symbol}", headers=_h(), timeout=10)
    r.raise_for_status()
    return r.json()


def api_profile(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/profile/{symbol}", headers=_h(), timeout=10)
    r.raise_for_status()
    return r.json()


def api_history(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/history/{symbol}", headers=_h(), timeout=10)
    r.raise_for_status()
    return r.json()


def api_news(symbol: str) -> dict:
    r = requests.get(f"{API_BASE_URL}/market/news/{symbol}", headers=_h(), timeout=10)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# SMALL RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _change_class(change: float) -> str:
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def _change_arrow(change: float) -> str:
    return "▲" if change > 0 else ("▼" if change < 0 else "—")


def _fmt_cap(cap: int | None) -> str:
    if not cap:
        return "N/A"
    if cap >= 1e12:
        return f"${cap / 1e12:.2f}T"
    if cap >= 1e9:
        return f"${cap / 1e9:.1f}B"
    return f"${cap / 1e6:.0f}M"


def _fmt_vol(vol: int | None) -> str:
    if not vol:
        return "N/A"
    if vol >= 1e6:
        return f"{vol / 1e6:.1f}M"
    if vol >= 1e3:
        return f"{vol / 1e3:.0f}K"
    return str(vol)


def _source_badge(mode: str) -> str:
    if mode == "live":
        return '<span class="badge-live">● LIVE</span>'
    return '<span class="badge-mock">◌ DEMO</span>'


# ─────────────────────────────────────────────────────────────────────────────
# AUTH PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_auth_page() -> None:
    col = st.columns([1, 1.4, 1])[1]
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="page-title">📈 AlphaWatch</p>', unsafe_allow_html=True)
        st.markdown('<p class="page-sub">Your personal stock research terminal</p>', unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                try:
                    data = api_login(email, password)
                    st.session_state["token"] = data["access_token"]
                    st.session_state["user_email"] = email
                    st.session_state["page"] = "Dashboard"
                    st.rerun()
                except requests.RequestException as exc:
                    _err("Login failed.", exc)

        with tab_register:
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="r_email")
                reg_pass = st.text_input("Password (min 6 chars)", type="password", key="r_pass")
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)
            if reg_submitted:
                try:
                    api_register(reg_email, reg_pass)
                    st.success("Account created! Sign in above.")
                except requests.RequestException as exc:
                    _err("Registration failed.", exc)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("""
        <div style='padding: 8px 0 20px 0;'>
            <span style='font-size:1.4rem; font-weight:700; color:#e8eaf0; font-family:"IBM Plex Mono",monospace;'>
                📈 AlphaWatch
            </span><br>
            <span style='font-size:0.75rem; color:#6b7280;'>Stock Research Terminal</span>
        </div>
        """, unsafe_allow_html=True)

        pages = ["Dashboard", "Watchlist", "Add Stock"]
        icons = {"Dashboard": "⬡", "Watchlist": "☰", "Add Stock": "+"}

        for p in pages:
            active = st.session_state["page"] == p and st.session_state.get("detail_stock_id") is None
            style = "background:#1a2235; border-radius:6px; " if active else ""
            if st.button(
                f"{icons[p]}  {p}",
                key=f"nav_{p}",
                use_container_width=True,
            ):
                st.session_state["page"] = p
                st.session_state["detail_stock_id"] = None
                st.session_state["edit_stock_id"] = None
                st.rerun()

        st.markdown("<hr style='border-color:#1e2130; margin:16px 0;'>", unsafe_allow_html=True)
        st.markdown(
            f"<span style='font-size:0.78rem; color:#6b7280;'>Signed in as<br>"
            f"<span style='color:#93c5fd;'>{st.session_state['user_email']}</span></span>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            for k in ["token", "user_email", "detail_stock_id", "edit_stock_id", "lookup_result"]:
                st.session_state[k] = None if k != "lookup_result" else {}
            st.session_state["page"] = "Dashboard"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_dashboard(stocks: list[dict]) -> None:
    st.markdown('<p class="page-title">Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Your portfolio at a glance</p>', unsafe_allow_html=True)

    if not stocks:
        st.info("Your watchlist is empty. Go to **Add Stock** to get started.")
        return

    # ── fetch live quotes for all stocks (best-effort) ────────────────────────
    quotes: dict[str, dict] = {}
    for s in stocks:
        try:
            quotes[s["symbol"]] = api_quote(s["symbol"])
        except Exception:
            pass

    # ── top metrics ───────────────────────────────────────────────────────────
    avg_score = sum(s["personal_score"] for s in stocks) / len(stocks)
    favs = sum(1 for s in stocks if s["is_favorite"])

    gainers = sorted(
        [s for s in stocks if s["symbol"] in quotes],
        key=lambda s: quotes[s["symbol"]].get("change_percent", 0),
        reverse=True,
    )
    top_gainer = gainers[0] if gainers else None
    top_loser = gainers[-1] if len(gainers) > 1 else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Stocks Tracked", len(stocks))
    c2.metric("Favorites", favs)
    c3.metric("Avg Score", f"{avg_score:.1f} / 10")

    if top_gainer and top_gainer["symbol"] in quotes:
        q = quotes[top_gainer["symbol"]]
        c4.metric(
            f"Top Gainer · {top_gainer['symbol']}",
            f"${q['price']:.2f}",
            f"+{q['change_percent']:.2f}%",
        )
    else:
        c4.metric("Top Gainer", "—")

    if top_loser and top_loser["symbol"] in quotes:
        q = quotes[top_loser["symbol"]]
        c5.metric(
            f"Top Loser · {top_loser['symbol']}",
            f"${q['price']:.2f}",
            f"{q['change_percent']:.2f}%",
        )
    else:
        c5.metric("Top Loser", "—")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── charts ────────────────────────────────────────────────────────────────
    try:
        import pandas as pd

        chart_l, chart_r = st.columns(2)

        with chart_l:
            st.markdown("**Sector Allocation**")
            sector_counts = pd.Series([s["sector"] for s in stocks]).value_counts()
            st.bar_chart(sector_counts, use_container_width=True, height=220)

        with chart_r:
            st.markdown("**Score Ranking**")
            score_df = pd.DataFrame(
                {"Score": [s["personal_score"] for s in stocks]},
                index=[s["symbol"] for s in stocks],
            ).sort_values("Score", ascending=True)
            st.bar_chart(score_df, use_container_width=True, height=220)

    except ImportError:
        st.info("Install pandas to enable charts.")

    # ── watchlist overview table ───────────────────────────────────────────────
    st.markdown("<br>**Watchlist Overview**", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#1e2130; margin:4px 0 14px 0;'>", unsafe_allow_html=True)

    header = st.columns([1, 2.5, 1.5, 1.5, 1.5, 1])
    for col, label in zip(header, ["Symbol", "Company", "Price", "Change", "Sector", "Score"]):
        col.markdown(f"<span class='stat-label'>{label}</span>", unsafe_allow_html=True)

    for s in stocks:
        sym = s["symbol"]
        q = quotes.get(sym, {})
        price = q.get("price")
        chg = q.get("change", 0.0)
        chgp = q.get("change_percent", 0.0)
        cls = _change_class(chg)
        arrow = _change_arrow(chg)

        row = st.columns([1, 2.5, 1.5, 1.5, 1.5, 1])
        row[0].markdown(f"<span class='sym'>{sym}</span>", unsafe_allow_html=True)
        row[1].markdown(f"<span style='color:#9ca3af; font-size:0.88rem;'>{s['company_name']}</span>", unsafe_allow_html=True)
        row[2].markdown(
            f"<span class='price {cls}'>${price:.2f}</span>" if price else "<span class='flat'>—</span>",
            unsafe_allow_html=True,
        )
        row[3].markdown(
            f"<span class='{cls}'>{arrow} {chgp:+.2f}%</span>" if price else "<span class='flat'>—</span>",
            unsafe_allow_html=True,
        )
        row[4].markdown(f"<span class='badge-sector'>{s['sector'][:18]}</span>", unsafe_allow_html=True)
        row[5].markdown(f"<span class='stat-value'>{s['personal_score']}/10</span>", unsafe_allow_html=True)

        if st.button("View", key=f"dash_view_{s['id']}", use_container_width=False):
            st.session_state["detail_stock_id"] = s["id"]
            st.rerun()

        st.markdown("<hr style='border-color:#111827; margin:4px 0;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# WATCHLIST PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_watchlist(stocks: list[dict]) -> None:
    st.markdown('<p class="page-title">Watchlist</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">All tracked positions</p>', unsafe_allow_html=True)

    if not stocks:
        st.info("Your watchlist is empty. Go to **Add Stock** to get started.")
        return

    for s in stocks:
        sym = s["symbol"]
        fav_badge = '<span class="badge-fav">★ FAV</span> ' if s["is_favorite"] else ""

        # fetch quote per card
        try:
            q = api_quote(sym)
            price = q["price"]
            chg = q["change"]
            chgp = q["change_percent"]
            cls = _change_class(chg)
            arrow = _change_arrow(chg)
            price_html = f'<span class="price {cls}">${price:.2f}</span>'
            change_html = f'<span class="{cls}">{arrow} {chg:+.2f} ({chgp:+.2f}%)</span>'
            src = _source_badge(q.get("source_mode", "mock"))
            prev_close = q.get("previous_close")
            open_p = q.get("open")
            high = q.get("day_high")
            low = q.get("day_low")
            volume = q.get("volume")
        except Exception:
            price_html = '<span class="flat">—</span>'
            change_html = '<span class="flat">—</span>'
            src = '<span class="badge-mock">◌ DEMO</span>'
            prev_close = open_p = high = low = volume = None

        with st.expander(f"{sym}  —  {s['company_name']}", expanded=False):
            st.markdown(
                f"{fav_badge}"
                f'<span class="badge-sector">{s["sector"]}</span> '
                f"{src}",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.markdown(
                f"<span class='stat-label'>Current Price</span><br>{price_html}",
                unsafe_allow_html=True,
            )
            mc2.markdown(
                f"<span class='stat-label'>Daily Change</span><br>{change_html}",
                unsafe_allow_html=True,
            )
            mc3.markdown(
                f"<span class='stat-label'>Target Price</span><br>"
                f"<span class='stat-value'>${s['target_price']:.2f}</span>",
                unsafe_allow_html=True,
            )
            mc4.markdown(
                f"<span class='stat-label'>Personal Score</span><br>"
                f"<span class='stat-value'>{s['personal_score']} / 10</span>",
                unsafe_allow_html=True,
            )

            if any(v is not None for v in [prev_close, open_p, high, low, volume]):
                st.markdown("<hr class='divider-line'>", unsafe_allow_html=True)
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                for col, label, val in [
                    (sc1, "Prev Close", f"${prev_close:.2f}" if prev_close else "—"),
                    (sc2, "Open", f"${open_p:.2f}" if open_p else "—"),
                    (sc3, "Day High", f"${high:.2f}" if high else "—"),
                    (sc4, "Day Low", f"${low:.2f}" if low else "—"),
                    (sc5, "Volume", _fmt_vol(volume)),
                ]:
                    col.markdown(
                        f"<span class='stat-label'>{label}</span><br>"
                        f"<span class='stat-value'>{val}</span>",
                        unsafe_allow_html=True,
                    )

            st.markdown("<hr class='divider-line'>", unsafe_allow_html=True)
            st.markdown(
                f"<span class='stat-label'>Thesis</span><br>"
                f"<span style='font-size:0.88rem; color:#9ca3af;'>{s['thesis']}</span>",
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("🔍 Details", key=f"wl_detail_{s['id']}", use_container_width=True):
                    st.session_state["detail_stock_id"] = s["id"]
                    st.rerun()
            with b2:
                if st.button("✏️ Edit", key=f"wl_edit_{s['id']}", use_container_width=True):
                    st.session_state["edit_stock_id"] = s["id"]
                    st.rerun()
            with b3:
                if st.button("🗑️ Remove", key=f"wl_del_{s['id']}", use_container_width=True):
                    try:
                        api_delete_stock(s["id"])
                        st.rerun()
                    except requests.RequestException as exc:
                        _err("Could not delete.", exc)

    # ── edit panel ────────────────────────────────────────────────────────────
    edit_id = st.session_state.get("edit_stock_id")
    if edit_id:
        stock = next((s for s in stocks if s["id"] == edit_id), None)
        if stock:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**Edit — {stock['symbol']}**")
            with st.form("edit_form"):
                e_sym  = st.text_input("Symbol", value=stock["symbol"])
                e_name = st.text_input("Company Name", value=stock["company_name"])
                e_sect = st.text_input("Sector", value=stock["sector"])
                e_tgt  = st.number_input("Target Price ($)", min_value=0.01, value=float(stock["target_price"]), step=1.0, format="%.2f")
                e_scr  = st.slider("Personal Score", 1, 10, value=stock["personal_score"])
                e_thes = st.text_area("Thesis", value=stock["thesis"])
                e_fav  = st.checkbox("Favorite", value=stock["is_favorite"])
                sv, cn = st.columns(2)
                save   = sv.form_submit_button("Save Changes", use_container_width=True)
                cancel = cn.form_submit_button("Cancel", use_container_width=True)

            if cancel:
                st.session_state["edit_stock_id"] = None
                st.rerun()
            if save:
                try:
                    api_update_stock(stock["id"], {
                        "symbol": e_sym.strip().upper(),
                        "company_name": e_name.strip(),
                        "sector": e_sect.strip(),
                        "target_price": e_tgt,
                        "personal_score": e_scr,
                        "thesis": e_thes.strip(),
                        "is_favorite": e_fav,
                    })
                    st.session_state["edit_stock_id"] = None
                    st.success("Saved!")
                    st.rerun()
                except requests.RequestException as exc:
                    _err("Could not save.", exc)


# ─────────────────────────────────────────────────────────────────────────────
# ADD STOCK PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_add_stock() -> None:
    st.markdown('<p class="page-title">Add Stock</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Add a new position to your watchlist</p>', unsafe_allow_html=True)

    # ── symbol auto-fill ──────────────────────────────────────────────────────
    with st.expander("🔍 Auto-fill from symbol lookup", expanded=True):
        lc1, lc2 = st.columns([3, 1])
        lookup_sym = lc1.text_input("Enter ticker symbol", placeholder="e.g. AAPL, NVDA, TSLA")
        if lc2.button("Look Up", use_container_width=True):
            if lookup_sym.strip():
                try:
                    info = api_lookup(lookup_sym.strip())
                    st.session_state["lookup_result"] = info
                    st.success(f"Found: **{info['company_name']}** ({info['sector']})")
                except requests.RequestException as exc:
                    _err("Lookup failed.", exc)
            else:
                st.warning("Enter a symbol first.")

    lookup = st.session_state.get("lookup_result") or {}

    # ── form ──────────────────────────────────────────────────────────────────
    with st.form("add_stock_form", clear_on_submit=False):
        fc1, fc2 = st.columns(2)
        symbol       = fc1.text_input("Ticker Symbol *", value=lookup.get("symbol", ""), placeholder="e.g. AAPL")
        company_name = fc2.text_input("Company Name *", value=lookup.get("company_name", ""))
        sector       = st.text_input("Sector *", value=lookup.get("sector", ""), placeholder="e.g. Technology")
        pc1, pc2     = st.columns(2)
        target_price = pc1.number_input("Target Price ($) *", min_value=0.01, step=1.0, format="%.2f", value=100.00)
        personal_score = pc2.slider("Personal Score (1–10)", 1, 10, value=7)
        thesis       = st.text_area("Investment Thesis *", placeholder="Why do you like this stock?", height=100)
        is_favorite  = st.checkbox("⭐ Mark as Favorite")
        submitted    = st.form_submit_button("Add to Watchlist", use_container_width=True)

    if submitted:
        sym_clean = symbol.strip().upper()
        if not sym_clean or not company_name.strip() or not sector.strip() or not thesis.strip():
            st.warning("Please fill in all required fields (*).")
        else:
            try:
                api_create_stock({
                    "symbol": sym_clean,
                    "company_name": company_name.strip(),
                    "sector": sector.strip(),
                    "target_price": target_price,
                    "personal_score": personal_score,
                    "thesis": thesis.strip(),
                    "is_favorite": is_favorite,
                })
                st.session_state["lookup_result"] = {}
                st.success(f"✅ {sym_clean} added to your watchlist!")
                st.session_state["page"] = "Watchlist"
                st.rerun()
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 409:
                    st.error(f"{sym_clean} is already in your watchlist.")
                else:
                    _err("Could not add stock.", exc)
            except requests.RequestException as exc:
                _err("Could not add stock.", exc)


# ─────────────────────────────────────────────────────────────────────────────
# STOCK DETAILS PAGE
# ─────────────────────────────────────────────────────────────────────────────

def show_stock_details(stock: dict) -> None:
    sym = stock["symbol"]

    if st.button("← Back", key="back_btn"):
        st.session_state["detail_stock_id"] = None
        st.rerun()

    # ── header ────────────────────────────────────────────────────────────────
    try:
        quote = api_quote(sym)
        price  = quote["price"]
        chg    = quote["change"]
        chgp   = quote["change_percent"]
        cls    = _change_class(chg)
        arrow  = _change_arrow(chg)
        src    = _source_badge(quote.get("source_mode", "mock"))
        is_mock_quote = quote.get("source_mode") == "mock"
    except Exception:
        price = chg = chgp = 0.0
        cls = "flat"; arrow = "—"; src = ""; is_mock_quote = True

    st.markdown(
        f"<div style='margin-bottom:8px;'>"
        f"<span class='sym' style='font-size:2rem;'>{sym}</span>&nbsp;&nbsp;"
        f"<span style='color:#6b7280; font-size:1rem;'>{stock['company_name']}</span>"
        f"&nbsp;&nbsp;{src}"
        f"</div>"
        f"<div style='margin-bottom:20px;'>"
        f"<span class='price {cls}' style='font-size:2.2rem;'>${price:.2f}</span>&nbsp;&nbsp;"
        f"<span class='{cls}' style='font-size:1.1rem;'>{arrow} {chg:+.2f} ({chgp:+.2f}%)</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if is_mock_quote:
        st.info("ℹ️ Showing demo market data. Yahoo Finance may be temporarily unreachable.", icon="🔵")

    # ── quote stats grid ──────────────────────────────────────────────────────
    st.markdown("**Quote**")
    qs = st.columns(6)
    stat_pairs = [
        ("Prev Close",  f"${quote.get('previous_close', 0):.2f}" if price else "—"),
        ("Open",        f"${quote.get('open', 0):.2f}" if price else "—"),
        ("Day High",    f"${quote.get('day_high', 0):.2f}" if price else "—"),
        ("Day Low",     f"${quote.get('day_low', 0):.2f}" if price else "—"),
        ("Volume",      _fmt_vol(quote.get("volume")) if price else "—"),
        ("Sector",      stock["sector"]),
    ]
    for col, (label, val) in zip(qs, stat_pairs):
        col.markdown(
            f"<span class='stat-label'>{label}</span><br><span class='stat-value'>{val}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color:#1e2130; margin:18px 0;'>", unsafe_allow_html=True)

    # ── my notes + company profile side by side ───────────────────────────────
    notes_col, profile_col = st.columns([1, 1.6])

    with notes_col:
        st.markdown("**My Notes**")
        fav_txt = "⭐ Yes" if stock["is_favorite"] else "No"
        st.markdown(
            f"<div class='stock-card'>"
            f"<span class='stat-label'>Target Price</span><br>"
            f"<span class='stat-value' style='font-size:1.3rem;'>${stock['target_price']:.2f}</span><br><br>"
            f"<span class='stat-label'>Personal Score</span><br>"
            f"<span class='stat-value' style='font-size:1.1rem;'>{stock['personal_score']} / 10</span><br><br>"
            f"<span class='stat-label'>Favorite</span><br>"
            f"<span class='stat-value'>{fav_txt}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='background:#0f1117; border:1px solid #1e2130; border-radius:8px; padding:14px 18px; margin-top:10px;'>"
            f"<span class='stat-label'>Thesis</span><br>"
            f"<span style='font-size:0.88rem; color:#9ca3af; line-height:1.6;'>{stock['thesis']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with profile_col:
        st.markdown("**Company Profile**")
        try:
            profile = api_profile(sym)
            cap_str = _fmt_cap(profile.get("market_cap"))
            site = profile.get("website", "")
            site_link = f'<a href="{site}" target="_blank" style="color:#3a7bd5; font-size:0.82rem;">{site}</a>' if site else ""
            desc = profile.get("description", "")[:500]
            desc_ellipsis = "…" if len(profile.get("description", "")) > 500 else ""
            country = profile.get("country", "")
            industry = profile.get("industry", "")
            country_span = f"&nbsp;<span class='badge-sector'>{country}</span>" if country else ""
            site_html = f"&nbsp;&nbsp;{site_link}" if site_link else ""

            st.markdown(
                f"<div class='stock-card'>"
                f"<span class='badge-sector'>{industry}</span>{country_span}"
                f"<br><br>"
                f"<span class='stat-label'>Market Cap</span> "
                f"<span class='stat-value'>{cap_str}</span>{site_html}"
                f"<br><br>"
                f"<span style='font-size:0.85rem; color:#9ca3af; line-height:1.6;'>{desc}{desc_ellipsis}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        except requests.RequestException as exc:
            _err("Could not load profile.", exc)

    st.markdown("<hr style='border-color:#1e2130; margin:18px 0;'>", unsafe_allow_html=True)

    # ── price history chart ───────────────────────────────────────────────────
    st.markdown("**Price History — Last 30 Trading Days**")
    try:
        import pandas as pd

        hist = api_history(sym)
        series = hist.get("series", [])
        mode = hist.get("source_mode", "mock")
        if mode == "mock":
            st.caption("📋 Demo chart · Yahoo Finance unreachable")

        if series:
            df = pd.DataFrame(series)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            st.line_chart(df["close"], use_container_width=True, height=260)
        else:
            st.info("No price history available.")
    except requests.RequestException as exc:
        _err("Could not load history.", exc)
    except ImportError:
        st.info("Install pandas to enable charts.")

    st.markdown("<hr style='border-color:#1e2130; margin:18px 0;'>", unsafe_allow_html=True)

    # ── news ──────────────────────────────────────────────────────────────────
    st.markdown("**Latest News**")
    try:
        news = api_news(sym)
        items = news.get("items", [])
        mode = news.get("source_mode", "mock")
        if mode == "mock":
            st.caption("📋 Demo headlines · Yahoo Finance unreachable")

        if not items:
            st.info("No recent news found.")
        for item in items:
            summary = item.get("summary", "") or ""
            summary_trunc = summary[:220] + ("…" if len(summary) > 220 else "")
            summary_html = f"<div class='news-summary'>{summary_trunc}</div>" if summary else ""
            st.markdown(
                f"<div class='news-card'>"
                f"<a class='news-title' href='{item['url']}' target='_blank'>{item['title']}</a>"
                f"<div class='news-meta'>{item['source']} &nbsp;·&nbsp; {item['published_at']}</div>"
                f"{summary_html}"
                f"</div>",
                unsafe_allow_html=True,
            )
    except requests.RequestException as exc:
        _err("Could not load news.", exc)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP SHELL
# ─────────────────────────────────────────────────────────────────────────────

def show_main_app() -> None:
    render_sidebar()

    # Load stocks once per render
    try:
        stocks = api_stocks()
    except requests.RequestException as exc:
        _err("Could not load watchlist.", exc)
        return

    # Stock details overrides the page nav
    detail_id = st.session_state.get("detail_stock_id")
    if detail_id:
        stock = next((s for s in stocks if s["id"] == detail_id), None)
        if stock:
            show_stock_details(stock)
            return
        st.session_state["detail_stock_id"] = None

    page = st.session_state.get("page", "Dashboard")
    if page == "Dashboard":
        show_dashboard(stocks)
    elif page == "Watchlist":
        show_watchlist(stocks)
    elif page == "Add Stock":
        show_add_stock()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state["token"] is None:
    show_auth_page()
else:
    show_main_app()
