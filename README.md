# AlphaWatch

AlphaWatch is a small FastAPI microservice for managing a personal stock watchlist. It uses in-memory storage, Pydantic validation, and pytest-based API tests, making it a simple local-only project for an EX1 course assignment.

## Create an Environment with `uv`

```bash
uv venv
```

## Install Dependencies

```bash
uv pip install -e ".[dev]"
```

## Run the API Locally

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Run Tests

```bash
uv run pytest
```

## Endpoints

- `GET /stocks`
- `GET /stocks/{stock_id}`
- `POST /stocks`
- `PUT /stocks/{stock_id}`
- `DELETE /stocks/{stock_id}`

## AI Assistance

AI tools were used for planning and scaffolding this project. All generated outputs were reviewed and tested locally.
