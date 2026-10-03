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

Research results retain every collected record and source. The response marks exact URL or
same-feed identifier duplicates and flags high-similarity headlines published within 48 hours
as candidates for review. `duplicate_count` excludes these candidates, which are reported
separately as `similarity_candidate_count`; title candidates are not treated as confirmed
duplicate evidence.

Research responses also include query-scoped topics. Content remains stored independently and
is linked to a topic when headlines share at least three informative terms, meet the similarity
threshold and were published within 48 hours. This lets related coverage of one event reuse a
topic across searches while keeping distinct events separate. Repeated items from the same RSS
source and canonical URL reuse their content record; copies from other sources remain preserved.
Topic counts include one item per source and canonical URL, so repeated collections do not inflate
the count. Existing topic rows are matched against their linked headlines before a new topic is
created.
