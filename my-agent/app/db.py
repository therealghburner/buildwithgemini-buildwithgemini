import os
import sqlite3
import re
from typing import Dict, Any, List

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "purchase_orders.db"))

class ReadOnlyDatabaseManager:
    """Safe Read-Only Database Manager enforcing query security guardrails."""

    FORBIDDEN_KEYWORDS = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
        r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"\bREPLACE\b",
        r"\bGRANT\b", r"\bREVOKE\b", r"\bEXEC\b", r"\bATTACH\b"
    ]

    @classmethod
    def validate_read_only(cls, sql_query: str) -> bool:
        """Verifies that the SQL query is strictly a read-only SELECT or WITH query."""
        clean_query = re.sub(r"--.*?\n", "", sql_query)
        clean_query = re.sub(r"/\*.*?\*/", "", clean_query, flags=re.DOTALL)
        clean_query = clean_query.strip().upper()

        if not (clean_query.startswith("SELECT") or clean_query.startswith("WITH")):
            return False

        for pattern in cls.FORBIDDEN_KEYWORDS:
            if re.search(pattern, clean_query):
                return False

        return True

    @classmethod
    def get_schema(cls, db_path: str = DB_PATH) -> str:
        """Returns string representation of database schema."""
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        conn.close()
        return "\n\n".join([t[0] for t in tables if t[0]])

    @classmethod
    def execute_query(cls, query: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
        """Executes read-only SQL query in URI read-only mode."""
        if not cls.validate_read_only(query):
            raise PermissionError("Security Guardrail Triggered: Only read-only SELECT/WITH queries are allowed!")

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()
        return result
