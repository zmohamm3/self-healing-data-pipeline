import argparse
import csv
import os
import random
import uuid
from datetime import datetime, timedelta

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Beauty"]
REGIONS = ["US-East", "US-West", "EU-Central", "APAC", "LATAM"]

def generate_daily_batch(batch_date_str, base_rows=100, inject_anomaly=None):
    num_rows = base_rows

    # Handle Volume Anomaly
    if inject_anomaly == "volume":
        multiplier = random.choice([0.1, 10.0])
        num_rows = max(1, int(base_rows * multiplier))

    records = []
    for _ in range(num_rows):
        order_id = str(uuid.uuid4())
        customer_id = f"CUST-{random.randint(1000, 1050)}"
        category = random.choice(CATEGORIES)
        region = random.choice(REGIONS)
        quantity = random.randint(1, 10)
        
        # Base price mean ~50
        unit_price = round(max(5.0, random.gauss(50.0, 15.0)), 2)

        # Handle Outlier Anomaly
        if inject_anomaly == "outlier" and random.random() < 0.3:
            unit_price = round(unit_price * 50, 2)

        total_amount = round(quantity * unit_price, 2)

        # Handle Nulls Anomaly
        if inject_anomaly == "nulls" and random.random() < 0.4:
            customer_id = None

        record = {
            "order_id": order_id,
            "customer_id": customer_id,
            "order_date": batch_date_str,
            "product_category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "region": region
        }
        records.append(record)

    # Handle Schema Anomaly
    if inject_anomaly == "schema" and records:
        choice = random.choice(["drop", "add"])
        if choice == "drop":
            for r in records:
                r.pop("region", None)
        else:
            for r in records:
                r["unexpected_column"] = "CORRUPTED_VALUE"

    return records

def main():
    parser = argparse.ArgumentParser(description="Synthetic retail order data generator")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to generate")
    parser.add_argument("--rows", type=int, default=100, help="Base rows per day")
    parser.add_argument("--output", type=str, default="data/", help="Output folder")
    parser.add_argument("--inject-anomaly", choices=["schema", "volume", "nulls", "outlier"], help="Type of anomaly to inject")

    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)

    start_date = datetime.strptime(args.start, "%Y-%m-%d")

    for i in range(args.days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Only inject anomaly on the last day if requested
        anomaly = args.inject_anomaly if (i == args.days - 1) else None
        batch_data = generate_daily_batch(date_str, base_rows=args.rows, inject_anomaly=anomaly)

        if not batch_data:
            continue

        file_path = os.path.join(args.output, f"orders_{date_str}.csv")
        fieldnames = list(batch_data[0].keys())

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(batch_data)

        print(f"Generated {file_path} with {len(batch_data)} rows" + (f" [Anomaly: {anomaly}]" if anomaly else ""))

if __name__ == "__main__":
    main()
