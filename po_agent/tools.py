# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import sqlite3
import datetime
from db import ReadOnlyDatabaseManager, DB_PATH


def get_vendor_risk_score(vendor_id: int) -> dict:
    """Calculates vendor performance metrics and risk score based on PO history.

    Args:
        vendor_id: The ID of the vendor to analyze.

    Returns:
        A dictionary containing total PO count, total spend, cancellation rate, and risk level.
    """
    db = ReadOnlyDatabaseManager()
    query = """
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_spend,
            SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled_orders
        FROM purchase_orders
        WHERE vendor_id = ?
    """
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (vendor_id,))
    row = dict(cursor.fetchone())
    conn.close()

    if not row or not row["total_orders"]:
        return {"vendor_id": vendor_id, "found": False, "message": "No PO history for vendor."}

    total_orders = row["total_orders"]
    cancelled = row["cancelled_orders"] or 0
    cancel_rate = (cancelled / total_orders) * 100
    risk_score = min(100, int(cancel_rate * 2.5 + (15 if (row["total_spend"] or 0) > 100000 else 0)))

    return {
        "vendor_id": vendor_id,
        "total_orders": total_orders,
        "total_spend": round(row["total_spend"] or 0, 2),
        "cancellation_rate": f"{cancel_rate:.1f}%",
        "risk_score": risk_score,
        "risk_level": "HIGH" if risk_score > 50 else ("MEDIUM" if risk_score > 25 else "LOW"),
    }


def flag_po_for_audit(po_id: int, reason: str) -> dict:
    """Flags a Purchase Order for compliance audit and logs the flag rationale.

    Args:
        po_id: The ID of the Purchase Order to flag.
        reason: Description or rationale for flagging the PO.

    Returns:
        A dictionary confirming the audit flag details.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS po_audit_flags (
            po_id INTEGER PRIMARY KEY,
            reason TEXT,
            flagged_at TEXT
        )
    """)
    flagged_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute(
        "INSERT OR REPLACE INTO po_audit_flags (po_id, reason, flagged_at) VALUES (?, ?, ?)",
        (po_id, reason, flagged_at),
    )
    conn.commit()
    conn.close()

    return {
        "status": "flagged",
        "po_id": po_id,
        "reason": reason,
        "flagged_at": flagged_at,
        "message": f"PO {po_id} has been flagged for audit.",
    }


def export_po_report_csv(query_sql: str, filename: str = "po_report.csv") -> dict:
    """Executes a read-only SQL query against the PO database and exports the results to a CSV file.

    Args:
        query_sql: The read-only SQL query to run.
        filename: Target filename for the exported CSV file.

    Returns:
        A dictionary with status, exported row count, and output filename.
    """
    results = ReadOnlyDatabaseManager.execute_query(query_sql)
    if not results:
        return {"status": "empty", "rows_exported": 0, "message": "Query returned no rows."}

    headers = list(results[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

    return {
        "status": "success",
        "filename": filename,
        "rows_exported": len(results),
        "message": f"Successfully exported {len(results)} rows to {filename}.",
    }
