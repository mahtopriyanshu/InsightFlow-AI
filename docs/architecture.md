# Planned System Architecture

## Purpose

InsightFlow AI is planned as an end-to-end analytics platform that turns untouched marketplace CSV files into governed data, business dashboards, an interactive application, natural-language assistance, and shareable reports.

The architecture is a future-state plan. At the current milestone, the raw Olist data has been inventoried and limited EDA has begun; ETL, PostgreSQL, Power BI, Streamlit, the AI chatbot, and automated PDF reporting have not yet been implemented.

## Future pipeline

```text
Raw CSV → ETL → PostgreSQL → Power BI → Streamlit → AI Chatbot → PDF Reports
```

```mermaid
flowchart LR
    A["Raw CSV"] --> B["ETL"]
    B --> C["PostgreSQL"]
    C --> D["Power BI"]
    C --> E["Streamlit"]
    D --> E
    E --> F["AI Chatbot"]
    F --> G["PDF Reports"]
```

The linear arrow expresses the planned user journey, while the diagram shows that both Power BI and Streamlit consume governed PostgreSQL data. Streamlit can present selected dashboard insights and provide the interface through which users reach the chatbot and report features.

## Component responsibilities

### 1. Raw CSV

Location: `data/raw/olist/`

Responsibilities:

- Preserve the nine original Olist CSV files exactly as acquired.
- Provide an auditable source for all later processing.
- Remain read-only during analysis and pipeline runs.

Rules:

- Never clean or overwrite source files.
- Record source, license, file inventory, and integrity information.
- Write transformed outputs elsewhere.

### 2. ETL

Planned location: `etl/`

Responsibilities:

- **Extract** raw CSV records using explicit schemas.
- **Transform** approved types, values, keys, and quality rules.
- **Load** validated records into PostgreSQL.
- Log row counts, rejected records, and pipeline results.
- Support repeatable and testable reloads.

Potential transformations include timestamp parsing, type validation, controlled category handling, and creation of a ZIP-prefix geography dimension. These decisions must be documented before implementation.

### 3. PostgreSQL

Planned supporting locations: `database/` and `sql/`

Responsibilities:

- Store governed relational tables with enforced keys and constraints.
- Separate staging data from analytics-ready models.
- Provide reusable SQL views for business metrics.
- Act as the consistent data source for Power BI, Streamlit, and chatbot queries.

Likely model areas:

- Orders and order lifecycle
- Order items and commercial measures
- Customers and repeat-buyer identity
- Products and translated categories
- Sellers
- Payments
- Reviews
- Controlled geography

### 4. Power BI

Planned location: `dashboard/`

Responsibilities:

- Deliver interactive management dashboards.
- Present sales, order status, delivery, customer, seller, product, payment, and review KPIs.
- Use curated PostgreSQL views rather than raw CSV joins.
- Apply documented measure definitions and filters.

Power BI is the primary business-intelligence presentation layer. It should not become the only place where business logic exists; reusable logic belongs in governed SQL or clearly documented measures.

### 5. Streamlit

Planned location: `streamlit_app/`

Responsibilities:

- Provide a browser-based project interface.
- Present selected metrics and explanations for users who do not use Power BI.
- Offer controlled filters and drill-downs.
- Host the future natural-language chatbot experience.
- Trigger approved report-generation workflows.

### 6. AI Chatbot

Planned location: `chatbot/`

Responsibilities:

- Translate user questions into safe, approved analytical requests.
- Query curated PostgreSQL views or a governed semantic layer.
- Explain results in clear business language.
- Preserve metric definitions and cite the data context used.
- Refuse unsupported conclusions when data is unavailable.

Safety and governance principles:

- Use read-only database credentials.
- Allow-list accessible schemas, views, and query patterns.
- Limit query cost and result size.
- Never expose secrets or raw personal identifiers.
- Show assumptions and distinguish retrieved facts from model-generated explanation.

### 7. PDF Reports

Planned location: `reports/`

Responsibilities:

- Produce consistent, shareable snapshots of approved metrics and commentary.
- Include report date, filters, metric definitions, and data-refresh information.
- Combine selected charts, tables, and chatbot-assisted narrative only after validation.

## Supporting concerns

### Configuration and secrets

- Store non-secret configuration in `config/`.
- Keep credentials in environment variables loaded from an uncommitted `.env` file.
- Use separate credentials for development and deployment.

### Testing

Planned location: `tests/`

- Test schema assumptions and key uniqueness.
- Test foreign-key and row-count expectations.
- Test ETL transformations and SQL metric definitions.
- Test chatbot query restrictions and report generation.

### Observability

- Record pipeline start/end time, source file identity, rows read, rows loaded, and failures.
- Expose the last successful refresh time to dashboards and reports.
- Preserve errors without silently dropping records.

### Deployment and automation

Planned location: `.github/workflows/`

- Run tests and validation checks on proposed changes.
- Build deployable application artifacts when implementation begins.
- Keep production deployment gated behind review and environment-specific secrets.

## Data flow summary

1. Untouched Olist CSV files remain the source of record in `data/raw/olist/`.
2. ETL validates and transforms copies of source records according to documented rules.
3. PostgreSQL enforces the relational model and exposes curated analytical views.
4. Power BI consumes those views for governed dashboards.
5. Streamlit provides a unified web interface and selected analytics.
6. The AI chatbot answers natural-language questions through restricted, read-only access to curated data.
7. Approved metrics and narratives are exported as traceable PDF reports.

This separation keeps raw evidence immutable, business logic reusable, user interfaces consistent, and AI-generated explanations grounded in governed data.
