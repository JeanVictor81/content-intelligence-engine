# Content Intelligence Engine

## Local backend

1. If the root `.env` does not exist, copy `.env.example` to `.env` and set local PostgreSQL
   credentials. If it already exists, keep its local credentials and edit it in place.
2. Add one or more authorized RSS/Atom feeds to `RSS_FEEDS` in `.env` as a JSON array, for example:
   `RSS_FEEDS='[{"name":"Example Feed","url":"https://news.example/feed.xml"}]'`
3. Start PostgreSQL with `docker compose up -d db` from the repository root.
4. From `backend/`, run `uv sync`, `uv run alembic upgrade head`, then
   `uv run uvicorn app.main:app --reload`.
5. Send `POST /research` with JSON `{"query":"CBLOL"}`. The endpoint searches only the
   feeds configured in `RSS_FEEDS`, stores normalized results and returns their source metadata.

The example feed URL is illustrative. Replace it with a feed you are authorized to access.
`GET /health` checks whether the API process is responsive.
