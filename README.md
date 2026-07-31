# Prod Report — Weekly Support Team Productivity & Quality Pipeline

An Apache Airflow (Astronomer) ELT pipeline that automates the weekly productivity and quality report for a 1st-level technical support team. It pulls raw exports from S3, cleans and transforms them, and loads the result into Snowflake so the report can be generated with a query instead of a spreadsheet.

> **Note on data:** This repo uses **mock/synthetic data only**. The problem it solves is a real one from my day-to-day work as a Team Lead, but no real customer, agent, or company data is included, to avoid breaching any privacy policy.

## Background

Every Monday, as a Team Lead, I put together a productivity and quality report covering:

- **Chats and calls** — exported from the systems the team uses
- **Backlog tickets (to-dos)** and **emails handled** — pulled from the daily reports each agent submits
- **Quality scores** — received from an L2 agent's quality review

Doing this by hand every week was slow and error-prone, so this project automates the ingestion, cleaning, and consolidation of that data into a single, query-ready source of truth in Snowflake.

## What the pipeline does

1. **Extract** — raw files (chat exports, call exports, agent daily reports, quality reports) land in an S3 bucket.
2. **Transform** — Airflow DAGs clean, standardize, and reshape the data (deduplication, type casting, joining agent-level metrics, calculating productivity/quality KPIs).
3. **Load** — the cleaned data is loaded into Snowflake tables, ready to be queried or plugged into a BI tool / report template.

## Tech stack

- **Apache Airflow** (via the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview)) for orchestration
- **Python** for extraction and transformation logic
- **Amazon S3** as the data source
- **Snowflake** as the data warehouse
- **Docker** for local development, via the Astro Runtime image
- **SQL** for in-warehouse transformations

## Project structure

```
.
├── dags/            # Airflow DAG definitions (the pipeline itself)
├── include/          # Helper modules, SQL templates, and other supporting files used by the DAGs
├── sql/               # SQL scripts (transformations / Snowflake table definitions)
├── tests/dags/         # DAG-level tests
├── Dockerfile         # Astro Runtime image used to run Airflow locally
├── packages.txt        # OS-level packages required by the project
├── requirements.txt    # Python dependencies
└── .astro/             # Astro CLI project configuration
```

## Prerequisites

- [Docker](https://www.docker.com/) (Desktop or Engine)
- [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli)
- AWS credentials with read access to the source S3 bucket (Airflow connection)
- Snowflake credentials with write access to the target database/schema (Airflow connection)

## Getting started

1. Clone the repo:
   ```bash
   git clone https://github.com/Enarb1/prod_report.git
   cd prod_report
   ```

2. Start Airflow locally with the Astro CLI:
   ```bash
   astro dev start
   ```
   This spins up the local Airflow stack (Postgres metadata DB, Scheduler, DAG Processor, API/Webserver, Triggerer).

3. Open the Airflow UI at [http://localhost:8080](http://localhost:8080).

4. Add the required connections in the Airflow UI (**Admin → Connections**):
   - `aws_default` (or your chosen conn ID) — AWS credentials for the S3 source bucket
   - `snowflake_default` (or your chosen conn ID) — Snowflake account, warehouse, database, and schema

5. Trigger the DAG(s) in the `dags/` folder from the UI, or let them run on their configured schedule.

6. Stop the local environment when done:
   ```bash
   astro dev stop
   ```

## Running tests

```bash
astro dev pytest
```
or, from inside the Airflow container:
```bash
pytest tests/dags
```

## Roadmap / ideas

- Add data quality checks (e.g. Great Expectations / Airflow data quality operators) before the Snowflake load
- Parameterize the KPI calculations so thresholds can be adjusted per team
- Add a dashboard layer (e.g. Streamlit or a BI tool) on top of the Snowflake tables for the final report view

## License

No license specified — all rights reserved by the author unless stated otherwise.
