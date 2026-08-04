"""
Firestore connection and data retrieval.
Pure Python — no Streamlit imports.
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore


class FirestoreConnectionError(Exception):
    """Raised when Firestore credentials are missing or invalid."""


def get_firestore_client(creds_path: str = None):
    """
    Initialize Firebase and return a Firestore client.
    Tries Streamlit secrets first (cloud deployment), falls back to a local
    credentials file. Raises FirestoreConnectionError if neither works.
    """
    if not firebase_admin._apps:
        try:
            import streamlit as st
            creds_dict = json.loads(st.secrets["firebase"]["credentials"])
            cred = credentials.Certificate(creds_dict)
        except Exception:
            try:
                cred = credentials.Certificate(creds_path)
            except Exception as e:
                raise FirestoreConnectionError(
                    f"Could not load Firestore credentials from {creds_path} "
                    f"or Streamlit secrets: {e}"
                ) from e

        try:
            firebase_admin.initialize_app(cred)
        except Exception as e:
            raise FirestoreConnectionError(f"Could not initialize Firebase: {e}") from e

    return firestore.client()


def get_all_sessions(db) -> list[dict]:
    """
    Fetch all documents from game_saves collection.
    Returns a list of metadata dicts (without gameData).
    """
    docs = db.collection("game_saves").order_by(
        "startTime", direction=firestore.Query.DESCENDING
    ).stream()

    sessions = []
    for doc in docs:
        data = doc.to_dict()
        sessions.append({
            "sessionId": data.get("sessionId", ""),
            "playerId": data.get("playerId", ""),
            "startTime": data.get("startTime", ""),
            "saveTime": data.get("saveTime", ""),
            "deviceName": data.get("deviceName", ""),
        })

    return sessions


def get_session_game_data(db, session_id: str) -> dict:
    """
    Fetch a single session's gameData and parse it from JSON string to dict.
    """
    doc = db.collection("game_saves").document(session_id).get()

    if not doc.exists:
        return {}

    data = doc.to_dict()
    game_data_str = data.get("gameData", "{}")
    return json.loads(game_data_str)