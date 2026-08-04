"""
Export dataframes to downloadable formats.
Pure Python — no streamlit imports.
"""

import os
import pandas as pd


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a dataframe to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def export_all_to_csv(game_data: dict, output_dir: str) -> list[str]:
    """
    Export all dataframes from game_data to CSV files on disk.
    Returns list of file paths created.
    """
    os.makedirs(output_dir, exist_ok=True)

    exports = {
        "player_movement.csv": game_data["player_movement_df"],
        "challenges.csv": game_data["challenge_df"],
        "game_events.csv": game_data["game_events_df"],
        "validations.csv": game_data["validations_df"],
    }

    paths = []
    for filename, df in exports.items():
        path = os.path.join(output_dir, filename)
        df.to_csv(path, index=False)
        paths.append(path)

    return paths