# Setup & Build Guide

A step-by-step walkthrough for building the self-healing data pipeline from
zero. Work through this in order — each phase leaves you with something that
runs before you add the next layer.

---

## Phase 0 — Prerequisites

Install these before you start:

| Tool | Why | Check it works |
|---|---|---|
| Git | Version control | `git --version` |
| Docker Desktop | Runs Airflow locally | `docker --version` |
| Docker Compose | Multi-container orchestration | `docker compose version` |
| Python 3.10+ | Anomaly-check logic | `python3 --version` |
| VS Code (or any editor) | Development | — |

Accounts you'll want:
- **GitHub** — you already have this (`zmohamm3`)
- **Slack workspace** — free personal workspace is fine, just for the alert webhook
- **Power BI Desktop** (free) or **Qlik Sense Desktop** — for the final dashboard

> Note: you can build this entirely locally with Docker + PostgreSQL. No cloud
> spend required. Move to Azure/GCP later only if you want the cloud story on
> your resume.

---

## Phase 1 — Repo and project scaffolding

### 1.1 Create the GitHub repo
1. Go to https://github.com/new
2. Name: `self-healing-data-pipeline`
3. Visibility: **Public**
4. Check "Add a README file"
5. Click **Create repository**

### 1.2 Clone and set up structure
```bash
git clone https://github.com/zmohamm3/self-healing-data-pipeline.git
cd self-healing-data-pipeline

mkdir -p dags checks tests data docs config
touch dags/.gitkeep checks/.gitkeep tests/.gitkeep docs/.gitkeep
```

Final structure you're aiming for:
```
self-healing-data-pipeline/
├── dags/                  # Airflow DAG definitions
├── checks/                # Reusable anomaly detection module
│   ├── __init__.py
│   ├── schema_check.py
│   ├── volume_check.py
│   ├── null_check.py
│   └── outlier_check.py
├── tests/                 # Unit tests for each check
├── config/                # Thresholds, connection settings
├── data/                  # Synthetic data generator + local files
├── docs/                  # Architecture diagram, screenshots
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
└── TASKS.md
```

### 1.3 Add `.gitignore`
Create a `.gitignore` file with:
```
__pycache__/
*.py[cod]
.env
venv/
.venv/
logs/
airflow.db
airflow-webserver.pid
data/*.csv
!data/.gitkeep
.DS_Store
.idea/
.vscode/
```

### 1.4 First commit
```bash
git add .
git commit -m "Initial project scaffolding"
git push origin main
```

---

## Phase 2 — Local environment (Airflow via Docker)

### 2.1 Get the official Airflow compose file
```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

### 2.2 Prepare the environment
```bash
mkdir -p ./logs ./plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### 2.3 Initialize and start
```bash
docker compose up airflow-init
docker compose up -d
```

Visit http://localhost:8080 — default login is `airflow` / `airflow`.

### 2.4 Confirm Postgres is reachable
The Airflow compose file already spins up PostgreSQL. You'll use a **separate
database** on that instance for your pipeline data (don't mix it with Airflow's
metadata DB):

```bash
docker compose exec postgres psql -U airflow -c "CREATE DATABASE pipeline_db;"
```

**Commit checkpoint:** `"Add Docker Compose environment for Airflow"`

---

## Phase 3 — Data source (synthetic generator)

Building your own generator is the recommended path — it lets you inject
anomalies on demand, which is essential for demoing the whole point of this
project.

### 3.1 Write the generator
Create `data/generate_data.py`. It should produce a daily batch of records with
realistic fields, for example a retail orders dataset:

| Column | Type | Notes |
|---|---|---|
| `order_id` | string | unique |
| `customer_id` | string | repeats across rows |
| `order_date` | date | the batch date |
| `product_category` | string | from a fixed list |
| `quantity` | int | normally 1–10 |
| `unit_price` | float | normally distributed around a mean |
| `total_amount` | float | `quantity * unit_price` |
| `region` | string | from a fixed list |

Key requirement: add a `--inject-anomaly` flag that can deliberately corrupt a
batch in one of these ways:
- `schema` — drop a column or add an unexpected one
- `volume` — emit 10x or 0.1x the normal row count
- `nulls` — null out 40% of a required field
- `outlier` — insert records with `unit_price` 50x the normal mean

### 3.2 Generate a baseline history
Run the generator for ~30 days of clean data first. Your volume and outlier
checks need historical baselines to compare against — without this, the rolling
average has nothing to work with.

```bash
python data/generate_data.py --start 2026-08-01 --days 30 --output data/
```

**Commit checkpoint:** `"Add synthetic data generator with anomaly injection"`

---

## Phase 4 — Happy-path pipeline (Bronze → Silver → Gold)

Build this **without any checks first**. Get data flowing end to end, then add
the observability layer on top.

### 4.1 Create the tables
In `pipeline_db`, create three schemas: `bronze`, `silver`, `gold`.

- **Bronze** — raw landing table, all columns as `TEXT`, plus `ingested_at`
  timestamp and `source_file` for lineage. Never transform here.
- **Silver** — typed and cleansed: proper data types, trimmed strings,
  deduplicated on `order_id`, invalid rows excluded.
- **Gold** — aggregated and analytics-ready: e.g. daily revenue by region and
  category, partitioned/indexed on date.

### 4.2 Write the DAG
Create `dags/pipeline_dag.py` with these tasks in sequence:

1. `ingest_raw` — read the day's file, load into `bronze.orders_raw`
2. `transform_silver` — cast types, dedupe, load into `silver.orders`
3. `aggregate_gold` — build the daily aggregate into `gold.daily_revenue`

Schedule it `@daily`. Use Airflow's `PostgresHook` for DB connections rather
than hardcoding credentials.

### 4.3 Verify
Trigger the DAG manually in the UI. Confirm rows land in all three layers and
counts make sense.

**Commit checkpoint:** `"Working Bronze → Silver → Gold pipeline"`

---

## Phase 5 — Anomaly detection layer

This is the differentiating part of the project. Build the checks as a
standalone, importable module — not inline in the DAG. That separation is
exactly what makes it look like production code.

### 5.1 Design the interface
Every check should return the same shape so the DAG can treat them uniformly:

```python
{
    "check_name": "volume_anomaly",
    "passed": False,
    "severity": "high",
    "message": "Row count 45,200 is 8.3x the 30-day rolling average of 5,400",
    "failed_records": [],        # empty for batch-level checks
    "metadata": {"observed": 45200, "expected": 5400, "ratio": 8.3}
}
```

### 5.2 Implement the four checks

**`checks/schema_check.py`**
Compare the incoming batch's columns against an expected schema defined in
`config/schema.yml`. Flag missing required columns, unexpected new columns, and
type mismatches. Severity: `critical` for missing required columns.

**`checks/volume_check.py`**
Query the historical daily row counts from Silver, compute a rolling mean and
standard deviation over the trailing 30 days, and flag the batch if it falls
outside a configurable band (e.g. more than 3 standard deviations, or outside
0.5x–2x the mean). Handle the cold-start case where there's insufficient history.

**`checks/null_check.py`**
For each column, compute the null rate and compare to a per-column threshold in
config. A column that's normally 0% null jumping to 40% is a strong signal
something upstream broke.

**`checks/outlier_check.py`**
Apply z-score (or IQR, which is more robust to skew) on key numeric fields like
`unit_price` and `total_amount`. This one returns **row-level** failures, since
individual records get quarantined rather than the whole batch.

### 5.3 Externalize thresholds
Put all thresholds in `config/checks.yml` — never hardcode them. This is a small
detail that reviewers notice:

```yaml
volume:
  rolling_window_days: 30
  std_dev_threshold: 3
  min_history_days: 7
nulls:
  order_id: 0.0
  customer_id: 0.05
  total_amount: 0.01
outliers:
  method: iqr
  iqr_multiplier: 3.0
  columns: [unit_price, total_amount]
```

### 5.4 Write unit tests
In `tests/`, write tests for each check using small known-good and known-bad
fixtures. You don't need exhaustive coverage — three or four tests per check
that prove it catches what it should and doesn't false-positive on clean data.

```bash
pytest tests/ -v
```

**Commit checkpoint:** `"Add anomaly detection module with unit tests"`

---

## Phase 6 — Quarantine and alerting

### 6.1 Create the quarantine table
```
quarantine.failed_records
├── quarantine_id       (PK)
├── batch_date
├── check_name
├── severity
├── failed_at           (timestamp)
├── record_payload      (JSONB — the offending row)
└── resolved            (boolean, default false)
```

The `resolved` flag matters: it turns quarantine from a dead-end dump into
something with a workflow, which is closer to how real observability tools work.

### 6.2 Wire checks into the DAG
Insert a `run_quality_checks` task between `transform_silver` and
`aggregate_gold`. Behavior by severity:

- **Critical** (schema drift, missing required columns) → fail the DAG, don't
  promote to Gold at all
- **High** (volume anomaly) → promote to Gold but alert loudly
- **Medium** (row-level outliers, null spikes) → quarantine the offending rows,
  promote the rest

That graduated response is the "self-healing" part — the pipeline keeps running
where it safely can instead of halting on every imperfection.

### 6.3 Set up Slack alerting
1. Create a Slack app at https://api.slack.com/apps
2. Enable **Incoming Webhooks**, add one to a channel (e.g. `#data-alerts`)
3. Store the webhook URL in an Airflow Connection or `.env` — **never commit it**
4. Write `checks/alerting.py` that formats a readable message:

```
🚨 Data Quality Alert — orders_pipeline
Batch: 2026-09-14
Check: volume_anomaly (HIGH)
Observed 45,200 rows vs. expected ~5,400 (8.3x)
Action: Batch promoted with warning
```

### 6.4 Test it end to end
```bash
python data/generate_data.py --date 2026-09-15 --inject-anomaly volume
# trigger the DAG, confirm the alert fires
```

Do this for each anomaly type. Screenshot the alerts — you'll want them for the
README.

**Commit checkpoint:** `"Add quarantine routing and Slack alerting"`

---

## Phase 7 — Dashboard

Connect Power BI or Qlik directly to `pipeline_db`.

Build one page with:
- **Clean vs. quarantined records over time** (stacked area or bar)
- **Check failures by type** (bar chart — which checks fire most)
- **Data quality score** — a single headline number, e.g. clean records as a
  percentage of total, trended over time
- **Recent quarantine detail table** — filterable by check name and date

Keep it to one page. A focused single view reads as more considered than four
half-filled tabs.

**Commit checkpoint:** `"Add data quality dashboard"`

---

## Phase 8 — Documentation and polish

This phase is what converts a working project into a *portfolio* project. Don't
skip it — most people do, which is exactly why doing it stands out.

### 8.1 Architecture diagram
Draw it in Excalidraw or draw.io, export as PNG to `docs/architecture.png`, and
embed it at the top of the README.

### 8.2 Flesh out the README
Include:
- One-paragraph summary of what it does and why
- Architecture diagram
- Tech stack
- Table of the checks implemented and what each catches
- Screenshots: the dashboard, and a Slack alert firing
- How to run it locally (clone → `docker compose up` → trigger DAG)
- **"What I'd do differently at scale"** — call out Great Expectations, dbt for
  the Silver transforms, a proper data catalog, and separating compute from
  orchestration. Showing you know the limits of your own implementation reads
  as senior.
- A line linking to your FLAGSHIP-PROJECT repo, noting how the two differ

### 8.3 Demo recording
Record 60–90 seconds: inject an anomaly, trigger the DAG, show the Slack alert
firing and the record landing in quarantine, then the dashboard updating. Use
Loom or a screen recorder, export as GIF or link it in the README.

### 8.4 Tag a release
```bash
git tag -a v1.0 -m "Initial complete build"
git push origin v1.0
```

### 8.5 Publish it
- Add to your resume under Projects, with a quantified line
- LinkedIn post walking through the problem and what you built
- Pin the repo on your GitHub profile

**Final commit:** `"Add documentation, diagrams, and demo"`

---

## Stretch goals

Once v1.0 is done and published:

- Replace hand-rolled checks with **Great Expectations** or **Soda Core** — and
  write up the comparison; that's genuinely interesting content
- Add **GitHub Actions** CI to run `pytest` on every push
- Add a **second data source** to prove the check module generalizes
- Deploy to **Azure Data Factory** or **Cloud Composer** for the cloud story
- Add **data lineage** tracking (OpenLineage / Marquez)
