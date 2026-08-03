"""
Load game data and buildings from JSON into dataframes.
Lookup helpers for time-based queries.
Pure Python — no streamlit imports.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime


# ======================== LOADING ======================== #

def get_game_data_dict(file_path: str) -> dict:
    """
    Load the main game JSON and return a dict of dataframes + metadata.

    Returns: {
        "player_id": player_id,
        "start_time": start_time,
        "save_time": save_time,
        "device_name": device_name,
        "player_movement_df": player_movement_df,
        "challenge_df": challenge_df,
        "game_events_df": game_events_df,
        "validations_df": validations_df,
        "challenge_id": challenge_id,
        "challenge_duration": challenge_duration,
    }

    """
    with open(file_path, mode="r") as f:
        data = json.load(f)

    # --- Metadata ---
    player_id = data["playerId"]
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
    challenge = data["challengesSaveObject"]["challengesList"][0]
    challenge_id = challenge["challengeId"]
    challenge_duration = float(challenge["challengeDuration"])

    challenge_df = pd.DataFrame([
        {
            "start_time": float(entry["startTime"]),
            "attempt_number": entry["attemptNumber"],
            "attempt_state": entry["state"],
            "attempt_duration": float(entry["attemptDuration"]),
            "target_building_id": entry["targetBuildingId"],
        }
        for entry in challenge["attemptsList"]
    ])

    # Keep only last row per attempt (drop "started", keep "ended")
    challenge_df = challenge_df.drop_duplicates(
        subset=["attempt_number"], keep="last"
    )
    # Replace 0 duration with NaN
    challenge_df["attempt_duration"] = challenge_df["attempt_duration"].replace(0, np.nan)

    # --- Game events ---
    events_list = data["gameEventsManagerSaveObject"]["gameEventsList"]
    game_events_df = pd.DataFrame([
        {
            "time": entry["timer"],
            "actor": entry["eventActor"],
            "verb": entry["eventVerb"],
            "object": entry["eventObject"],
        }
        for entry in events_list
    ]).reset_index(drop=True)

    # --- Validations ---
    validations_list = data["validationManagerSaveObject"]["playerValidationsList"]
    validations_df = pd.DataFrame([
        {
            "time": entry["gameTimer"],
            "validation": entry["playerValidationSaveObject"]["validation"],
            "position_correct": entry["playerValidationSaveObject"]["isPositionCorrect"],
            "orientation_correct": entry["playerValidationSaveObject"]["isOrientationCorrect"],
        }
        for entry in validations_list
    ])

    return {
        "player_id": player_id,
        "start_time": start_time,
        "save_time": save_time,
        "device_name": device_name,
        "player_movement_df": player_movement_df,
        "challenge_df": challenge_df,
        "game_events_df": game_events_df,
        "validations_df": validations_df,
        "challenge_id": challenge_id,
        "challenge_duration": challenge_duration,
    }


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