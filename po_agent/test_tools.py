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

import os
from tools import get_vendor_risk_score, flag_po_for_audit, export_po_report_csv


def test_get_vendor_risk_score():
    res = get_vendor_risk_score(1)
    assert "vendor_id" in res
    assert "risk_score" in res
    assert "risk_level" in res


def test_flag_po_for_audit():
    res = flag_po_for_audit(101, "High dollar threshold exceeded")
    assert res["status"] == "flagged"
    assert res["po_id"] == 101


def test_export_po_report_csv(tmp_path):
    csv_file = str(tmp_path / "test_report.csv")
    res = export_po_report_csv("SELECT po_id, total_amount FROM purchase_orders LIMIT 5", filename=csv_file)
    assert res["status"] == "success"
    assert res["rows_exported"] == 5
    assert os.path.exists(csv_file)
