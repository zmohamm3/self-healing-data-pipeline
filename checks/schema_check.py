import yaml

def check_schema(batch_columns, checks_config_path="config/checks.yml"):
    with open(checks_config_path, "r") as f:
        cfg = yaml.safe_load(f)
        
    expected_cols = cfg.get("required_columns", {})
    expected = list(expected_cols.keys()) if isinstance(expected_cols, dict) else expected_cols
    
    missing = set(expected) - set(batch_columns)
    unexpected = set(batch_columns) - set(expected)
    
    passed = len(missing) == 0 and len(unexpected) == 0
    severity = "critical" if missing else ("low" if unexpected else "none")
    
    msg = f"Schema check {'passed' if passed else 'failed'}. Missing: {list(missing)}, Unexpected: {list(unexpected)}"
    return {
        "check_name": "schema_check",
        "passed": passed,
        "severity": severity,
        "message": msg,
        "failed_records": [],
        "metadata": {"missing": list(missing), "unexpected": list(unexpected)}
    }
