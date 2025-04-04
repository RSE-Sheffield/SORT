"""
Component builders for the dashboard layout.

This module provides functions for constructing the UI components that make up
the dashboard layout.
"""

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from .constants import (
    THEME,
    TEXT_STYLE,
    CARD_STYLE,
    TABLE_STYLE,
    METRICS,
)


def create_styled_label(text, additional_style=None):
    style = {**TEXT_STYLE, "marginBottom": "5px"}
    if additional_style:
        style.update(additional_style)
    return html.Label(text, style=style)


def create_filter_dropdown(filter_id, placeholder):
    return dcc.Dropdown(
        id=f"{filter_id}-filter",
        placeholder=f"Select {placeholder}",
        clearable=True,
        className="mb-2",
        style={"width": "100%"}
    )


def create_filters_section(dash_app):
    demographic_fields = dash_app.demographic_fields

    filter_columns = [
        dbc.Col(
            [
                create_styled_label(f'{field["label"]}:'),
                create_filter_dropdown(field["id"], field["label"]),
            ],
            width=2,
            className="px-2",
            style={"minWidth": "230px"},
        )
        for field in demographic_fields
    ]

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dbc.Row(
                                                filter_columns,
                                                className="justify-content-center",
                                                style={"display": "flex", "flexWrap": "wrap"}
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Button(
                                                                "Clear All Filters",
                                                                id="clear-filters",
                                                                className="btn btn-primary",
                                                                style={
                                                                    "backgroundColor": THEME[
                                                                        "btn_primary"
                                                                    ],
                                                                    "border": "none",
                                                                    "float": "right",
                                                                },
                                                            )
                                                        ],
                                                        width=12,
                                                    )
                                                ],
                                                className="mt-3",
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        style=CARD_STYLE,
                    )
                ],
                width=12,
            )
        ]
    )


def create_metric_card(metric_id, title):
    """Create a metric card component"""
    return dbc.Col(
        [
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H6(title, style={**TEXT_STYLE, "textAlign": "center"}),
                            html.H3(
                                id=metric_id,
                                style={
                                    **TEXT_STYLE,
                                    "fontWeight": "normal",
                                    "textAlign": "center",
                                },
                            ),
                        ]
                    )
                ],
                style=CARD_STYLE,
            )
        ],
        width=4,
    )


def create_metrics_section():
    """Create the key metrics cards section"""
    return dbc.Row(
        [create_metric_card(metric["id"], metric["title"]) for metric in METRICS],
        className="g-4",
        style={"marginBottom": "20px"},
    )


def create_section_components(section_letter, title):
    """Create the components for a section (incl. summary, graph, and stats table)"""
    return [
        # Summary Card
        dbc.Card(
            [
                dbc.CardHeader(
                    [html.H5(f"Section {section_letter}: {title}", style=TEXT_STYLE)]
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            id=f"section-summary-{section_letter.lower()}",
                            style={
                                **TEXT_STYLE,
                                "padding": "20px",
                                "backgroundColor": "white",
                                "borderRadius": "1rem",
                                "fontSize": "15px",
                                "lineHeight": "1.6",
                            },
                        )
                    ]
                ),
            ],
            style=CARD_STYLE,
        ),
        # Graph Card
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id=f"section-breakdown-{section_letter.lower()}",
                            config={"displayModeBar": False},
                        )
                    ]
                )
            ],
            style=CARD_STYLE,
        ),
        # Statistics Table
        dash_table.DataTable(
            id=f"section-{section_letter.lower()}-stats",
            columns=[
                {"name": "Statistic", "id": "statistic"},
                {"name": "Value", "id": "value"},
            ],
            style_table=TABLE_STYLE,
            style_cell={
                "textAlign": "center",
                "padding": "10px",
                "fontFamily": THEME["font_family"],
                "fontSize": "15px",
                "border": "1px solid #ddd",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_header={
                "backgroundColor": "white",
                "fontWeight": "bold",
                "border": "1px solid #ddd",
                "whiteSpace": "normal",
                "height": "auto",
                "fontSize": "16px",
            },
        ),
    ]


def create_section_layout(section_letter, title):
    """Create layout for a given survey section with proper spacing and centered comment header"""
    components = create_section_components(section_letter, title)

    # Comments section with properly spaced and centered header
    comments_section = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        id=f"toggle-comments-{section_letter.lower()}",
                        children="Loading comments...",
                        style={
                            **TEXT_STYLE,
                            "textAlign": "center",  # Center the text
                            "margin": "0px",
                        }
                    )
                ]
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        html.Div(
                            id=f"comments-panel-{section_letter.lower()}",
                            children="No comments available.",
                            style={
                                **TEXT_STYLE,
                                "padding": "20px",
                                "backgroundColor": "white",
                                "borderRadius": "1rem",
                                "fontSize": "15px",
                                "lineHeight": "1.6",
                            },
                        )
                    ]
                ),
                id=f"collapse-comments-{section_letter.lower()}",
                is_open=False,
            ),
        ],
        style={
            **CARD_STYLE,
            "cursor": "pointer",
            "marginTop": "20px"  # Add space between this and the previous element
        },
        id=f"comments-card-{section_letter.lower()}"
    )

    # Add the comments section to the list of components
    all_components = components + [comments_section]

    return dbc.Row(
        [
            dbc.Col(all_components, width=12),
        ],
        style={"marginTop": "20px", "marginBottom": "20px"},
    )


def create_ranking_matrix(dash_app):
    """Create the ranking matrix component with legend"""
    sections = dash_app.sections

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.H5(
                                        "Summary Ranking Matrix",
                                        style={
                                            "fontFamily": THEME["font_family"],
                                            "color": THEME["text_color"],
                                            "marginBottom": "0px",
                                        },
                                    )
                                ]
                            ),
                            dbc.CardBody(
                                [
                                    dash_table.DataTable(
                                        id="ranking-matrix",
                                        columns=[
                                            {"name": "", "id": "survey"},
                                            *[
                                                {
                                                    "name": section["title"],
                                                    "id": section["id"],
                                                }
                                                for section in sections
                                            ],
                                        ],
                                        style_table={
                                            "width": "100%",
                                            "borderRadius": "1rem",
                                        },
                                        style_cell={
                                            "textAlign": "center",
                                            "padding": "8px",
                                            "fontFamily": THEME["font_family"],
                                            "fontSize": "14px",
                                            "border": "1px solid #ddd",
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "maxWidth": "0",
                                            "overflow": "hidden",
                                            "textOverflow": "ellipsis",
                                        },
                                        style_header={
                                            "backgroundColor": "white",
                                            "fontWeight": "semi-bold",
                                            "border": "1px solid #ddd",
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    *[
                                                        html.Div(
                                                            [
                                                                html.Span(
                                                                    style={
                                                                        "display": "inline-block",
                                                                        "width": "12px",
                                                                        "height": "12px",
                                                                        "backgroundColor": color,
                                                                        "marginRight": "4px",
                                                                        "verticalAlign": "middle",
                                                                    }
                                                                ),
                                                                html.Span(
                                                                    label,
                                                                    style={
                                                                        "fontFamily": THEME[
                                                                            "font_family"
                                                                        ],
                                                                        "fontSize": "12px",
                                                                        "verticalAlign": "middle",
                                                                    },
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "inline-flex",
                                                                "alignItems": "center",
                                                                "marginRight": "8px",
                                                                "marginBottom": "8px",
                                                                "flexShrink": 0,
                                                            },
                                                        )
                                                        for label, color in [
                                                            (
                                                                "Not Yet Planned",
                                                                "#d7191c",
                                                            ),
                                                            ("Planned", "#fdae61"),
                                                            (
                                                                "Early Progress",
                                                                "#abd9e9",
                                                            ),
                                                            (
                                                                "Substantial Progress",
                                                                "#74add1",
                                                            ),
                                                            ("Established", "#2c7bb6"),
                                                        ]
                                                    ]
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "flexWrap": "wrap",
                                                    "justifyContent": "center",
                                                    "alignItems": "center",
                                                    "gap": "8px",
                                                },
                                            )
                                        ],
                                        style={"marginTop": "16px", "width": "100%"},
                                    ),
                                ]
                            ),
                        ],
                        style={
                            "borderRadius": "10px",
                            "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
                            "marginBottom": "20px",
                        },
                    )
                ],
                width=12,
            )
        ],
        style={"marginTop": "20px", "marginBottom": "20px"},
    )


def create_demographics_section(dash_app):
    """
    Create the demographics charts section with larger charts and flexible legends
    """
    demographic_fields = dash_app.demographic_fields

    charts = []
    for field in demographic_fields:
        chart_col = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5(field["label"], style=TEXT_STYLE)
                    ),
                    dbc.CardBody(
                        dcc.Graph(
                            id=f"{field['id']}-chart",
                            config={"displayModeBar": False},
                            figure={},
                            style={"height": "400px"}
                        ),
                        style={"height": "480px", "padding": "15px"}
                    )
                ],
                style={**CARD_STYLE, "height": "550px"}
            ),
            xs=12,
            sm=12,
            md=6,
            lg=6,
            xl=4,
            className="mb-4"
        )
        charts.append(chart_col)

    responsive_charts = dbc.Row(
        charts,
        className="g-4"
    )

    return dbc.Row(
        [
            dbc.Col(
                [

                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [html.H5("Demographic Breakdown", style=TEXT_STYLE)]
                            )
                        ],
                        style=CARD_STYLE
                    ),

                    responsive_charts
                ],
                width=12
            )
        ],
        style={"marginTop": "20px", "marginBottom": "40px"}
    )


def create_dashboard_layout(dash_app):
    """Create the main dashboard layout"""
    sections = dash_app.sections

    return html.Div(
        [
            dcc.Store(id="stored-data", storage_type="memory"),
            dbc.Container(
                [   # 1: filters
                    create_filters_section(dash_app),
                    # 2: summary metrics
                    dcc.Loading(
                        id="loading-metrics",
                        type="circle",
                        children=create_metrics_section(),
                    ),
                    # 3: SORT sections
                    *[
                        dcc.Loading(
                            id=f"loading-section-{section['letter'].lower()}",
                            type="circle",
                            children=create_section_layout(section["letter"], section["title"]),
                        )
                        for section in sections
                    ],
                    # 4: Demographic sections
                    dcc.Loading(
                        id="loading-demographics",
                        type="circle",
                        children=create_demographics_section(dash_app)
                    ),
                    # 5: Overall ranking metrics
                    create_ranking_matrix(dash_app),

                ],
                fluid=True,
            ),
        ]
    )