"""
Download buttons for data and images.
Reusable across pages.
"""

import streamlit as st
import pandas as pd
from modules.data_export import dataframe_to_csv_bytes


def csv_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "Download CSV",
) -> None:
    """Render a download button for a dataframe as CSV."""
    st.download_button(
        label=label,
        data=dataframe_to_csv_bytes(df),
        file_name=filename,
        mime="text/csv",
    )


def image_download_button(
    fig,
    filename: str = "map.png",
    label: str = "Download PNG",
) -> None:
    """Render a download button for a plotly figure as PNG."""
    img_bytes = fig.to_image(format="png", scale=2)
    st.download_button(
        label=label,
        data=img_bytes,
        file_name=filename,
        mime="image/png",
    )