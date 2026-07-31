"""
Visual styles for all map elements.
Change values here → updates everywhere (static, animated, video sync).
"""



# --- Trail ---
TRAIL_COLOR = "white"
TRAIL_SIZE = 5
TRAIL_OPACITY = 0.25

# --- Player (current position) ---
PLAYER_COLOR = "seagreen"
PLAYER_SIZE = 20
PLAYER_OUTLINE_COLOR = "black"
PLAYER_OUTLINE_WIDTH = 2

# --- Rotation triangle ---
TRIANGLE_SIZE = 6
TRIANGLE_FILL = "mediumseagreen"
TRIANGLE_OUTLINE_COLOR = "black"
TRIANGLE_OUTLINE_WIDTH = 1.5
TRIANGLE_MODE = "lines"

# --- Attempt paths ---
ATTEMPT_MARKER_SIZE = 4
ATTEMPT_LINE_WIDTH = 2
ATTEMPT_OPACITY = 0.8
ATTEMPT_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
]

# --- POIs (buildings) ---
POI_COLOR = "orange"
POI_SIZE = 25
POI_SYMBOL = "square"
POI_OUTLINE_COLOR = "black"
POI_OUTLINE_WIDTH = 1

# --- Target building ---
TARGET_COLOR = "lightblue"
TARGET_SIZE = 14
TARGET_SYMBOL = "star"
TARGET_OUTLINE_COLOR = "blue"
TARGET_OUTLINE_WIDTH = 1

# --- Cathedral ---
CATHEDRAL_COLOR = "dodgerblue"
CATHEDRAL_SIZE = 30
CATHEDRAL_SYMBOL = "square"
CATHEDRAL_OUTLINE_COLOR = "blue"
CATHEDRAL_OUTLINE_WIDTH = 1
CATHEDRAL_POSITION = (90, 68)

# --- Game events ---
EVENT_STYLES = {
    "attacks": {
        "color": "firebrick",
        "symbol": "x",
        "label": "Dragon",
        "size": 20,
        "opacity": 1.0,
    },
    "validates": {
        "color": "pink",
        "symbol": "diamond",
        "label": "Validation",
        "size": 20,
        "opacity": 1.0,
    },
}