# Self-Healing Data Pipeline with Anomaly Detection

## Overview
A production-style ETL pipeline that doesn't just move data — it watches its own
data quality, quarantines bad records automatically, and alerts when something
looks wrong. Built to demonstrate data observability and reliability engineering
skills on top of a standard Bronze/Silver/Gold pipeline.

## Why this project
Most portfolio pipelines only prove you can move data from A to B. This one
proves you think about failure modes, data quality, and production reliability —
the difference between "I can build a pipeline" and "I can be trusted to run one."

## Architecture

```
Data Source (synthetic or public API)
        │
        ▼
   Bronze Layer (raw ingestion)
        │
        ▼
   Silver Layer (cleansing, schema enforcement)
        │
        ▼
  ┌─────────────────┐
  │ Anomaly Checks   │──── fail ────► Quarantine Table ──► Slack/Email Alert
  │ (schema, volume, │
  │ nulls, outliers) │
  └─────────────────┘
        │ pass
        ▼
   Gold Layer (clean, analytics-ready)
        │
        ▼
   Power BI / Qlik Dashboard
```

## Tech Stack
- **Orchestration:** Apache Airflow (Docker)
- **Storage:** PostgreSQL / Azure Synapse / BigQuery
- **Anomaly detection:** Python (schema diff, rolling volume check, null-rate
  threshold, z-score/IQR outlier detection)
- **Alerting:** Slack webhook or SMTP email
- **Visualization:** Power BI or Qlik
- **Version control:** Git / GitHub (commit incrementally!)

## Anomaly Checks Implemented
| Check | What it catches |
|---|---|
| Schema drift | Missing or unexpected columns |
| Volume anomaly | Row count spikes/drops vs. rolling average |
| Null-rate threshold | Sudden increase in missing values |
| Statistical outlier | z-score or IQR breach on key numeric fields |

## Status
See `TASKS.md` for the week-by-week build plan and progress tracking.

## Demo
_(Add a link to your demo video/GIF here once complete)_

## What I'd do differently at scale
_(Fill this in at the end — interviewers love this section. e.g. "Add
Great Expectations instead of hand-rolled checks," "Use dbt for the Silver
transforms," etc.)_
