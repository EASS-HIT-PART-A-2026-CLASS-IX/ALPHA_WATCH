# AlphaWatch

AlphaWatch is a small local app for managing a personal stock watchlist.

EX1 includes a FastAPI backend with in-memory storage, Pydantic validation, and pytest-based API tests.

EX2 adds a lightweight Streamlit interface that talks to the same FastAPI backend. The interface lets users quickly add a stock, list the current watchlist, auto-fill basic company information, and view a small summary at the top of the page.

## Create an Environment with `uv`

```bash
uv venv
```

## Install Dependencies

```bash
uv pip install -e ".[dev]"
```

## Configure Company Lookup

The backend can use Alpha Vantage to look up basic company information by stock symbol.

Create a free API key at `https://www.alphavantage.co/support/#api-key`, then set it in your terminal:

```bash
export ALPHAVANTAGE_API_KEY="your-api-key-here"
```

The Streamlit frontend does not call Alpha Vantage directly. It only calls the local FastAPI backend.

## Run the API Locally

In the first terminal, run:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Run the Streamlit Interface

In a second terminal, run:

```bash
uv run streamlit run ui/streamlit_app.py
```

The Streamlit app will open in your browser. Keep the FastAPI backend and the Streamlit interface running side-by-side in two terminals.

## Run Tests

```bash
uv run pytest
```

## Endpoints

- `GET /stocks`
- `GET /stocks/lookup/{symbol}`
- `GET /stocks/{stock_id}`
- `POST /stocks`
- `PUT /stocks/{stock_id}`
- `DELETE /stocks/{stock_id}`

## EX2 Interface

The Streamlit interface uses `requests` to call the local FastAPI backend at `http://127.0.0.1:8000`.

For company auto-fill, Streamlit calls `GET /stocks/lookup/{symbol}` on the local backend. The backend then calls Alpha Vantage and returns only the basic fields needed by the UI:

- `symbol`
- `company_name`
- `sector`

From the interface, users can:

- add a new stock with symbol, company name, sector, target price, personal score, thesis, and favorite status
- enter a ticker symbol and click `Auto-fill company info`
- list all stocks currently stored by the backend
- refresh the table after changes
- see summary metrics for total stocks, total favorites, and average personal score

The user still manually fills target price, personal score, thesis, and favorite status.

The extra EX2 feature is the summary metrics section at the top of the page. The company auto-fill is a small convenience feature that keeps the backend as the center of the system.

## AI Assistance

AI tools were used for planning, scaffolding, and extending this project for EX2. All generated outputs were reviewed and tested locally.
