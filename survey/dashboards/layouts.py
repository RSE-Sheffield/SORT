from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from .constants import (
    THEME,
    TEXT_STYLE,
    FILTERS,
    CARD_STYLE,
    TABLE_STYLE,
    SECTIONS,
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
        className="mb-3",
    )


def create_filters_section():

    filter_columns = [
        dbc.Col(
            [
                create_styled_label(f'{filter["label"]}:'),
                create_filter_dropdown(filter["id"], filter["label"]),
            ],
            width=3,
        )
        for filter in FILTERS
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
                                            dbc.Row(filter_columns),
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
                                                ]
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


def create_ranking_matrix():
    """Create the ranking matrix component with legend"""
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
                                            {
                                                "name": "Releasing Potential",
                                                "id": "releasing_potential",
                                            },
                                            {
                                                "name": "Embedding Research",
                                                "id": "embedding_research",
                                            },
                                            {
                                                "name": "Linkages and Leadership",
                                                "id": "linkages_leadership",
                                            },
                                            {
                                                "name": "Inclusive Research",
                                                "id": "inclusive_research",
                                            },
                                            {
                                                "name": "Digital Capability",
                                                "id": "digital_capability",
                                            },
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


def create_section_layout(section_letter, title):
    """Create layout for a given survey section"""
    return dbc.Row(
        [dbc.Col(create_section_components(section_letter, title), width=12)],
        style={"marginTop": "20px", "marginBottom": "20px"},
    )


def create_dashboard_layout():
    """Create the main dashboard layout"""
    return html.Div(
        [
            dcc.Store(id="stored-data", storage_type="memory"),
            dbc.Container(
                [
                    create_filters_section(),
                    dcc.Loading(
                        id="loading-metrics",
                        type="circle",
                        children=create_metrics_section(),
                    ),
                    create_metrics_section(),
                    dcc.Loading(
                        id="loading-ranking-matrix",
                        type="circle",
                        children=create_ranking_matrix(),
                    ),
                    *[
                        dcc.Loading(
                            id=f"loading-section-{section['letter'].lower()}",
                            type="circle",
                            children=create_section_layout(section["letter"], section["title"]),
                        )
                        for section in SECTIONS
                    ],
                ],
                fluid=True,
            ),
            create_ranking_matrix(),
        ]
    )
