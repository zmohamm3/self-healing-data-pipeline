import pytest
from checks.schema_check import check_schema
from checks.volume_check import check_volume
from checks.null_check import check_nulls
from checks.outlier_check import check_outliers

def test_schema_check():
    valid_cols = ["order_id", "customer_id", "order_date", "product_category", "quantity", "unit_price", "total_amount", "region"]
    assert check_schema(valid_cols)["passed"] is True
    
    invalid_cols = ["order_id", "customer_id"]
    assert check_schema(invalid_cols)["passed"] is False

def test_volume_check():
    history = [100] * 10
    assert check_volume(105, history)["passed"] is True
    assert check_volume(1000, history)["passed"] is False

def test_null_check():
    clean_batch = [{"order_id": "1", "customer_id": "C1", "total_amount": "10.0"}]
    assert check_nulls(clean_batch)["passed"] is True

    corrupt_batch = [{"order_id": "1", "customer_id": None, "total_amount": "10.0"}] * 10
    assert check_nulls(corrupt_batch)["passed"] is False

def test_outlier_check():
    clean_batch = [{"order_id": str(i), "unit_price": 50.0, "total_amount": 100.0} for i in range(100)]
    assert check_outliers(clean_batch)["passed"] is True

    corrupt_batch = list(clean_batch)
    corrupt_batch.append({"order_id": "999", "unit_price": 5000.0, "total_amount": 10000.0})
    assert check_outliers(corrupt_batch)["passed"] is False
