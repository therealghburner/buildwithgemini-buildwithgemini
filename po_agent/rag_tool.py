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
import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-03-dcb3c6d873b1"
LOCATION = "us-central1"


def search_procurement_policies(query: str) -> str:
    """Searches the corporate procurement policy RAG corpus for guidelines, approval matrices, and vendor rules.

    Args:
        query: What purchasing rule, approval threshold, or vendor policy to look up.

    Returns:
        Relevant passages from the official procurement policy document.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    corpus_file = os.path.join(os.path.dirname(__file__), "rag_config.txt")
    if not os.path.exists(corpus_file):
        return "Error: RAG Corpus configuration file 'rag_config.txt' not found."

    with open(corpus_file, "r") as f:
        corpus_name = f.read().strip()

    try:
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=3),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant policy passages found."
    except Exception as e:
        return f"Policy RAG search failed: {e}"
