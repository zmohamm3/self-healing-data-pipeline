import math
import yaml

def check_volume(current_count, historical_counts, checks_config_path="config/checks.yml"):
    with open(checks_config_path, "r") as f:
        cfg = yaml.safe_load(f).get("volume", {})
    
    min_days = cfg.get("min_history_days", 7)
    if len(historical_counts) < min_days:
        return {
            "check_name": "volume_check",
            "passed": True,
            "severity": "info",
            "message": f"Cold start: Insufficient history ({len(historical_counts)} days < {min_days} min required).",
            "failed_records": [],
            "metadata": {"observed": current_count, "history_days": len(historical_counts)}
        }

    mean = sum(historical_counts) / len(historical_counts)
    variance = sum((x - mean) ** 2 for x in historical_counts) / len(historical_counts)
    raw_std_dev = math.sqrt(variance)
    
    # Avoid divide-by-zero when standard deviation is zero (constant history)
    std_dev = raw_std_dev if raw_std_dev > 0 else (mean * 0.1 if mean > 0 else 1.0)

    threshold = cfg.get("std_dev_threshold", 3.0)
    z_score = abs(current_count - mean) / std_dev
    passed = z_score <= threshold

    return {
        "check_name": "volume_check",
        "passed": passed,
        "severity": "high" if not passed else "none",
        "message": f"Row count {current_count} is {round(z_score, 2)} std devs from rolling mean ({round(mean, 2)})",
        "failed_records": [],
        "metadata": {"observed": current_count, "expected_mean": mean, "std_dev": std_dev, "z_score": z_score}
    }
