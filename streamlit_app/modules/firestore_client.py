"""
Firestore connection and data retrieval.
Pure Python — no Streamlit imports.
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client(creds_path: str = None):
    if not firebase_admin._apps:
        try:
            import streamlit as st
            creds_dict = json.loads(st.secrets["firebase"]["credentials"])
            cred = credentials.Certificate(creds_dict)
        except Exception:
            cred = credentials.Certificate(creds_path)

        firebase_admin.initialize_app(cred)

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