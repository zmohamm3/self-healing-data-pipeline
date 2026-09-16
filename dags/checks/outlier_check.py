import yaml

def check_outliers(records, checks_config_path="config/checks.yml"):
    with open(checks_config_path, "r") as f:
        cfg = yaml.safe_load(f).get("outliers", {})
    
    cols = cfg.get("columns", [])
    multiplier = cfg.get("iqr_multiplier", 3.0)

    failed_records = []
    metadata = {}

    for col in cols:
        values = sorted([float(r[col]) for r in records if r.get(col) is not None])
        if not values:
            continue

        n = len(values)
        q1 = values[int(n * 0.25)]
        q3 = values[int(n * 0.75)]
        iqr = q3 - q1
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)

        metadata[col] = {"q1": q1, "q3": q3, "iqr": iqr, "bounds": [lower_bound, upper_bound]}

        for r in records:
            if r.get(col) is not None:
                val = float(r[col])
                if val < lower_bound or val > upper_bound:
                    failed_records.append({"order_id": r.get("order_id"), "field": col, "value": val, "bounds": [lower_bound, upper_bound]})

    passed = len(failed_records) == 0
    return {
        "check_name": "outlier_check",
        "passed": passed,
        "severity": "medium" if not passed else "none",
        "message": f"Identified {len(failed_records)} outlier field values." if not passed else "Outlier checks passed",
        "failed_records": failed_records,
        "metadata": metadata
    }
