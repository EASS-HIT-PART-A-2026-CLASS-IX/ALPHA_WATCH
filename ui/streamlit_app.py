import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


def list_stocks() -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/stocks", timeout=5)
    response.raise_for_status()
    return response.json()


def create_stock(payload: dict) -> dict:
    response = requests.post(f"{API_BASE_URL}/stocks", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def lookup_company_info(symbol: str) -> dict:
    clean_symbol = symbol.strip().upper()
    response = requests.get(f"{API_BASE_URL}/stocks/lookup/{clean_symbol}", timeout=10)
    response.raise_for_status()
    return response.json()


def calculate_summary(stocks: list[dict]) -> tuple[int, int, float]:
    total_stocks = len(stocks)
    total_favorites = sum(1 for stock in stocks if stock.get("is_favorite"))

    if total_stocks == 0:
        average_score = 0.0
    else:
        total_score = sum(stock.get("personal_score", 0) for stock in stocks)
        average_score = total_score / total_stocks

    return total_stocks, total_favorites, average_score


def show_request_error(message: str, error: requests.RequestException) -> None:
    response = getattr(error, "response", None)

    if response is None:
        st.error(f"{message} Make sure the FastAPI backend is running at {API_BASE_URL}.")
        return

    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text

    st.error(f"{message} Backend returned {response.status_code}: {detail}")


st.set_page_config(page_title="AlphaWatch", layout="wide")

st.title("AlphaWatch")
st.write("A small local interface for managing your personal stock watchlist.")

if st.session_state.get("stock_created"):
    st.success("Stock added successfully.")
    st.session_state["stock_created"] = False

try:
    stocks = list_stocks()
except requests.RequestException as error:
    stocks = []
    show_request_error("Could not load stocks.", error)

total_stocks, total_favorites, average_score = calculate_summary(stocks)

metric_one, metric_two, metric_three = st.columns(3)
metric_one.metric("Total stocks", total_stocks)
metric_two.metric("Favorites", total_favorites)
metric_three.metric("Average score", f"{average_score:.1f}")

if st.button("Refresh stocks"):
    st.rerun()

st.subheader("Add a new stock")

symbol = st.text_input("Symbol", key="stock_symbol", placeholder="AAPL")

if st.button("Auto-fill company info"):
    if not symbol.strip():
        st.error("Enter a stock symbol first.")
    else:
        try:
            company_info = lookup_company_info(symbol)
            st.session_state["company_name"] = company_info["company_name"]
            st.session_state["sector"] = company_info["sector"]
            st.success("Company name and sector were filled from the backend.")
        except requests.RequestException as error:
            show_request_error("Could not auto-fill company info.", error)

with st.form("create_stock_form"):
    company_name = st.text_input(
        "Company name", key="company_name", placeholder="Apple Inc."
    )
    sector = st.text_input("Sector", key="sector", placeholder="Technology")
    target_price = st.number_input(
        "Target price",
        min_value=0.01,
        step=1.0,
        format="%.2f",
    )
    personal_score = st.slider("Personal score", min_value=1, max_value=10, value=5)
    thesis = st.text_area(
        "Thesis",
        placeholder="Why is this stock on your watchlist?",
    )
    is_favorite = st.checkbox("Favorite")

    submitted = st.form_submit_button("Add stock")

if submitted:
    payload = {
        "symbol": st.session_state["stock_symbol"].strip().upper(),
        "company_name": company_name,
        "sector": sector,
        "target_price": target_price,
        "personal_score": personal_score,
        "thesis": thesis,
        "is_favorite": is_favorite,
    }

    try:
        create_stock(payload)
        st.session_state["stock_created"] = True
        st.rerun()
    except requests.RequestException as error:
        show_request_error("Could not add stock.", error)

st.subheader("Current watchlist")

if stocks:
    st.dataframe(stocks, use_container_width=True, hide_index=True)
else:
    st.info("No stocks yet. Add one with the form above.")
