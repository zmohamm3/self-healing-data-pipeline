import os
import json
import urllib.request
import urllib.error

# Retrieve from environment variable, fallback to default URL if not set
SLACK_WEBHOOK_URL = os.getenv(
    "SLACK_WEBHOOK_URL",
    "https://hooks.slack.com/services/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"
)

def send_slack_alert(batch_date, check_name, severity, message, action_taken):
    # Syntax fix for conditional emoji selection
    emoji = "🚨" if severity.lower() in ["critical", "high"] else "⚠️"
    
    alert_text = (
        f"{emoji} *Data Quality Alert — orders_pipeline*\n"
        f"*Batch:* {batch_date}\n"
        f"*Check:* {check_name} ({severity.upper()})\n"
        f"*Message:* {message}\n"
        f"*Action:* {action_taken}"
    )

    if not SLACK_WEBHOOK_URL:
        print("\n" + "=" * 50)
        print("[SLACK ALERT - NO WEBHOOK CONFIGURED]")
        print(alert_text)
        print("=" * 50 + "\n")
        return

    payload = json.dumps({"text": alert_text}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print(f"Successfully sent Slack alert for check: {check_name}")
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")
