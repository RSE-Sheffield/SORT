"""
Constants settings for the survey dashboard

This script defines the visual styling, colour palettes, maturity levels, and other
constants used throughout the dashboard.
"""

THEME = {
    "primary": "#1192e8",
    "primary_bg": "#e5f6ff",
    "btn_primary": "#0072c3",
    "text_color": "#393939",
    "font_family": "Source Sans Pro, sans-serif",
    "bg_color": "#f8f9fa",
    "agree_color": "#198038",
}

# Colour palette and maturity levels
COLOUR_PALETTE = [
    "#d7191c",  # Red - Not Yet Planned
    "#fdae61",  # Orange - Planned
    "#abd9e9",  # Light Blue - Early Progress
    "#74add1",  # Medium Blue - Substantial Progress
    "#2c7bb6",  # Dark Blue - Established
]

MATURITY_LEVELS = {
    0: "Not Yet Planned",
    1: "Planned",
    2: "Early Progress",
    3: "Substantial Progress",
    4: "Established",
}

# Styles
CARD_STYLE = {
    "borderRadius": "10px",
    "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
    "marginBottom": "20px",
}

TABLE_STYLE = {
    "width": "100%",
    "borderRadius": "1rem",
    "overflow": "hidden",
    "border": "1px solid #ddd",
    "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
}

CELL_STYLE = {
    "textAlign": "center",
    "padding": "10px",
    "fontFamily": THEME["font_family"],
    "fontSize": "15px",
    "border": "1px solid #ddd",
    "whiteSpace": "normal",
    "height": "auto",
}

HEADER_STYLE = {
    "backgroundColor": "white",
    "fontWeight": "bold",
    "border": "1px solid #ddd",
    "whiteSpace": "normal",
    "height": "auto",
    "fontSize": "16px",
}

METRICS = [
    {"id": "total-responses", "title": "Total Responses", "format": lambda x: str(x)},
    {
        "id": "completion-rate",
        "title": "Completion Rate",
        "format": lambda x: f"{x:.0f}%",
    },
    {
        "id": "average-score",
        "title": "Average Survey Score",
        "format": lambda x: f"{x:.1f}",
    },
]

# Graph configurations
GRAPH_LAYOUT = {
    "height": 350,
    "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
    "paper_bgcolor": "white",
    "plot_bgcolor": "white",
    "font": {"family": THEME["font_family"], "size": 13},
    "showlegend": True,
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
    },
    "xaxis": {"showgrid": False, "gridcolor": "rgba(0,0,0,0.1)", "tickangle": 45},
    "yaxis": {"showgrid": True, "gridcolor": "rgba(0,0,0,0.1)"},
}


TEXT_STYLE = {
    "fontFamily": THEME["font_family"],
    "color": THEME["text_color"],
    "marginBottom": "0px",
}


FILTERS = [
    {"id": "gender", "label": "Gender"},
    {"id": "age", "label": "Age"},
    {"id": "band", "label": "Band/Grade"},
    {"id": "qualification", "label": "Qualification"},
    {"id": "ethnicity", "label": "Ethnicity"},
]


SECTIONS = [
    {"letter": "A", "title": "Releasing Potential"},
    {"letter": "B", "title": "Embedding Research"},
    {"letter": "C", "title": "Linkages and Leadership"},
    {"letter": "D", "title": "Inclusive Research"},
    {"letter": "E", "title": "Digital Capability"},
]
