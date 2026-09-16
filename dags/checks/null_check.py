import yaml

def check_nulls(records, checks_config_path="config/checks.yml"):
    with open(checks_config_path, "r") as f:
        thresholds = yaml.safe_load(f).get("nulls", {})
    
    if not records:
        return {"check_name": "null_check", "passed": True, "severity": "none", "message": "Empty batch", "failed_records": [], "metadata": {}}

    total_rows = len(records)
    failed_columns = {}

    for col, max_rate in thresholds.items():
        null_count = sum(1 for r in records if r.get(col) is None or str(r.get(col)).strip() == "")
        null_rate = null_count / total_rows
        if null_rate > max_rate:
            failed_columns[col] = {"observed_rate": null_rate, "allowed_rate": max_rate}

    passed = len(failed_columns) == 0
    return {
        "check_name": "null_check",
        "passed": passed,
        "severity": "high" if not passed else "none",
        "message": f"Null rate violations found in columns: {list(failed_columns.keys())}" if not passed else "Null checks passed",
        "failed_records": [],
        "metadata": {"failed_columns": failed_columns, "total_rows": total_rows}
    }
