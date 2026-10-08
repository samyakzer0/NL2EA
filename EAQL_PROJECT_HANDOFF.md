# EAQL Project Handoff

> **Purpose:** Drop this file into a new session so another agent can understand the project without reconstructing its history from scratch.
>
> **Scope rule:** This is documentation only. No new feature is proposed or added here. The project is recorded as it exists at the captured revision.

## 1. Snapshot

- **Project:** EAQL — Enterprise Aware RAG & Query Platform.
- **Repository:** `samyakzer0/NL2EA`
- **Remote:** `https://github.com/samyakzer0/NL2EA`
- **Captured branch:** `feature/agentic-rag`
- **Captured HEAD:** `5a1b154` — `refactor: centralize LLM generation and harden services`
- **Remote branch:** `origin/feature/agentic-rag` at the same commit.
- **Worktree at capture:** clean.
- **Tracked files:** 37.
- **Primary language:** Python.
- **Project type:** backend service/API with database and AI integrations; not a frontend or monorepo.
- **Current intended stopping point:** documentation, evaluation, demo quality, and interview preparation—not additional agents, memory, Redis, Kubernetes, vector databases, or other technology added only for resume keywords.

## 2. What the system does today

EAQL exposes one natural-language query interface:

1. A client sends a question to `POST /query`.
2. FastAPI validates the request.
3. LangGraph classifies the question as either `sql` or `rag`.
4. The SQL branch:
   - introspects the allowed PostgreSQL schema,
   - asks Gemini to generate SQL,
   - removes Markdown fences,
   - validates that the result is one `SELECT` or `WITH` statement,
   - executes it inside a read-only transaction,
   - serializes database values.
5. The RAG branch:
   - embeds the question with Gemini,
   - retrieves the top three records through LangChain PGVector,
   - asks Gemini to answer using only retrieved context.
6. Both branches pass through a final answer node that hides internal routing, SQL, RAG, and embedding details from the user.
7. FastAPI returns `{ "answer": "..." }`.

Canonical runtime path:

```text
User
  -> FastAPI POST /query
  -> LangGraph START
  -> classifier
     -> SQL -> schema introspection -> Gemini SQL -> clean -> validate -> read-only PostgreSQL
     -> RAG -> Gemini embedding -> PGVector/pgvector top-k retrieval -> LangChain Gemini answer
  -> final Gemini answer node
  -> FastAPI response
```

## 3. Public HTTP contract

### `GET /`

Implemented in [`app/main.py`](app/main.py:22).

Returns:

```json
{
  "message": "EAQL API is running"
}
```

### `POST /query`

Implemented in [`app/main.py`](app/main.py:28).

Request model:

```json
{
  "question": "What is the refund period?"
}
```

Response model:

```json
{
  "answer": "..."
}
```

Behavior:

- Empty or whitespace-only `question` returns HTTP 400 with:

  ```json
  { "detail": "Question cannot be empty." }
  ```

- Unexpected graph exceptions are logged with `print` and returned as HTTP 500 with:

  ```json
  { "detail": "Failed to process the query." }
  ```

- The internal exception text is not exposed through the HTTP response.
- Swagger/OpenAPI is available through FastAPI's normal `/docs` endpoint when the service is running.

## 4. Architecture by module

### API layer

[`app/main.py`](app/main.py:1)

- Creates the FastAPI application.
- Defines `QueryRequest` and `QueryResponse`.
- Owns `/` and `/query`.
- Performs empty-question validation and top-level error translation.
- Imports the compiled graph from [`app/graph.py`](app/graph.py:137).

### Orchestration layer

[`app/graph.py`](app/graph.py:1)

- Defines the LangGraph `State` with:
  - `message: str`
  - `result: str`
- Defines SQL and RAG nodes.
- Defines the classifier prompt and router.
- Defines the final answer prompt.
- Compiles the graph:

  ```text
  START -> router -> sql|rag -> answer -> END
  ```

- The classifier intentionally treats the word `document` alone as insufficient to force RAG:
  - `"How many documents mention shipping?"` -> SQL
  - `"Show me documents that mention refunds"` -> SQL
  - `"What is the refund period?"` -> RAG
  - `"Who is the CEO of the company?"` -> RAG

### Structured-data capability

[`agents/sql_agent.py`](agents/sql_agent.py:1)

- `run_sql(question)` is the single structured-data entry point.
- Uses `DATABASE_URL`.
- Restricts schema exposure to `allowed_tables=["documents"]`.
- Delegates schema extraction to [`database/schema.py`](database/schema.py:12).
- Delegates generation, cleaning, validation, execution, and serialization to [`database/sql.py`](database/sql.py:7).

### Unstructured-document capability

[`agents/rag_agent.py`](agents/rag_agent.py:1)

- Builds a LangChain runnable chain.
- Uses `create_retriever(k=3)`.
- Uses `ChatGoogleGenerativeAI` directly rather than the generic `services/llm.py` helper.
- Grounds the prompt in retrieved context and instructs the model to say `"I don't know"` when the context is insufficient.
- `run_rag(question)` invokes the chain and returns `response.content[0]["text"]`.

### Database schema layer

[`database/schema.py`](database/schema.py:1)

- Uses SQLAlchemy inspection at request time.
- Enumerates database tables, optionally filtering by an allow-list.
- Excludes the `embedding` column from the prompt-facing schema.
- Formats the remaining table/column/type information for SQL generation.
- Suppresses the expected SQLAlchemy warning for the PostgreSQL `vector` column.

### SQL execution and safety layer

[`database/sql.py`](database/sql.py:1)

- Generates SQL through the shared Gemini service.
- Cleans leading/trailing whitespace and Markdown code fences.
- Allows one parsed `SELECT`.
- Allows one statement beginning with `WITH` because `sqlparse` may classify a CTE as `UNKNOWN`.
- Rejects empty SQL, multiple statements, and non-`SELECT` statement types.
- Uses SQLAlchemy `text(query)`.
- Executes:

  ```sql
  SET TRANSACTION READ ONLY
  ```

  before the generated query in the same transaction.
- Serializes:
  - `date`/`datetime` -> ISO string
  - `bytes` -> UTF-8 with replacement
  - `Decimal`-named values -> `float`
- On execution errors, prints an error and returns an empty list.
- Always disposes the SQLAlchemy engine.

### Shared LLM boundary

[`services/llm.py`](services/llm.py:1)

- Loads environment variables.
- Creates one Google GenAI client at module import.
- Uses model `gemini-3.5-flash-lite`.
- `generate_content(prompt)` retries up to three attempts.
- Retry delay is exponential:
  - after first failure: 2 seconds
  - after second failure: 4 seconds
  - final failure: re-raise the exception.
- Classifier, final answer generation, and SQL generation use this boundary.
- The RAG path intentionally retains LangChain's chat-model abstraction.

### Embedding adapter

[`retrieval/embeddings.py`](retrieval/embeddings.py:1)

- Provides LangChain-compatible `GeminiEmbedding`.
- `embed_documents()` uses `gemini-embedding-001`.
- `embed_query()` uses `gemini-embedding-001`.
- Returns `embedding.values`.

### Vector store

[`retrieval/vector_store.py`](retrieval/vector_store.py:1)

- Creates a LangChain `PGVector`.
- Collection name: `nl2ea_docs_v2`.
- Connection: `DATABASE_URL`.
- Uses JSONB metadata.
- Creates a retriever with configurable `k`, currently invoked with `k=3`.

## 5. Data model and persistence

The build journal records the primary table as:

```text
documents(id, content, embedding, metadata)
```

- `embedding` is a pgvector column of dimension 3072 according to the journal.
- Gemini model `gemini-embedding-001` supplies the vectors.
- The SQL prompt hides `embedding`; the RAG/PGVector layer uses it for similarity retrieval.
- The current SQL agent allow-list exposes only `documents`.
- Direct manual vector search historically used pgvector's `<=>` distance operator.
- The current vector-store collection is `nl2ea_docs_v2`.

The journal records eight policy-style seed documents used for retrieval demonstrations:

1. Refund period: 30 days.
2. Standard shipping: 5 to 7 business days.
3. Order cancellation: within 24 hours.
4. Premium customers: free shipping.
5. Refund processing: within 5 business days after approval.
6. Customer support: 9 AM to 6 PM.
7. Password reset: account settings page.
8. International shipping: currently unavailable.

The repository does not contain a production ingestion command in the tracked application modules. [`tests/embedding_test.py`](tests/embedding_test.py:1) contains an executable/manual insertion script for embedding and inserting text into `documents`.

## 6. Configuration and runtime

### Environment variables used by live code

- `DATABASE_URL`
  - Local test configuration is documented as `localhost:5433`.
  - Docker Compose service-to-service configuration is documented as `postgres:5432`.
- `GEMINI_API_KEY`
  - Required for Gemini generation and embeddings.
- `HOST` and `PORT`
  - Present in `.env.example`, but the current Docker command explicitly binds Uvicorn to `0.0.0.0:8000`.
- `LLM_API_KEY`
  - Present in `.env.example`/historical README text but not used by the current live code.

Sensitive files:

- `.env` and `.env.local` are ignored by [` .gitignore`](.gitignore:17) and are not tracked.
- Do not copy API key values into a future handoff, commit, issue, or log.
- The captured local files contained live-looking secret material; treat those keys as sensitive and rotate them if they were exposed outside the intended local environment.

### Docker

[`Dockerfile`](Dockerfile:1)

- Base image: `python:3.11-slim`.
- Installs `requirements.txt`.
- Copies the repository into `/app`.
- Exposes port 8000.
- Starts `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

[`docker-compose.yml`](docker-compose.yml:1)

- `postgres`:
  - image `pgvector/pgvector:pg17`
  - container `nl2ea-postgres`
  - user `nl2ea`
  - database `nl2ea`
  - host port `5433` mapped to container port `5432`
  - persistent volume `nl2ea_postgres_data`
  - `pg_isready` health check
- `api`:
  - built from the repository Dockerfile
  - container `nl2ea-api`
  - host port `8000`
  - loads `.env`
  - waits for PostgreSQL `service_healthy`

The documented networking distinction is intentional:

```text
From Windows/local process: localhost:5433
From API container:         postgres:5432
```

## 7. Dependencies and stack

Declared in [`requirements.txt`](requirements.txt:1):

- FastAPI >= 0.110.0
- Uvicorn standard extras >= 0.28.0
- SQLAlchemy >= 2.0.0
- psycopg binary
- google-genai >= 0.1.1
- langchain
- langchain-core
- langchain-google-genai
- langchain-postgres
- langgraph
- pgvector
- sqlparse >= 0.4.4
- python-dotenv >= 1.0.1
- pydantic >= 2.6.0
- pytest >= 8.0.0
- httpx >= 0.27.0

Runtime versions evidenced by the repository:

- Python 3.11 in the Docker image.
- PostgreSQL/pgvector image `pgvector/pgvector:pg17`.
- Gemini generation model: `gemini-3.5-flash-lite`.
- Gemini embedding model: `gemini-embedding-001`.

No exact lockfile is tracked. Dependency resolution can therefore change between environments.

## 8. Tests and validation evidence

Tracked test/support files:

- [`tests/api_test.py`](tests/api_test.py:1)
  - SQL query API path.
  - RAG query API path.
  - Empty-question HTTP 400.
  - Simulated graph failure HTTP 500.
- [`tests/sql_validation_test.py`](tests/sql_validation_test.py:1)
  - safe `SELECT`
  - `COUNT`
  - CTE
  - `DELETE`
  - `UPDATE`
  - `INSERT`
  - `DROP`
  - stacked statements
- [`tests/sql_agent_test.py`](tests/sql_agent_test.py:1)
  - SQL agent behavior against the configured database.
- [`tests/schema_test.py`](tests/schema_test.py:1)
  - schema extraction/formatting support.
- [`tests/rag_agent_test.py`](tests/rag_agent_test.py:1)
  - RAG agent path.
- [`tests/retrieval_test.py`](tests/retrieval_test.py:1)
  - retriever path.
- [`tests/langgraph_test.py`](tests/langgraph_test.py:1)
  - graph/routing path.
- [`tests/llm_test.py`](tests/llm_test.py:1)
  - centralized LLM service.
- [`tests/embedding_test.py`](tests/embedding_test.py:1), [`tests/gemini_embedding_test.py`](tests/gemini_embedding_test.py:1), [`tests/pgvector_test.py`](tests/pgvector_test.py:1), [`tests/search_test.py`](tests/search_test.py:1), [`tests/langchain_rag.py`](tests/langchain_rag.py:1), [`tests/langchain_test.py`](tests/langchain_test.py:1)
  - exploratory/manual integration checks for embeddings, direct pgvector search, LangChain, and RAG.

The build journal records an API milestone of 4/4 passing tests and successful demonstrations of:

- SQL and RAG routing.
- Refund-period retrieval.
- Safe SELECT/COUNT/CTE behavior.
- Rejection of destructive and stacked statements.
- Read-only database enforcement.
- Docker startup.
- PostgreSQL health-gated Compose startup.
- Centralized Gemini retry behavior.

These are journal claims; a future session should rerun the relevant tests before asserting current external-service health.

## 9. Historical architectural evolution

The supplied `EAQL_Project_Build_Journal.pdf` is the historical source for this section.

1. **Original NL2SQL goal:** natural-language questions translated into relational queries.
2. **EAQL concept:** expanded to combine structured SQL answers and unstructured document answers.
3. **PostgreSQL + pgvector:** selected as one relational/vector foundation.
4. **Gemini embeddings:** integrated through the Google GenAI SDK and a LangChain adapter.
5. **Manual vector search first:** verified pgvector similarity before adding LangChain abstractions.
6. **LangChain RAG:** introduced reusable PGVector retrieval and context-grounded answers.
7. **Initial SQL engine:** FastAPI, Gemini, SQLAlchemy, runtime schema, cleanup, validation, and execution.
8. **SQL safety:** added sqlparse checks, stacked-statement rejection, SELECT/CTE handling, transaction read-only mode, and a database read-only user.
9. **Dynamic schema introspection:** moved from copied schema text to SQLAlchemy inspection, with only `documents` currently allowed.
10. **SQL agent refactor:** consolidated structured-data behavior in `agents/sql_agent.py`.
11. **LangGraph:** introduced explicit state, routing, branch nodes, and a final answer node.
12. **FastAPI:** became the stable external boundary with Pydantic request/response models and HTTP error handling.
13. **Testing milestone:** API, SQL safety, RAG, routing, and adversarial destructive-request checks.
14. **Gemini 503 incident:** model availability failures motivated resilience rather than an architectural rewrite.
15. **Dockerization:** added the Python image and Uvicorn entrypoint.
16. **Compose:** added API + pgvector/PostgreSQL, service-name networking, persistent volume, and health gating.
17. **Environment separation:** `.env` for Docker and `.env.local` for local Windows tests.
18. **Centralized LLM service:** added retry/backoff and migrated SQL generation, classification, and final-answer generation.
19. **RAG exception:** kept LangChain `ChatGoogleGenerativeAI` because the RAG chain depends on that abstraction.
20. **Deliberate stop:** documentation/evaluation/demo/interview readiness were considered higher-value than additional infrastructure or agents.

## 10. Git history and architectural change points

Relevant captured commits, newest first:

- `5a1b154` — centralize LLM generation and harden services.
- `1d0543a` — add health check and resilient LLM service.
- `635c5cf` — remove old `nl2sql` files (`main.py`, `test_edge_cases.py`, `help.txt`).
- `1405bf0` — Dockerize EAQL application.
- `894ccf8` — add API integration tests.
- `d8025a4` — expose EAQL through FastAPI.
- `bed2b57` — isolate SQL schema handling in the agent.
- `a13246c` — integrate SQL and RAG agents with LangGraph.
- `6b2cf28` — separate SQL agent and database layer.
- `e412b84` — extract RAG agent.
- `0ad03f3` — extract RAG retrieval layer.
- `15ed0c4` — extract retrieval layer and vector-store integration.
- `31a115c` — restrict SQL schema exposure.
- `cc235bf` — extract SQL utilities.
- `2b784cd` — extract database schema utilities.
- `7e1f3c9` — add database module.
- `0ddf462` — complete LangGraph RAG and SQL orchestration.
- `ee43d7a` — add SQL/RAG LangGraph nodes and unified answer flow.
- `6e6e3f8` — test LangChain/pgvector and Gemini embeddings.
- `955168e` — add raw embedding and search tests.

Branch references at capture:

- `feature/agentic-rag` and `origin/feature/agentic-rag`: `5a1b154`.
- `main` and `origin/main`: `490ccc4`.
- `backup/feature-agentic-rag-before-rebase`: `19e7a68`.

## 11. Current source-of-truth versus historical documentation

When the README, journal, and live code differ, use this precedence:

1. Current tracked source at the captured HEAD.
2. Current Docker/Compose configuration.
3. Current tests.
4. Build journal for rationale and historical sequence.
5. README for historical design context only where it matches the source.

Known README/live-code divergence:

- The README still describes an older generic NL2SQL API with fields such as `db_connection_uri`, `user_prompt`, and API-key request fields. The live API accepts only `question`.
- The README references an old `main.py`/`test_edge_cases.py` layout that was removed in `635c5cf`.
- The README describes broader multi-dialect/general-schema behavior, while the current SQL agent restricts the prompt-facing schema to the `documents` table.
- The README claims a larger historical edge-case suite that is no longer tracked under the old filename.
- The live Docker command is `uvicorn app.main:app`, not the historical `uvicorn main:app` example.
- The live generation path uses centralized `services/llm.py`; the RAG path intentionally remains on LangChain's chat model.

## 12. Known limitations and evidence gaps

These are observations of the current implementation, not feature requests:

- Classification is LLM-based and has no deterministic fallback branch if the classifier returns unexpected text.
- `services/llm.py` creates the client at import time; missing configuration may fail during import/client initialization.
- SQL validation checks the top-level statement shape, but does not constitute a full database authorization policy. The database permission and transaction read-only layers remain important.
- `execute_sql()` converts any execution failure into an empty list, which can be indistinguishable from a valid query returning no rows at the branch-result level.
- The SQL and RAG agents create/retrieve external resources during request handling.
- RAG response extraction assumes the returned LangChain content shape supports `response.content[0]["text"]`.
- No dependency lockfile is tracked.
- The repository includes manual/exploratory scripts in `tests/` that may perform external calls or database writes when run directly.
- Current source line formatting is inconsistent in places; this handoff does not change it.
- The supplied journal records a PostgreSQL read-only user, but that user/permission setup is not represented as a tracked migration or initialization script in this repository.
- The current source uses `DATABASE_URL` and `GEMINI_API_KEY`; generic `LLM_API_KEY` support is historical/documented but not wired into the live code.
- External Gemini availability, database contents, pgvector extension state, and seeded documents are environment-dependent.

## 13. Unit-style implementation map for a future session

This is a compact handoff map, not a redesign:

| Unit | External trigger | Primary source | Important contracts |
|---|---|---|---|
| `health_root` | `GET /` | `app/main.py:22` | status JSON message |
| `query_endpoint` | `POST /query` | `app/main.py:28` | request/response models; 400/500 behavior |
| `question_router` | graph start for a question | `app/graph.py:120` | classifier returns `sql` or `rag` |
| `sql_question` | routed structured question | `agents/sql_agent.py:17` | documents-only schema; safe read-only query |
| `rag_question` | routed document question | `agents/rag_agent.py:31` | top-3 PGVector retrieval; grounded answer |
| `final_answer` | after SQL/RAG branch | `app/graph.py:88` | concise answer; hide internals |

Shared modules used across units:

- `services/llm.py`: shared generation/retry boundary.
- `database/sql.py`: SQL generation/cleaning/validation/execution/serialization.
- `database/schema.py`: schema extraction/formatting.
- `retrieval/vector_store.py`: PGVector retriever.
- `retrieval/embeddings.py`: Gemini embedding adapter.

## 14. Safe instructions for the next session

If the next session is asked to work on this project:

1. Read this file first.
2. Verify the actual branch, HEAD, and worktree before changing anything.
3. Treat source code as the current behavior contract.
4. Do not add features, agents, memory, infrastructure, or dependencies unless the user explicitly asks.
5. Preserve the current API shape unless the user explicitly requests an API change.
6. Never print, copy, or commit secrets from `.env` or `.env.local`.
7. Use the build journal for rationale, not as proof that removed code still exists.
8. If changing behavior, update directly related documentation and tests only when requested or required by the change.
9. For any migration/rewrite, keep the smallest runtime boundary and do not treat every historical file as an implementation target.

## 15. Evidence files

- Current API: [`app/main.py`](app/main.py)
- Current orchestration: [`app/graph.py`](app/graph.py)
- SQL agent: [`agents/sql_agent.py`](agents/sql_agent.py)
- RAG agent: [`agents/rag_agent.py`](agents/rag_agent.py)
- SQL/database utilities: [`database/sql.py`](database/sql.py), [`database/schema.py`](database/schema.py)
- Retrieval: [`retrieval/embeddings.py`](retrieval/embeddings.py), [`retrieval/vector_store.py`](retrieval/vector_store.py)
- Shared LLM service: [`services/llm.py`](services/llm.py)
- Runtime image: [`Dockerfile`](Dockerfile)
- Local orchestration: [`docker-compose.yml`](docker-compose.yml)
- Dependencies: [`requirements.txt`](requirements.txt)
- Tests: [`tests/`](tests/)
- Historical build journal supplied by the user: `C:\Users\SAMYAKK\Downloads\EAQL_Project_Build_Journal.pdf`
- Tagged RAG source supplied by the user: [`agents/rag_agent.py`](agents/rag_agent.py)

**End of handoff.**
