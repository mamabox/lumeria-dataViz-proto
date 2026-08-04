"""
Map grid configuration and coordinate calculations.
Each level can have a different grid size, but block spacing is always the same.
"""
from dataclasses import dataclass

MAP_GRID_BLOCK_SIZE: int = 30

@dataclass
class MapBounds:
    x_min: float
    x_max: float
    z_min: float
    z_max: float

def get_map_config(grid_cols: int, grid_rows: int) -> dict:
    """
    Calculate map coordinates and extent from grid dimensions.
    
    Args:
        grid_cols: number of columns in the grid (e.g. 6 for level 1)
        grid_rows: number of rows in the grid (e.g. 5 for level 1)
    
    Returns:
        dict with 'coord' and 'extent' tuples
    """
    block = MAP_GRID_BLOCK_SIZE
    half = block / 2

    # Image corners (where the image file maps to)
    coord = MapBounds(
        x_min=-half,
        x_max=grid_cols * block + half,
        z_min=-half,
        z_max=grid_rows * block + half,
    )

    # Axis limits (can include offset adjustments later)
    axis_range = MapBounds(
        x_min=coord.x_min,
        x_max=coord.x_max,
        z_min=coord.z_min,
        z_max=coord.z_max,
    )

    return {
      "coord": coord,           # where the image maps to
      "axis_range": axis_range, # what the plot shows
      "grid_cols": grid_cols,
      "grid_rows": grid_rows,
      "block_size": block,
    }


# --- Predefined levels ---

LEVELS = {
    "level_1": {"grid_cols": 6, "grid_rows": 5},
    # "level_0": {"grid_cols": 3, "grid_rows": 2},
}

# Default map background image per level — filename only, resolved against
# the app's defaults/ folder by data_loader.get_loaded_data.
MAP_IMAGES = {
    "level_1": "example_map_level1.png",
    # "level_0": "example_map_level0.png",
}