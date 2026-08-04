"""
Load game data and buildings from JSON into dataframes.
Lookup helpers for time-based queries.
Pure Python — no streamlit imports.
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

from modules.map_config import get_map_config, LEVELS, MAP_IMAGES

# streamlit_app/ — same depth as components/sidebar.py's _BASE_DIR
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Single canonical buildings file, spans every level — not user-uploadable
_BUILDINGS_PATH = os.path.join(_BASE_DIR, "defaults", "example_buildings.json")


# ======================== LOADING ======================== #

def get_game_data_dict_from_dict(data: dict) -> dict:
    """
    Parse a game data dict into dataframes + metadata.
    Works for both file uploads and Firestore data.
    """
    # --- Metadata ---
    player_id = data["playerId"]
    start_time = datetime.fromisoformat(data["startTime"])
    save_time = datetime.fromisoformat(data["saveTime"])
    device_name = data["deviceName"]

    # --- Player movement ---
    movement_list = (
        data["playerSaveObject"]
            ["playerMovementSaveObject"]
            ["playerMovementInfoList"]
    )
    player_movement_df = pd.DataFrame([
        {
            "time": entry["gameTime"],
            "pos_x": entry["position"]["x"],
            "pos_z": entry["position"]["z"],
            "rot_y": entry["rotation"]["y"],
        }
        for entry in movement_list
    ])

    # --- Challenge / attempts ---
    challenge_list = data["challengesSaveObject"]["challengesList"][0]
    level_number: str = challenge_list["levelNumber"]
    challenge_id = challenge_list["challengeId"]
    challenge_duration = float(challenge_list["challengeDuration"])

    challenge_df = pd.DataFrame([
        {
            "start_time": float(entry["startTime"]),
            "attempt_number": entry["attemptNumber"],
            "attempt_state": entry["state"],
            "attempt_duration": float(entry["attemptDuration"]),
            "target_building_id": entry["targetBuildingId"],
        }
        for entry in challenge_list["attemptsList"]
    ])

    challenge_df = challenge_df.drop_duplicates(
        subset=["attempt_number"], keep="last"
    )
    challenge_df["attempt_duration"] = challenge_df["attempt_duration"].replace(0, np.nan)

    # --- Game events ---
    events_list = data["gameEventsManagerSaveObject"]["gameEventsList"]
    if events_list:
        game_events_df = pd.DataFrame([
            {
                "time": entry["timer"],
                "actor": entry["eventActor"],
                "verb": entry["eventVerb"],
                "object": entry["eventObject"],
            }
            for entry in events_list
        ]).reset_index(drop=True)
    else:
        # When no game events
        game_events_df = pd.DataFrame(columns=["time", "actor", "verb", "object"])

    # --- Validations ---
    validations_list = data["validationManagerSaveObject"]["playerValidationsList"]
    if validations_list:
        validations_df = pd.DataFrame([
            {
                "time": entry["gameTimer"],
                "validation": entry["playerValidationSaveObject"]["validation"],
                "position_correct": entry["playerValidationSaveObject"]["isPositionCorrect"],
                "orientation_correct": entry["playerValidationSaveObject"]["isOrientationCorrect"],
            }
            for entry in validations_list
        ])
    else:
        # When not validation
        validations_df = pd.DataFrame(columns=["time", "validation", "position_correct", "orientation_correct"])

    return {
        "player_id": player_id,
        "start_time": start_time,
        "save_time": save_time,
        "device_name": device_name,
        "player_movement_df": player_movement_df,
        "challenge_df": challenge_df,
        "game_events_df": game_events_df,
        "validations_df": validations_df,
        "level_number": level_number,
        "challenge_id": challenge_id,
        "challenge_duration": challenge_duration,
    }

def get_game_data_dict(file_path: str) -> dict:
    """
    Load game JSON from file and parse into dataframes + metadata.
    """
    with open(file_path, mode="r") as f:
        data = json.load(f)

    return get_game_data_dict_from_dict(data)

def get_buildings_df(file_path: str) -> pd.DataFrame:
    """
    Load buildings JSON into a dataframe with building_id as index.
    """
    return pd.read_json(file_path).set_index("building_id")


# ======================== LOOKUPS ======================== #

def get_nearest_index_for_time(
    df: pd.DataFrame, time: float, time_col: str = "time"
) -> int:
    """
    Find the index of the last row where time_col < given time.
    Returns -1 if no match.
    """
    matches = df[df[time_col] < time][time_col]
    if matches.empty:
        return -1
    return int(matches.idxmax())


def get_challenge_value_for_time(
    challenge_df: pd.DataFrame, time: float, key: str
):
    """
    Look up any column value in challenge_df for a given game time.
    Returns -1 if no match.
    """
    idx = get_nearest_index_for_time(challenge_df, time, time_col="start_time")
    if idx == -1:
        return -1
    value = challenge_df.loc[idx, key]
    return int(value) if isinstance(value, np.integer) else value


def get_player_pos_for_time(
    player_movement_df: pd.DataFrame, time: float
) -> tuple[float, float] | None:
    """
    Return (pos_x, pos_z) for the nearest recorded time before the given time.
    Returns None if no match.
    """
    idx = get_nearest_index_for_time(player_movement_df, time)
    if idx == -1:
        return None
    return (
        float(player_movement_df.loc[idx, "pos_x"]),
        float(player_movement_df.loc[idx, "pos_z"]),
    )


# ======================== TIMELINE ======================== #

def get_player_timeline_df(
    player_movement_df: pd.DataFrame,
    challenge_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge challenge context into each movement row.
    Adds: attempt_number, attempt_state, attempt_duration, target_building_id.
    """
    df = player_movement_df.copy()

    df["attempt_number"] = df["time"].apply(
        lambda t: get_challenge_value_for_time(challenge_df, t, "attempt_number")
    )
    df["attempt_state"] = df["time"].apply(
        lambda t: get_challenge_value_for_time(challenge_df, t, "attempt_state")
    )
    df["attempt_duration"] = df["time"].apply(
        lambda t: get_challenge_value_for_time(challenge_df, t, "attempt_duration")
    )
    df["target_building_id"] = df["time"].apply(
        lambda t: get_challenge_value_for_time(challenge_df, t, "target_building_id")
    )

    return df

# ======================== LOADED DATA ======================== #

def get_loaded_data(
    game_data: dict,
    map_image_path: str | None,
    video_path: str | None,
) -> dict:
    """
    Assemble the session payload every view reads: map config and default
    map image derived from the game data's level, the canonical buildings
    file filtered to that level, parsed game data, and the merged movement
    timeline. Single source of truth for this shape so sidebar.py and
    firestore_test.py can't drift apart on how it's built.

    map_image_path may be None (nothing uploaded) — the level's default
    background image is resolved here in that case. Buildings aren't
    user-uploadable at all — always loaded from the one canonical file.
    """
    level_number = game_data["level_number"]
    level_key = f"level_{level_number}"
    map_config = get_map_config(**LEVELS[level_key])

    if map_image_path is None:
        map_image_path = os.path.join(_BASE_DIR, "defaults", MAP_IMAGES[level_key])

    # Single buildings file spans every level — keep only this session's
    buildings_df = get_buildings_df(_BUILDINGS_PATH)
    level_buildings_df = buildings_df[buildings_df["level"] == level_number]

    timeline_df = get_player_timeline_df(
        game_data["player_movement_df"],
        game_data["challenge_df"],
    )
    target_building_id = game_data["challenge_df"].iloc[0]["target_building_id"]

    return {
        "map_config": map_config,
        "map_image_path": map_image_path,
        "video_path": video_path,
        "game_data": game_data,
        "buildings_df": level_buildings_df,
        "timeline_df": timeline_df,
        "target_building_id": target_building_id,
    }