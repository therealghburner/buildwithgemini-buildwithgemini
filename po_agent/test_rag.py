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
from rag_tool import search_procurement_policies


def test_search_procurement_policies():
    # If rag_config.txt exists, test retrieval tool
    if os.path.exists("rag_config.txt"):
        res = search_procurement_policies("What is the approval threshold for $30,000 purchase order?")
        assert isinstance(res, str)
        assert len(res) > 0
