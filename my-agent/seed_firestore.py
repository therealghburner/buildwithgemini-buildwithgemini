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

import datetime
from google.cloud import firestore

# CRITICAL: Hardcode project ID as string for Firestore client
PROJECT_ID = "qwiklabs-gcp-03-dcb3c6d873b1"
COLLECTION_NAME = "user_profiles"


def seed_firestore():
    print(f"Connecting to Firestore with hardcoded project ID: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)

    seeded_items = [
        {
            "user_id": "alice_smith",
            "display_name": "Alice Smith",
            "allergies": ["peanuts", "penicillin"],
            "dietary_preferences": ["vegetarian"],
            "notes": "Severe peanut allergy - carries EpiPen. Avoid cross-contamination.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "user_id": "bob_jones",
            "display_name": "Bob Jones",
            "allergies": ["shellfish", "dust mites"],
            "dietary_preferences": ["gluten-free", "dairy-free"],
            "notes": "Prefers seafood-free Asian cuisines. Allergic to shrimp, crab, and lobster.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "user_id": "charlie_brown",
            "display_name": "Charlie Brown",
            "allergies": ["tree nuts", "latex", "sulfa drugs"],
            "dietary_preferences": ["keto"],
            "notes": "Tree nut allergy (almonds, walnuts, cashews). Seeds and peanuts are fine.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    ]

    collection_ref = db.collection(COLLECTION_NAME)
    for item in seeded_items:
        doc_ref = collection_ref.document(item["user_id"])
        doc_ref.set(item, merge=True)
        print(f"Seeded user profile for '{item['user_id']}' ({item['display_name']})")

    print("\n✅ Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_firestore()
