# EAQL SQL Query Interactive IDE Plan

## 1. Product concept

Transform EAQL into a focused, AI-assisted SQL workspace inspired by the Antigravity-style layout shown in the reference screenshot.

The application will contain only the essential surfaces:

```text
┌──────────────────────────────────────────────────────────────┐
│ EAQL                         PostgreSQL       Connected  Run  │
├───────────────────────────────────────────┬──────────────────┤
│                                           │                  │
│              SQL Editor                   │    AI Agent      │
│                                           │                  │
│  SELECT                                    │  Ask natural-   │
│      ...                                   │  language        │
│  FROM documents;                           │  questions here  │
│                                           │                  │
├───────────────────────────────────────────┴──────────────────┤
│ Results / Messages / Query Status                             │
└──────────────────────────────────────────────────────────────┘
```

The product should feel like a developer tool for exploring data, not a generic dashboard or chat application.

## 2. Design goals

### Primary goals

1. Let users ask questions in natural language.
2. Generate SQL directly into the main editor.
3. Allow users to inspect and edit generated SQL.
4. Execute SQL from the editor.
5. Display results in a structured table.
6. Let the AI agent explain, improve, and troubleshoot queries.
7. Preserve EAQL's read-only SQL safety model.

### Visual goals

- Dark-first developer-tool interface.
- No Explorer panel.
- No Search, Source Control, or Extensions sidebar.
- No unnecessary navigation.
- Main editor and AI panel dominate the screen.
- Results appear in a resizable bottom panel.
- Compact controls and low visual noise.

## 3. Proposed application layout

### Top application bar

The top bar should contain only essential information and actions:

- EAQL logo or name.
- Current workspace or database name.
- Connection status.
- Database type, initially PostgreSQL.
- Run query button.
- Stop/cancel button while a query is running.
- Settings button.
- Optional theme toggle.

Example:

```text
EAQL     PostgreSQL / Documents DB     Connected        Run Query
```

### Main SQL editor

The central editor is where generated and manually written SQL is displayed.

Required capabilities:

- SQL syntax highlighting.
- Line numbers.
- Direct editing.
- Formatting.
- Copy action.
- Clear/reset action.
- Keyboard execution shortcuts.
- Inline validation errors.
- Unsafe-query highlighting.

Example:

```sql
SELECT
    category,
    COUNT(*) AS document_count
FROM documents
GROUP BY category
ORDER BY document_count DESC;
```

Initial editor actions:

- Run.
- Format.
- Explain.
- Copy.
- Save query.
- Clear.
- Undo/redo.
- Query history.

### Right-side AI agent panel

The agent panel is where users write natural-language questions.

Example questions:

```text
How many documents were uploaded last month?
```

```text
Show me the top five document categories.
```

```text
Why did this query return no results?
```

```text
Rewrite this query to group the results by month.
```

When the user asks a data question, the agent should:

1. Understand the question.
2. Inspect the available schema.
3. Generate SQL.
4. Write the SQL into the main editor.
5. Explain the generated query.
6. Ask for confirmation before execution when appropriate.
7. Display execution results after the user runs the query.

The agent must not only return SQL inside a chat message. Its primary value is writing editable SQL into the editor.

### Bottom results panel

The bottom panel displays the result of the executed query.

Successful query state:

- Result table.
- Row count.
- Query execution duration.
- Columns and data types.
- Export button.
- Copy results button.

Empty-result state:

```text
Query executed successfully but returned no rows.
```

Validation-error state:

```text
This query was blocked because only read-only SELECT and WITH statements are allowed.
```

Database-error state:

```text
The query could not be executed.

Reason:
relation "document" does not exist
```

The result panel should be collapsible and resizable.

## 4. Core user workflows

### Workflow 1: Ask a natural-language question

```text
User types a question in the Agent panel
        ↓
EAQL analyzes the database schema
        ↓
EAQL generates SQL
        ↓
SQL appears in the editor
        ↓
Agent explains the query
        ↓
User reviews or edits SQL
        ↓
User clicks Run
        ↓
Results appear below the editor
```

### Workflow 2: Write SQL manually

```text
User writes SQL in the editor
        ↓
User clicks Run
        ↓
EAQL validates the query
        ↓
Read-only transaction executes
        ↓
Results appear in the bottom panel
```

### Workflow 3: Improve an existing query

```text
User keeps SQL in the editor
        ↓
User asks the agent to improve or rewrite it
        ↓
Agent reads the current editor content
        ↓
Agent proposes a modified query
        ↓
User accepts or rejects the change
        ↓
Accepted SQL replaces the editor content
```

The agent should not silently overwrite the query. It should show a diff or request approval before applying changes.

### Workflow 4: Explain a query

The agent should explain:

- Tables used.
- Joins.
- Filters.
- Grouping.
- Ordering.
- Expected output.
- Potential limitations.

## 5. AI panel interaction model

The panel should support more than a standard chat transcript.

### Response types

#### SQL generation response

Contains:

- Short explanation.
- Generated SQL.
- Insert into editor action.
- Replace current query action.
- Run query action.

#### Query explanation response

Contains:

- Tables used.
- Filters applied.
- Expected output.
- Potential limitations.

#### Error response

Contains:

- What failed.
- Why it failed.
- Corrected SQL suggestion.
- Apply fix action.

### Recommended response actions

- Insert into editor.
- Replace current query.
- Explain query.
- Run query.
- Copy SQL.
- Show query diff.
- Retry.

## 6. Backend integration plan

The existing EAQL backend should be extended rather than rebuilt.

Existing capabilities to preserve:

- FastAPI API layer.
- LangGraph orchestration.
- PostgreSQL schema introspection.
- Gemini SQL generation.
- SQL cleanup.
- SQL validation.
- Read-only query execution.
- Database value serialization.
- RAG behavior for document-oriented questions.

The current `/query` endpoint can remain for compatibility while IDE-specific endpoints are added.

### Natural-language query response

```json
{
  "intent": "sql",
  "question": "Show the latest documents",
  "sql": "SELECT ...",
  "explanation": "This query returns the latest documents...",
  "is_safe": true,
  "requires_confirmation": false
}
```

### SQL execution response

```json
{
  "sql": "SELECT ...",
  "columns": ["id", "title", "created_at"],
  "rows": [
    {
      "id": 1,
      "title": "Example document",
      "created_at": "2026-10-08"
    }
  ],
  "row_count": 1,
  "duration_ms": 84
}
```

### SQL validation response

```json
{
  "is_valid": false,
  "is_safe": false,
  "errors": [
    "Only SELECT and WITH statements are allowed."
  ]
}
```

## 7. Suggested API surface

### `POST /api/agent/query`

Generates SQL from a natural-language question.

```json
{
  "question": "How many documents were uploaded last month?"
}
```

### `POST /api/sql/validate`

Validates SQL without executing it.

```json
{
  "sql": "SELECT COUNT(*) FROM documents;"
}
```

### `POST /api/sql/execute`

Executes a validated read-only query.

```json
{
  "sql": "SELECT COUNT(*) FROM documents;"
}
```

### `POST /api/sql/explain`

Explains the current SQL query.

```json
{
  "sql": "SELECT COUNT(*) FROM documents;"
}
```

## 8. Frontend structure

Suggested component structure:

```text
frontend/
├── App
├── WorkspaceShell
├── TopBar
├── SqlEditor
├── EditorToolbar
├── AgentPanel
├── AgentMessage
├── QueryActions
├── ResultsPanel
├── ResultsTable
├── QueryStatusBar
├── QueryHistory
└── SettingsPanel
```

Initial application state:

```text
currentSql
agentMessages
isGenerating
isExecuting
queryResult
validationErrors
connectionStatus
selectedDatabase
queryHistory
```

The first version should use a simple state model rather than introducing a complex frontend architecture.

## 9. Visual design direction

### Overall style

- Dark-first.
- Developer-tool aesthetic.
- Low visual noise.
- High-contrast syntax colors.
- Subtle borders instead of heavy cards.
- Compact controls.
- Monospace SQL editor.
- Clear separation between editor, agent, and results.

### Suggested proportions

Desktop:

```text
Main editor: 65–70%
Agent panel: 30–35%
```

Bottom results panel:

```text
Initial height: 30–40%
Resizable by the user
```

### Suggested color roles

- Background: deep charcoal.
- Editor background: slightly lighter charcoal.
- Panel background: dark neutral.
- Border: muted gray.
- Primary action: blue or indigo.
- Success: green.
- Warning: amber.
- Error: red.
- SQL keywords: purple or blue.
- SQL strings: green.
- SQL numbers: orange.
- Comments: muted gray.

Avoid excessive gradients, oversized cards, or decorative dashboard elements.

## 10. Safety and trust requirements

The application executes AI-generated SQL, so safety must be visible and enforced.

Required safeguards:

1. Allow read-only SQL by default.
2. Permit only one `SELECT` or `WITH` statement.
3. Reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and `TRUNCATE`.
4. Reject multiple SQL statements.
5. Execute queries in a read-only transaction.
6. Apply a query timeout.
7. Limit returned rows.
8. Clearly indicate when a query was generated by AI.
9. Display validation errors before execution.
10. Require explicit user action to run generated SQL.

Users must always be able to inspect the SQL before it executes.

## 11. Query history and saved queries

These features should follow the core workflow.

### Query history

Store:

- Natural-language question.
- Generated SQL.
- Timestamp.
- Execution status.
- Row count.
- Duration.

### Saved queries

Allow users to save:

- Query name.
- Description.
- SQL.
- Optional tags.

For the first release, history may be local to the browser or session. Persistent storage can be added later.

## 12. Implementation phases

### Phase 0: Product and interaction definition

- Confirm the application layout.
- Confirm whether the UI is browser-based or desktop-style.
- Define the initial database connection model.
- Define the first supported use case.
- Decide whether RAG remains visible in the first UI version.

Deliverables:

- Approved layout.
- Component inventory.
- API contract.
- Visual design direction.

### Phase 1: Application shell

Build the visual workspace with mock data:

- Top bar.
- Main editor area.
- Right agent panel.
- Bottom results panel.
- Resizable layout.
- Dark theme.
- Empty, loading, and error states.

### Phase 2: SQL editor

Add:

- SQL syntax highlighting.
- Line numbers.
- Run button.
- Format button.
- Copy button.
- Clear button.
- Query status.
- Validation messages.

### Phase 3: Agent integration

Connect the agent panel to the backend:

- Send natural-language questions.
- Receive generated SQL.
- Insert SQL into the editor.
- Display explanations.
- Show loading states.
- Show backend errors.
- Add apply/reject behavior.

### Phase 4: SQL execution

Connect the editor to SQL execution:

- Validate the query.
- Execute read-only SQL.
- Display the result table.
- Display row count and execution time.
- Handle empty results.
- Handle database errors.
- Add timeout or cancellation handling.

### Phase 5: Agent-assisted query editing

Add:

- Explain query.
- Improve query.
- Fix query.
- Rewrite query.
- Query diff.
- Apply generated changes.
- Ask questions about current SQL.

### Phase 6: History and polish

Add:

- Query history.
- Saved queries.
- Keyboard shortcuts.
- Resizable panels.
- Connection indicator.
- Export results.
- Loading animations.
- Empty-state onboarding.
- Accessibility improvements.

## 13. Recommended MVP scope

The first working version should contain only:

1. A dark IDE-style layout.
2. A central SQL editor.
3. A right-side natural-language agent panel.
4. A Run button.
5. A backend endpoint that generates SQL.
6. A backend endpoint that validates and executes SQL.
7. A results table.
8. Clear safety and error messages.
9. No Explorer sidebar.
10. No Git panel.
11. No Extensions panel.
12. No complex workspace management.

## 14. Features excluded from the first version

Do not initially add:

- Multiple agent hierarchies.
- Redis.
- Celery.
- Kubernetes.
- Additional vector-database infrastructure.
- Complex plugin systems.
- Full database administration.
- Table creation or data mutation.
- Multi-user collaboration.
- Advanced dashboards.
- Full VS Code extension compatibility.
- Large workspace navigation.

The goal is not to recreate VS Code. The goal is to create a focused AI SQL workspace.

## 15. Success criteria

The MVP is successful when a user can:

1. Open the application.
2. See the SQL editor and agent panel immediately.
3. Ask:

   ```text
   How many documents are in the database?
   ```

4. See generated SQL appear in the editor.
5. Review or edit the query.
6. Click Run.
7. See the results in a table.
8. Ask the agent to explain or modify the query.
9. Receive clear errors when the query is invalid or unsafe.
10. Complete the workflow without an Explorer or navigation sidebar.

## 16. Recommended direction

Build EAQL as:

> **An AI-assisted, read-only SQL IDE where natural-language questions generate editable SQL in a central code editor and results appear below it.**

The recommended starting point is a browser-based workspace connected to the existing FastAPI backend. This provides the fastest path to an MVP and the easiest way to demonstrate the concept.
