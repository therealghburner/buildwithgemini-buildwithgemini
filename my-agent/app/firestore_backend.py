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

# CRITICAL: Hardcode project ID as string for Firestore client so Agent Platform deployment uses project ID instead of project number.
PROJECT_ID = "qwiklabs-gcp-03-dcb3c6d873b1"
COLLECTION_NAME = "user_profiles"


def get_db_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded GCP project ID."""
    return firestore.Client(project=PROJECT_ID)


def get_user_profile(user_id: str) -> dict:
    """Fetches a user's profile from Firestore including allergies, dietary preferences, and notes.

    Args:
        user_id: The unique identifier for the user (e.g. 'user_123' or 'alice_smith').

    Returns:
        A dictionary containing user_id, display_name, allergies, dietary_preferences, notes, and updated_at.
    """
    db = get_db_client()
    doc_ref = db.collection(COLLECTION_NAME).document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return {
        "user_id": user_id,
        "found": False,
        "message": f"No profile found for user_id '{user_id}'.",
    }


def update_user_profile(
    user_id: str,
    display_name: str | None = None,
    allergies: list[str] | None = None,
    dietary_preferences: list[str] | None = None,
    notes: str | None = None,
) -> dict:
    """Updates or creates a user profile record in Firestore with allergies and preferences.

    Args:
        user_id: The unique identifier for the user.
        display_name: The user's full or preferred display name.
        allergies: List of user allergies (e.g. ['peanuts', 'penicillin', 'shellfish']).
        dietary_preferences: List of dietary restrictions (e.g. ['gluten-free', 'vegan']).
        notes: Additional medical, health, or personal notes.

    Returns:
        A dictionary confirming the update operation and updated profile data.
    """
    db = get_db_client()
    doc_ref = db.collection(COLLECTION_NAME).document(user_id)
    doc = doc_ref.get()

    current_data = doc.to_dict() if doc.exists else {}

    update_payload = {
        "user_id": user_id,
        "display_name": display_name if display_name is not None else current_data.get("display_name", user_id),
        "allergies": allergies if allergies is not None else current_data.get("allergies", []),
        "dietary_preferences": dietary_preferences if dietary_preferences is not None else current_data.get("dietary_preferences", []),
        "notes": notes if notes is not None else current_data.get("notes", ""),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    doc_ref.set(update_payload, merge=True)
    return {
        "status": "success",
        "message": f"Successfully updated profile for user_id '{user_id}'.",
        "profile": update_payload,
    }


def list_user_profiles() -> list[dict]:
    """Lists all user profile records stored in the Firestore user_profiles collection.

    Returns:
        A list of dictionaries, each representing a user profile record.
    """
    db = get_db_client()
    docs = db.collection(COLLECTION_NAME).stream()
    profiles = []
    for doc in docs:
        profiles.append(doc.to_dict())
    return profiles
