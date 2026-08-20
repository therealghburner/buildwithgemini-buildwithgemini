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

import time
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-dcb3c6d873b1"
LOCATION = "us-central1"
GCS_PATH = "gs://bwg3-qwiklabs-gcp-03-dcb3c6d873b1/rag/procurement_policy.md"


def create_po_rag_corpus():
    print(f"Initializing Vertex AI RAG Engine for project '{PROJECT_ID}' in location '{LOCATION}'...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Switch region RAG DB to serverless mode
    cfg_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg_name,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("Updated RAG Engine config to serverless mode.")
    except Exception as e:
        print(f"Serverless config notice: {e}")

    # 2. Create the RAG Corpus
    corpus = rag.create_corpus(
        display_name="po-procurement-policy-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"Created RAG Corpus: {corpus.name}")

    # 3. Import and index procurement policy document with LLM parser
    print(f"Importing {GCS_PATH} into RAG Corpus...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=(
                "Extract all procurement rules, approval thresholds, payment terms, and vendor policies cleanly."
            ),
        ),
    )
    print(f"Import complete! Imported files count: {resp.imported_rag_files_count}")

    # Save corpus name to a config file for tools
    with open("rag_config.txt", "w") as f:
        f.write(corpus.name)

    return corpus.name


if __name__ == "__main__":
    create_po_rag_corpus()
