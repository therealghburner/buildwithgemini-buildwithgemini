import pytest
import sqlite3
import os
from db import ReadOnlyDatabaseManager
from generate_db import init_db

TEST_DB = "test_purchase_orders.db"

@pytest.fixture(scope="module")
def setup_test_db():
    init_db(TEST_DB)
    yield TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_read_only_validation():
    # Valid SELECT queries
    assert ReadOnlyDatabaseManager.validate_read_only("SELECT * FROM purchase_orders;") == True
    assert ReadOnlyDatabaseManager.validate_read_only("WITH top_v AS (SELECT vendor_id FROM vendors) SELECT * FROM top_v;") == True

    # Invalid Mutating queries
    assert ReadOnlyDatabaseManager.validate_read_only("UPDATE purchase_orders SET status = 'Approved';") == False
    assert ReadOnlyDatabaseManager.validate_read_only("DELETE FROM vendors WHERE vendor_id = 1;") == False
    assert ReadOnlyDatabaseManager.validate_read_only("DROP TABLE po_items;") == False
    assert ReadOnlyDatabaseManager.validate_read_only("INSERT INTO departments (department_name) VALUES ('Test');") == False

def test_db_execution(setup_test_db):
    results = ReadOnlyDatabaseManager.execute_query("SELECT COUNT(*) as count FROM purchase_orders;", db_path=setup_test_db)
    assert len(results) == 1
    assert results[0]["count"] == 10000

def test_guardrail_exception(setup_test_db):
    with pytest.raises(PermissionError):
        ReadOnlyDatabaseManager.execute_query("DELETE FROM purchase_orders WHERE po_id = 1;", db_path=setup_test_db)
