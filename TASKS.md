# Project Tasks

Check items off as you complete them. Commit after each task (or small group of
tasks) so your GitHub history shows the build progressing.

## Week 1 — Data source + pipeline skeleton
- [ ] Decide on data source (recommended: write a synthetic data generator so you
      control when/how anomalies get injected)
- [ ] Create GitHub repo, initial commit (README + folder structure)
- [ ] Set up Airflow locally via Docker
- [ ] Write DAG: ingest raw data into Bronze layer
- [ ] Write transform: Bronze → Silver (basic cleansing, schema enforcement)
- [ ] Confirm the happy-path pipeline runs end-to-end with no checks yet
- [ ] Commit: "Working Bronze → Silver pipeline skeleton"

## Week 2 — Anomaly detection layer
- [ ] Build Python module for reusable checks (not hardcoded into the DAG)
- [ ] Implement schema drift check (missing/unexpected columns)
- [ ] Implement volume anomaly check (row count vs. rolling average)
- [ ] Implement null-rate threshold check
- [ ] Implement statistical outlier check (z-score or IQR on a key numeric field)
- [ ] Wire checks into the DAG between Silver and Gold
- [ ] Write a few unit tests for each check using known-good and known-bad data
- [ ] Commit: "Add anomaly detection layer"

## Week 3 — Quarantine + alerting
- [ ] Create a quarantine table/storage location for failed records
- [ ] Route failing records to quarantine instead of blocking the whole pipeline
- [ ] Set up Slack webhook (or SMTP email) for alerts
- [ ] Alert payload includes: which check failed, record count, timestamp
- [ ] Test end-to-end: inject a bad record, confirm it's quarantined and alerted
- [ ] Commit: "Add quarantine routing and alerting"

## Week 4 — Dashboard + polish
- [ ] Build Power BI or Qlik dashboard: clean vs. quarantined records over time
- [ ] Add breakdown of which anomaly type triggers most often
- [ ] Draw architecture diagram (Excalidraw or draw.io) and add to README
- [ ] Record short demo video/GIF (bonus: inject an anomaly live on camera)
- [ ] Write "What I'd do differently at scale" section in README
- [ ] Final commit + tag release (e.g. `v1.0`)
- [ ] Add project link + one-line description to resume and LinkedIn

## Stretch goals (optional, if you have extra time)
- [ ] Swap hand-rolled checks for Great Expectations or Soda Core
- [ ] Add a simple CI pipeline (GitHub Actions) to run tests on every push
- [ ] Parameterize thresholds via a config file instead of hardcoding
- [ ] Add a second data source to prove the checks generalize
