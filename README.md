# EAQL — Setup, Installation & Usage Guide

Hey! Welcome to EAQL.

EAQL is an AI-powered platform that lets you ask questions about business data and internal company documents using natural language. Instead of writing SQL queries or manually searching through documents, you can ask a question in plain English and let the system figure out how to answer it.

For example, you could ask:

- "How many active subscriptions do we have?"
- "What does our enterprise SLA promise?"
- "What was our enterprise revenue in Q3 2026, and what does our SLA promise?"

The first question requires structured database access. The second requires document retrieval. The third combines both.

This guide will walk you through setting up the project from scratch, running it locally, loading documents, and asking your first questions.

---

## 1. How EAQL works

EAQL combines three main components:

**1. SQL agent**

Handles structured business data stored in PostgreSQL. It generates SQL from natural-language questions, validates the generated query, executes it, and returns the results.

**2. RAG agent**

Handles unstructured company knowledge. It retrieves relevant document chunks from a vector store and uses Gemini to generate an answer grounded in the retrieved context.

**3. Hybrid orchestrator**

Uses LangGraph to route questions to the appropriate agent. When a question needs both database facts and document knowledge, it decomposes the question, runs both agents, and combines their results.

The underlying technologies include Python, FastAPI, LangGraph, SQLAlchemy, PostgreSQL, pgvector, and Google's Gemini models.

---

## 2. Prerequisites

Before getting started, make sure you have the following installed:

- **Python 3.11 or a compatible version** supported by the project's dependencies.
- **Git** to clone the repository.
- **Docker Desktop** to run PostgreSQL with pgvector and the API container.
- **A Gemini API key** for embeddings and LLM calls.

You'll also need an internet connection for downloading dependencies and accessing the Gemini API.

Check your installations:

```powershell
python --version
git --version
docker --version
docker compose version
```

If any command fails, install or configure the corresponding tool before continuing.

---

## 3. Clone the repository

Open PowerShell and navigate to the directory where you keep your projects.

```powershell
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

Replace the placeholders with your actual Git repository URL and repository folder name.

The examples below assume that the project root contains folders such as `agents`, `app`, `database`, `ingestion`, `retrieval`, `services`, and `tests`.

Run this command to inspect the repository:

```powershell
Get-ChildItem
```

**Important:** Run project commands from the repository root. The ingestion pipeline uses relative paths, so running it from a different directory can cause it to look for documents in the wrong location.

---

## 4. Create a Python virtual environment

A virtual environment keeps the project's Python dependencies separate from those of your other projects.

From the repository root, run:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your terminal should now show `(.venv)` at the beginning of the prompt.

If PowerShell blocks activation, you can use a Command Prompt terminal and run:

```bat
.venv\Scripts\activate.bat
```

Next, install the project's dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the repository does not contain `requirements.txt`, check its installation instructions and dependency files instead. Do not install arbitrary package versions without checking the project's existing dependencies.

---

## 5. Configure your environment variables

EAQL needs a Gemini API key and database connection details.

Create the environment files expected by the project. Keep secrets out of source control.

### A. `.env` — Docker configuration

The Docker API container needs to connect to PostgreSQL using the Compose service hostname.

```env
DATABASE_URL=postgresql+psycopg://nl2ea_readonly:<READONLY_PASSWORD>@postgres:5432/nl2ea
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

Here, `postgres` is the Docker Compose service hostname. The API container connects to PostgreSQL through the internal Docker network, not through `localhost:5433`.

### B. `.env.local` — Local Python scripts

For local ingestion and development scripts, use the host-accessible PostgreSQL port:

```env
DATABASE_URL=postgresql+psycopg://nl2ea_ingest:<INGEST_PASSWORD>@localhost:5433/nl2ea
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

Replace the password and API-key placeholders with the credentials configured for your environment.

The local development connection uses `localhost:5433`, while Docker containers communicate with PostgreSQL at `postgres:5432`.

If you configure a separate `SQL_DATABASE_URL` for the read-only SQL agent, update the SQL agent to use that variable explicitly. Do not assume that merely adding a variable changes the connection used by the code.

### C. Protect your secrets

Add the following to `.gitignore` if they are not already covered:

```gitignore
.env
.env.local
.venv/
__pycache__/
*.pyc
```

Never commit your real Gemini API key or database passwords.

---

## 6. Start PostgreSQL and the API

EAQL uses PostgreSQL with pgvector. PostgreSQL stores the structured business tables, while pgvector stores document embeddings and metadata for semantic retrieval.

Start the Docker services from the project root:

```powershell
docker compose up --build -d
```

The `--build` flag builds the API image, while `-d` starts the containers in the background.

Check their status:

```powershell
docker compose ps
```

Check the logs if a container is not running correctly:

```powershell
docker compose logs -f postgres
```

In another terminal, inspect the API logs:

```powershell
docker compose logs -f api
```

To stop the services later:

```powershell
docker compose down
```

This stops the containers but ordinarily preserves data in a named Docker volume. Do not remove the volume unless you intentionally want to delete the stored database data.

---

## 7. Understand the database setup

EAQL uses a PostgreSQL database named `nl2ea`.

The development setup has two distinct kinds of data.

### Structured business data

The fictional Zer0Labs dataset lives in the `zer0labs` schema. It contains tables for entities such as:

- Customers
- Plans
- Subscriptions
- Invoices
- Payments
- Usage
- Employees

These records are queried through the SQL agent.

### Document and vector data

The PGVector integration stores document chunks, embeddings, and metadata in tables such as:

- `langchain_pg_collection`
- `langchain_pg_embedding`

The collection currently used by the vector-store configuration is `nl2ea_docs_v2`.

These records are used by the RAG agent.

### Initialize the business schema

If the repository includes `tests/zer0labs_schema.sql`, use it to initialize the sample business schema in a fresh development database, following the project's intended initialization process.

For an already-running PostgreSQL container, the following PowerShell command can feed the SQL file into `psql`:

```powershell
Get-Content -Raw .\tests\zer0labs_schema.sql |
    docker exec -i nl2ea-postgres psql -U nl2ea -d nl2ea
```

Run this only when initialization is needed. Do not repeatedly execute a seed script against an existing database unless it is designed to be rerun safely.

The database role used by the SQL agent should have permission to read the authorized business schema and tables. The ingestion role needs the additional permissions required to write vector data.

For a real deployment, keep these roles separate. The SQL agent should not receive unnecessary write permissions on business data.

---

## 8. Add your own documents

This is where the RAG functionality becomes useful.

The ingestion pipeline reads files from the `zer0Labs` directory in the project root. The folder name must match the path configured in `ingestion/ingest.py`.

A typical directory structure looks like this:

```text
your-project/
├── agents/
├── app/
├── database/
├── ingestion/
├── retrieval/
├── services/
├── tests/
├── zer0Labs/
│   ├── company_profile.md
│   ├── financial_reports_q3_2026.md
│   ├── product_documentation.md
│   ├── security_policy.md
│   ├── enterprise_sla.md
│   ├── customer_handbook.md
│   ├── company_roadmap.md
│   └── customer_contracts.md
├── .env
├── .env.local
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

The filenames above are examples from the development dataset. You can replace or supplement them with your own supported documents.

The loader supports file formats including:

- Markdown (`.md`)
- Text (`.txt`)
- PDF (`.pdf`)
- Word documents (`.docx`)
- CSV (`.csv`)
- JSON (`.json`)

For the best results, use documents with clear headings, meaningful section boundaries, and accurate content.

**A practical tip:** Start with a small set of documents that you understand well. This makes it much easier to determine whether retrieval is returning the correct information.

### Ingest the documents

Place the files inside `zer0Labs/`, then run:

```powershell
python -m ingestion.ingest
```

The pipeline loads the files, splits their contents into chunks, generates embeddings, and stores the chunks in PostgreSQL using pgvector.

The current chunker uses a chunk size of 1,000 characters with 200 characters of overlap.

A successful run should report the number of chunks and documents ingested.

For example, the development dataset previously processed eight documents into 69 chunks. Your numbers may differ depending on the files you provide.

### What happens when you run ingestion again?

The pipeline uses stable chunk identifiers to avoid blindly creating new copies of unchanged chunks. However, changed or deleted source documents may leave stale chunks behind.

For that reason, treat ingestion as a data-management operation, not merely a command to run without considering the existing collection.

Do not drop the vector collection just to refresh a document unless you understand which data it contains.

---

## 9. Test document retrieval

Before asking the complete application a question, test whether the vector store can retrieve relevant content.

The project includes `tests/rag_agent_test.py` for testing RAG behavior. The standalone retrieval test can also be used if it exists in your checkout.

Run:

```powershell
python -m tests.rag_agent_test
```

A useful test question is:

> What was Zer0Labs' enterprise revenue in Q3 2026?

The expected answer is `$111,400`, based on the fictional financial report included with the development dataset.

The important part is not just the final number. Check whether the result references the appropriate source document.

If the answer is incorrect, investigate retrieval quality and document ingestion before changing the answer-generation prompt.

---

## 10. Ask questions through the API

Once the services are running, open the FastAPI interactive documentation:

**http://localhost:8000/docs**

This is the easiest place to interact with the application without building a frontend.

Find the `POST /query` endpoint and expand it.

1. Click **Try it out**.
2. Inspect the request-body schema displayed by FastAPI.
3. Enter a question using the exact fields shown in that schema.
4. Click **Execute**.
5. Inspect the response.

The request schema is the source of truth for the expected JSON format; do not assume the field name without checking it.

You can use the following example questions.

### SQL questions

These should be answered from structured business records:

- How many customers do we have?
- How many active subscriptions do we have?
- How many employees work in Engineering?
- What was enterprise invoiced revenue in Q3 2026?
- How many API requests occurred in September 2026?

### RAG questions

These should be answered using company documents:

- What does the enterprise SLA promise?
- What is our security policy?
- What does the customer handbook say about support?
- What is the company's product roadmap?

### Hybrid questions

These require both database results and document knowledge:

- What was our enterprise revenue in Q3 2026, and what does our enterprise SLA promise?
- How many active subscriptions do we have, and what support commitments apply to enterprise customers?
- What does our product documentation say about Zer0SQL, and how many customers do we currently have?

For hybrid questions, check that the SQL agent supplies the structured facts, the RAG agent supplies the relevant document context, and the final answer combines the two without inventing missing information.

---

## 11. Run the development tests

The repository includes test scripts for the main components.

Run them individually from the project root:

```powershell
python -m tests.sql_agent_test
```

This exercises the SQL agent.

```powershell
python -m tests.rag_agent_test
```

This exercises the RAG workflow.

```powershell
python -m tests.langgraph_test
```

This exercises the LangGraph routing and answer-generation workflow.

If an API test file is available, run it using the project's test setup. For example, if `tests/api_test.py` exists and pytest is installed:

```powershell
python -m pytest tests/api_test.py -v
```

A successful manual run is useful, but it does not replace automated tests covering normal behavior, invalid questions, missing information, and agent failures.

---

## 12. Troubleshooting

### PostgreSQL connection fails

Check whether the containers are running:

```powershell
docker compose ps
```

Remember the connection distinction:

- Python running on your computer: `localhost:5433`
- API running inside Docker: `postgres:5432`

Using the wrong hostname for the execution environment will cause connection failures.

### Permission denied for a schema or table

Check which database user the failing component actually uses.

For example, the ingestion process and the SQL agent may load different environment variables. Grant only the permissions required by the relevant role.

A successful ingestion run does not automatically prove that the SQL agent has the correct schema permissions.

### No relevant document is retrieved

Check that:

- The document is inside the configured `zer0Labs/` directory.
- The file is not empty.
- Ingestion completed successfully.
- The retriever uses the expected collection.
- The question is relevant to the content actually present in the document.

Reingesting files is not guaranteed to remove outdated chunks.

### The answer contains incorrect or unsupported facts

Inspect the individual agent results before inspecting the final synthesized answer.

A plausible-looking answer is not proof that the sources support it. Check the generated SQL, returned rows, retrieved document snippets, and source metadata.

### Gemini warnings appear

Warnings about model sampling defaults or automatic function calling may appear during execution. These warnings are distinct from database permission errors. Investigate an actual failed request separately rather than treating every warning as a fatal error.

---

## 13. What is implemented, and what should be improved?

EAQL currently demonstrates the core combination of natural-language SQL, document retrieval, and hybrid orchestration.

It is still important to distinguish a working development prototype from a production-ready enterprise system.

Before deploying it for real users, improve and validate:

- Database role separation and least-privilege access.
- SQL validation against malicious or unsafe generated queries.
- Graceful handling of SQL, retrieval, and LLM failures.
- Automated tests for SQL-only, RAG-only, and hybrid questions.
- Source attribution and protection against unsupported answers.
- Authentication, authorization, rate limiting, and secret management.
- Document updates, deletion, and stale-chunk cleanup.
- Deployment configuration, logging, and operational monitoring.

The project is designed to be extended. You do not need to implement every enterprise feature before you can demonstrate the core functionality, but you should be clear about what has and has not been tested.

---

## 14. Quick-start checklist

When returning to the project after cloning or setting it up on another machine, follow this sequence:

1. Install Python, Git, and Docker Desktop.
2. Clone the repository and enter the project root.
3. Create and activate the virtual environment.
4. Install the project dependencies.
5. Configure `.env` and `.env.local` with the appropriate credentials and database URLs.
6. Start the Docker services using `docker compose up --build -d`.
7. Initialize the sample business schema if the database is fresh.
8. Place documents inside `zer0Labs/`.
9. Run `python -m ingestion.ingest`.
10. Run the SQL, RAG, and LangGraph test scripts.
11. Open `http://localhost:8000/docs`.
12. Use the `POST /query` endpoint to ask questions in natural language.

If something fails, inspect the logs and identify which component failed before changing unrelated parts of the project.

---

## Final note

EAQL is built around a simple idea: business users should be able to ask questions about both their data and their documentation without needing to know SQL or manually search through every document.

The database provides structured facts. The document retriever provides contextual knowledge. The orchestrator decides how to use them together.

Start with the development dataset, verify each component, then experiment with your own documents and questions. Once the basic workflow is reliable, you can extend the system with better evaluations, access controls, document lifecycle management, and a user-facing interface.

Happy building!