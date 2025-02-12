from django_plotly_dash import DjangoDash
from dash import html, dcc, dash_table, Input, Output, no_update
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
from collections import defaultdict
import json
import os
from django.conf import settings
from scipy import stats

colour_palette = ["#d7191c", "#fdae61", "#ffffbf", "#91bfdb", "#2c7bb6"]

sort_config_path = os.path.join(settings.BASE_DIR, 'data', 'survey_config', 'sort_only_config.json')
demographic_config_path = os.path.join(settings.BASE_DIR, 'data', 'survey_config', 'demography_only_config.json')

with open(sort_config_path, 'r') as f:
    SURVEY_CONFIG = json.load(f)

with open(demographic_config_path, 'r') as f:
    DEMOGRAPHIC_CONFIG = json.load(f)

ALL_SECTIONS = {
    'sort': SURVEY_CONFIG['sections'],
    'demographic': DEMOGRAPHIC_CONFIG['sections']
}


def get_demographic_question(question_label):
    for field in ALL_SECTIONS['demographic'][0]['fields']:
        if field['label'] == question_label:
            return field
    return None


def get_section_questions(section_idx):
    if section_idx < 1 or section_idx > len(SURVEY_CONFIG['sections']):
        return {}

    try:
        section = SURVEY_CONFIG['sections'][section_idx - 1]

        section_title = section['title'].strip()
        section_letter = section_title[0]

        likert_field = next(field for field in section['fields'] if field['type'] == 'likert')

        questions = {}
        for i, text in enumerate(likert_field['sublabels']):
            q_id = f'{section_letter}{i + 1}'
            questions[q_id] = text

        return questions
    except Exception as e:
        print(f"Error in get_section_questions for section {section_idx}: {str(e)}")
        return {}


# Define colour-blind-friendly theme

THEME = {
    'primary': '#1192e8',
    'primary_bg': '#e5f6ff',
    'btn_primary': '#0072c3',
    'text_color': '#393939',
    'font_family': 'Source Sans Pro, sans-serif',
    'bg_color': '#f8f9fa',
    'agree_color': '#198038',
}

dash_app = DjangoDash('SurveyDashboard',
                      external_stylesheets=[dbc.themes.BOOTSTRAP],
                      external_scripts=['https://cdn.plot.ly/plotly-2.20.0.min.js']  # This line is needed for graphs
                      )


def get_category_and_colour(score):
    # Round down to nearest integer
    score_int = int(np.floor(score))

    # Category mappings
    categories = {
        0: "Not yet planned",
        1: "Planned",
        2: "Early progress",
        3: "Substantial Progress",
        4: "Established"
    }

    colours = {
        0: "#d7191c",  # colour-blind safe red
        1: "#fdae61",  # colour-blind safe orange
        2: "#ffffbf",  # colour-blind safe yellow
        3: "#91bfdb",  # colour-blind safe light blue
        4: "#2c7bb6"  # colour-blind safe dark blue
    }

    return categories[score_int], colours[score_int]


# Define the dashboard layout
dash_app.layout = html.Div([
    dcc.Store(id='stored-data', storage_type='memory'),

    dbc.Container([
        # Filter Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label('Gender:',
                                               style={
                                                   'fontFamily': THEME['font_family'],
                                                   'color': THEME['text_color'],
                                                   'marginBottom': '5px'
                                               }),
                                    dcc.Dropdown(
                                        id='gender-filter',
                                        placeholder='Select Gender',
                                        clearable=True,
                                        className='mb-3'
                                    ),
                                ], width=3),
                                dbc.Col([
                                    html.Label('Band/Grade:',
                                               style={
                                                   'fontFamily': THEME['font_family'],
                                                   'color': THEME['text_color'],
                                                   'marginBottom': '5px'
                                               }),
                                    dcc.Dropdown(
                                        id='band-filter',
                                        placeholder='Select Band/Grade',
                                        clearable=True,
                                        className='mb-3'
                                    ),
                                ], width=3),
                                dbc.Col([
                                    html.Label('Qualification:',
                                               style={
                                                   'fontFamily': THEME['font_family'],
                                                   'color': THEME['text_color'],
                                                   'marginBottom': '5px'
                                               }),
                                    dcc.Dropdown(
                                        id='qualification-filter',
                                        placeholder='Select Qualification',
                                        clearable=True,
                                        className='mb-3'
                                    ),
                                ], width=3),
                                dbc.Col([
                                    html.Label('Ethnicity:',
                                               style={
                                                   'fontFamily': THEME['font_family'],
                                                   'color': THEME['text_color'],
                                                   'marginBottom': '5px'
                                               }),
                                    dcc.Dropdown(
                                        id='ethnicity-filter',
                                        placeholder='Select Ethnicity',
                                        clearable=True,
                                        className='mb-3'
                                    ),
                                ], width=3),
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Button(
                                        'Clear All Filters',
                                        id='clear-filters',
                                        className='btn btn-primary',
                                        style={
                                            'backgroundColor': THEME['btn_primary'],
                                            'border': 'none',
                                            'float': 'right'
                                        }
                                    )
                                ], width=12)
                            ])
                        ])
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                })
            ], width=12)
        ]),

        # Key Metrics Cards
        dbc.Row([
            # Total Responses
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Responses",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '8px',
                                    'textAlign': 'center'
                                }),
                        html.H3(id='total-responses',
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px',
                                    'fontWeight': 'normal',
                                    'textAlign': 'center',
                                })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=4),

            # Completion Rate
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Completion Rate",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px',
                                    'textAlign': 'center'
                                }),
                        html.H3(id='completion-rate',
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px',
                                    'fontWeight': 'normal',
                                    'textAlign': 'center'
                                })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=4),

            # Average Score
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Average Score",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '8px',
                                    'textAlign': 'center'
                                }),
                        html.H3(id='average-score',
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px',
                                    'fontWeight': 'normal',
                                    'textAlign': 'center'
                                })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=4)
        ], className='g-4', style={'marginBottom': '20px'}),

        # Section A
        dbc.Row([
            dbc.Col([

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Section A: Releasing Potential",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        html.Div(id='section-summary-a',
                                 style={
                                     'padding': '20px',
                                     'backgroundColor': 'white',
                                     'borderRadius': '1rem',
                                     'fontFamily': THEME['font_family'],
                                     'fontSize': '15px',
                                     'lineHeight': '1.6',

                                 })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                }),

                # Graph Card
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='section-breakdown-a',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        dbc.CardBody([
            dash_table.DataTable(
                id='section-a-stats',
                columns=[
                    {'name': 'Statistic', 'id': 'statistic'},
                    {'name': 'Value', 'id': 'value'}
                ],
                style_table={
                    'width': '100%',
                    'borderRadius': '1rem',
                    'overflow': 'hidden',
                    'border': '1px solid #ddd',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': THEME['font_family'],
                    'fontSize': '15px',
                    'border': '1px solid #ddd',
                    'minWidth': '0px',
                    'maxWidth': 'none',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px'
                }
            )
        ]),

        # Section B
        dbc.Row([
            dbc.Col([

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Section B: Embedding Research",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        html.Div(id='section-summary-b',
                                 style={
                                     'padding': '20px',
                                     'backgroundColor': 'white',
                                     'borderRadius': '1rem',
                                     'fontFamily': THEME['font_family'],
                                     'fontSize': '15px',
                                     'lineHeight': '1.6',

                                 })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                }),

                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='section-breakdown-b',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

dbc.CardBody([
            dash_table.DataTable(
                id='section-b-stats',
                columns=[
                    {'name': 'Statistic', 'id': 'statistic'},
                    {'name': 'Value', 'id': 'value'}
                ],
                style_table={
                    'width': '100%',
                    'borderRadius': '1rem',
                    'overflow': 'hidden',
                    'border': '1px solid #ddd',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': THEME['font_family'],
                    'fontSize': '15px',
                    'border': '1px solid #ddd',
                    'minWidth': '0px',
                    'maxWidth': 'none',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px'
                }
            )
        ]),

        # Section C
        dbc.Row([
            dbc.Col([

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Section C: Linkages and Leadership",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        html.Div(id='section-summary-c',
                                 style={
                                     'padding': '20px',
                                     'backgroundColor': 'white',
                                     'borderRadius': '1rem',
                                     'fontFamily': THEME['font_family'],
                                     'fontSize': '15px',
                                     'lineHeight': '1.6',
                                 })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                }),

                # Graph Card
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='section-breakdown-c',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),


dbc.CardBody([
            dash_table.DataTable(
                id='section-c-stats',
                columns=[
                    {'name': 'Statistic', 'id': 'statistic'},
                    {'name': 'Value', 'id': 'value'}
                ],
                style_table={
                    'width': '100%',
                    'borderRadius': '1rem',
                    'overflow': 'hidden',
                    'border': '1px solid #ddd',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': THEME['font_family'],
                    'fontSize': '15px',
                    'border': '1px solid #ddd',
                    'minWidth': '0px',
                    'maxWidth': 'none',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px'
                }
            )
        ]),

        # Section D
        dbc.Row([
            dbc.Col([

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Section D: Inclusive Research",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        html.Div(id='section-summary-d',
                                 style={
                                     'padding': '20px',
                                     'backgroundColor': 'white',
                                     'borderRadius': '1rem',
                                     'fontFamily': THEME['font_family'],
                                     'fontSize': '15px',
                                     'lineHeight': '1.6',
                                 })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                }),

                # Graph Card
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='section-breakdown-d',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

dbc.CardBody([
            dash_table.DataTable(
                id='section-d-stats',
                columns=[
                    {'name': 'Statistic', 'id': 'statistic'},
                    {'name': 'Value', 'id': 'value'}
                ],
                style_table={
                    'width': '100%',
                    'borderRadius': '1rem',
                    'overflow': 'hidden',
                    'border': '1px solid #ddd',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': THEME['font_family'],
                    'fontSize': '15px',
                    'border': '1px solid #ddd',
                    'minWidth': '0px',
                    'maxWidth': 'none',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px'
                }
            )
        ]),

        # Section E
        dbc.Row([
            dbc.Col([

                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Section E: Digital Capability",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        html.Div(id='section-summary-e',
                                 style={
                                     'padding': '20px',
                                     'backgroundColor': 'white',
                                     'borderRadius': '1rem',
                                     'fontFamily': THEME['font_family'],
                                     'fontSize': '15px',
                                     'lineHeight': '1.6',
                                 })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                }),

                # Graph Card
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id='section-breakdown-e',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}
        ),

    dbc.CardBody([
            dash_table.DataTable(
                id='section-e-stats',
                columns=[
                    {'name': 'Statistic', 'id': 'statistic'},
                    {'name': 'Value', 'id': 'value'}
                ],
                style_table={
                    'width': '100%',
                    'borderRadius': '1rem',
                    'overflow': 'hidden',
                    'border': '1px solid #ddd',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': THEME['font_family'],
                    'fontSize': '15px',
                    'border': '1px solid #ddd',
                    'minWidth': '0px',
                    'maxWidth': 'none',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '16px'
                }
            )
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Pay Band Proportion",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='band-chart',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Gender Proportion",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='gender-chart',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Ethnicity Proportion",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='ethnicity-chart',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Qualification Proportion",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        dcc.Graph(
                            id='qualification-chart',
                            config={'displayModeBar': False}
                        )
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                })
            ], width=12)
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        # Legend for Ranking Matrix
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Summary Ranking Matrix",
                                style={
                                    'fontFamily': THEME['font_family'],
                                    'color': THEME['text_color'],
                                    'marginBottom': '0px'
                                })
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='ranking-matrix',
                            columns=[
                                {'name': '', 'id': 'survey', 'width': '15%'},
                                {'name': 'Releasing Potential', 'id': 'releasing_potential', 'width': '17%'},
                                {'name': 'Embedding Research', 'id': 'embedding_research', 'width': '17%'},
                                {'name': 'Linkages and Leadership', 'id': 'linkages_leadership', 'width': '17%'},
                                {'name': 'Inclusive Research', 'id': 'inclusive_research', 'width': '17%'},
                                {'name': 'Digital Capability', 'id': 'digital_capability', 'width': '17%'}
                            ],
                            style_table={
                                'width': '100%',
                                'borderRadius': '1rem',
                            },
                            style_cell={
                                'textAlign': 'center',
                                'padding': '10px',
                                'fontFamily': THEME['font_family'],
                                'fontSize': '15px',
                                'border': '1px solid #ddd',
                                'minWidth': '0px',
                                'maxWidth': 'none',
                                'whiteSpace': 'normal',
                                'height': 'auto'
                            },
                            style_header={
                                'backgroundColor': 'white',
                                'fontWeight': 'semi-bold',
                                'border': '1px solid #ddd',
                                'whiteSpace': 'normal',
                                'height': 'auto'
                            }
                        ),

                        html.Div([
                            html.Div([
                                html.Span(style={
                                    'display': 'inline-block',
                                    'width': '15px',
                                    'height': '15px',
                                    'backgroundColor': '#d7191c',
                                    'marginRight': '5px',
                                    'verticalAlign': 'middle'
                                }),
                                html.Span('Not Yet Planned', style={
                                    'fontFamily': THEME['font_family'],
                                    'fontSize': '12px',
                                    'marginRight': '10px',
                                    'verticalAlign': 'middle'
                                })
                            ], style={'display': 'inline-block', 'marginRight': '10px'}),
                            html.Div([
                                html.Span(style={
                                    'display': 'inline-block',
                                    'width': '15px',
                                    'height': '15px',
                                    'backgroundColor': '#fdae61',
                                    'marginRight': '5px',
                                    'verticalAlign': 'middle'
                                }),
                                html.Span('Planned', style={
                                    'fontFamily': THEME['font_family'],
                                    'fontSize': '12px',
                                    'marginRight': '10px',
                                    'verticalAlign': 'middle'
                                })
                            ], style={'display': 'inline-block', 'marginRight': '10px'}),
                            html.Div([
                                html.Span(style={
                                    'display': 'inline-block',
                                    'width': '15px',
                                    'height': '15px',
                                    'backgroundColor': '#ffffbf',
                                    'marginRight': '5px',
                                    'verticalAlign': 'middle'
                                }),
                                html.Span('Early Progress', style={
                                    'fontFamily': THEME['font_family'],
                                    'fontSize': '12px',
                                    'marginRight': '10px',
                                    'verticalAlign': 'middle'
                                })
                            ], style={'display': 'inline-block', 'marginRight': '10px'}),
                            html.Div([
                                html.Span(style={
                                    'display': 'inline-block',
                                    'width': '15px',
                                    'height': '15px',
                                    'backgroundColor': '#91bfdb',
                                    'marginRight': '5px',
                                    'verticalAlign': 'middle'
                                }),
                                html.Span('Substantial Progress', style={
                                    'fontFamily': THEME['font_family'],
                                    'fontSize': '12px',
                                    'marginRight': '10px',
                                    'verticalAlign': 'middle'
                                })
                            ], style={'display': 'inline-block', 'marginRight': '10px'}),
                            html.Div([
                                html.Span(style={
                                    'display': 'inline-block',
                                    'width': '15px',
                                    'height': '15px',
                                    'backgroundColor': '#2c7bb6',
                                    'marginRight': '5px',
                                    'verticalAlign': 'middle'
                                }),
                                html.Span('Established', style={
                                    'fontFamily': THEME['font_family'],
                                    'fontSize': '12px',
                                    'verticalAlign': 'middle'
                                })
                            ], style={'display': 'inline-block'})
                        ], style={
                            'textAlign': 'center',
                            'marginTop': '20px'
                        })
                    ])
                ], style={
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                    'marginBottom': '20px'
                })
            ], width=12)
        ],
            style={'marginTop': '20px', 'marginBottom': '20px'}),

    ], fluid=True)
])


@dash_app.callback(
    Output('stored-data', 'data'),
    [Input('gender-filter', 'value'),
     Input('band-filter', 'value'),
     Input('qualification-filter', 'value'),
     Input('ethnicity-filter', 'value')]
)
def filter_data(gender, band, qualification, ethnicity):
    # Get all survey responses
    all_responses = dash_app.initial_arguments.get('survey_responses', [])

    # Apply filters
    filtered_responses = []
    for response in all_responses:
        if 'fields' in response and 'answers' in response['fields']:
            try:
                demographics = response['fields']['answers'][6]  # Demographics section

                # Get demographic field indices from config
                demo_fields = DEMOGRAPHIC_CONFIG['sections'][0]['fields']
                gender_idx = next(i for i, field in enumerate(demo_fields) if field['label'] == 'Your Gender')
                band_idx = next(
                    i for i, field in enumerate(demo_fields) if field['label'] == 'What is your current Band/Grade')
                qual_idx = next(i for i, field in enumerate(demo_fields) if
                                field['label'] == 'Please indicate your highest qualification')
                eth_idx = next(i for i, field in enumerate(demo_fields) if field['label'] == 'What is your ethnicity?')

                # Check if response matches all active filters
                matches_filters = True
                if gender and demographics[gender_idx] != gender:
                    matches_filters = False
                if band and demographics[band_idx] != band:
                    matches_filters = False
                if qualification and demographics[qual_idx] != qualification:
                    matches_filters = False
                if ethnicity and demographics[eth_idx] != ethnicity:
                    matches_filters = False

                if matches_filters:
                    filtered_responses.append(response)
            except (IndexError, KeyError) as e:
                print(f"Error processing response: {e}")
                continue

    # Calculate averages across filtered responses
    section_averages = {}
    for section_idx, section in enumerate(
            ['releasing_potential', 'embedding_research', 'linkages_leadership', 'inclusive_research',
             'digital_capability']):
        section_scores = []
        for response in filtered_responses:
            if 'fields' in response and 'answers' in response['fields']:
                section_data = response['fields']['answers'][section_idx + 1][0]
                scores = [float(score) for score in section_data if score.isdigit()]
                if scores:
                    section_scores.append(np.mean(scores))

        section_averages[section] = np.mean(section_scores) if section_scores else 0

    return {
        'section_averages': section_averages,
        'survey_responses': filtered_responses
    }


def get_section_data(response, section_idx):
    if 'fields' in response and 'answers' in response['fields']:
        try:
            return response['fields']['answers'][section_idx][0]
        except (IndexError, KeyError):
            return []
    return []


def create_section_summary(data, section_idx):

    if not data or 'survey_responses' not in data:
        return []
    scores = []
    for response in data['survey_responses']:
        section_data = get_section_data(response, section_idx)
        scores.extend([int(score) for score in section_data if score.isdigit()])

    if not scores:
        return []

    statistics = [
        {
            'Metric': 'Average Score',
            'Value': f"{np.mean(scores):.2f}"
        },

        {
            'Metric': 'Response Count',
            'Value': str(len(scores))
        },
        {
            'Metric': 'Low Scores (1-2)',
            'Value': f"{(sum(1 for s in scores if s <= 2) / len(scores) * 100):.1f}%"
        },
        {
            'Metric': 'Mid Scores (3)',
            'Value': f"{(sum(1 for s in scores if s == 3) / len(scores) * 100):.1f}%"
        },
        {
            'Metric': 'High Scores (4-5)',
            'Value': f"{(sum(1 for s in scores if s >= 4) / len(scores) * 100):.1f}%"
        }
    ]

    return statistics


# Callback for Section A
@dash_app.callback(
    Output('section-table-a', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_a_table(data):
    if not data:
        return []
    # Section A corresponds to index 1
    return create_section_summary(data, section_idx=1)


@dash_app.callback(
    Output('ranking-matrix', 'data'),
    [Input('stored-data', 'data')]
)
def update_ranking_matrix(data):
    if data and 'section_averages' in data:
        matrix_data = [{
            'survey': 'Current Survey',
            'releasing_potential': get_maturity_level(data['section_averages']['releasing_potential']),
            'embedding_research': get_maturity_level(data['section_averages']['embedding_research']),
            'linkages_leadership': get_maturity_level(data['section_averages']['linkages_leadership']),
            'inclusive_research': get_maturity_level(data['section_averages']['inclusive_research']),
            'digital_capability': get_maturity_level(data['section_averages']['digital_capability'])
        }]
        return matrix_data
    return []


@dash_app.callback(
    Output('ranking-matrix', 'style_data_conditional'),
    [Input('stored-data', 'data')]
)
def update_matrix_styles(data):
    if not data or 'section_averages' not in data:
        return []

    styles = []
    categories = {
        'Not Yet Planned': '#d7191c',
        'Planned': '#fdae61',
        'Early Progress': '#ffffbf',
        'Substantial Progress': '#91bfdb',
        'Established': '#2c7bb6'
    }

    for section in ['releasing_potential', 'embedding_research', 'linkages_leadership',
                    'inclusive_research', 'digital_capability']:
        if section in data['section_averages']:
            maturity_level = get_maturity_level(data['section_averages'][section])
            styles.append({
                'if': {
                    'column_id': section,
                    'filter_query': f'{{{section}}} = "{maturity_level}"'
                },
                'backgroundColor': categories[maturity_level],
                'color': 'black' if maturity_level == 'Early Progress' else 'white'
            })

    return styles


@dash_app.callback(
    [Output('total-responses', 'children'),
     Output('completion-rate', 'children'),
     Output('average-score', 'children')],
    [Input('stored-data', 'data')]
)
def update_stats(data):
    if not data or 'survey_responses' not in data:
        return "0", "0%", "0.0"

    try:

        total_responses = len(data['survey_responses'])

        completed = sum(1 for response in data['survey_responses']
                        if 'fields' in response
                        and 'answers' in response['fields']
                        and len(response['fields']['answers']) >= 6
                        and all(isinstance(response['fields']['answers'][i], list)
                                and len(response['fields']['answers'][i]) >= 1
                                for i in range(1, 6)))

        completion_rate = (completed / total_responses * 100) if total_responses > 0 else 0

        all_scores = []
        for response in data['survey_responses']:
            if 'fields' in response and 'answers' in response['fields']:
                # Loop through sections 1-5, skip consent and demographics
                for section_idx in range(1, 6):
                    try:
                        section_data = response['fields']['answers'][section_idx][0]
                        scores = [float(score) for score in section_data if score.isdigit()]
                        all_scores.extend(scores)
                    except (IndexError, KeyError, ValueError):
                        continue

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        return f"{total_responses}", f"{completion_rate:.0f}%", f"{avg_score:.1f}"

    except Exception as e:
        print(f"Error in update_stats: {str(e)}")
        return "0", "0%", "0.0"


@dash_app.callback(
    Output('consent-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_consent_chart(data):
    if not data or 'survey_responses' not in data:
        return {}

    consent_counts = {'agree': 0, 'disagree': 0}
    total_responses = len(data['survey_responses'])

    for response in data['survey_responses']:
        if 'fields' in response and 'answers' in response['fields']:
            try:
                consent = response['fields']['answers'][0][0]
                if 'Yes' in consent:
                    consent_counts['agree'] += 1
                else:
                    consent_counts['disagree'] += 1
            except (IndexError, KeyError):
                continue

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=['Consent'],
        x=[consent_counts['agree']],
        name='Agreed',
        orientation='h',
        marker_color='#2c7bb6',
        text=[f"{(consent_counts['agree'] / total_responses * 100):.1f}%"],
        textposition='auto',
    ))

    fig.update_layout(
        barmode='stack',
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(
            family=THEME['font_family'],
            size=12
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Number of Responses",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            showgrid=False,
            automargin=True
        )
    )

    return fig


def create_section_figure(data, section_idx):
    if not data or 'survey_responses' not in data:
        return {}

    questions = get_section_questions(section_idx)
    if not questions:
        return {}

    section_letter = list(questions.keys())[0][0]

    responses = defaultdict(list)
    for response in data['survey_responses']:
        section_data = get_section_data(response, section_idx)
        for q_idx, score in enumerate(section_data):
            if score.isdigit():  # Only process numeric responses
                question_id = f'{section_letter}{q_idx + 1}'
                responses[question_id].append(int(score))
    fig = go.Figure()
    question_ids = sorted(responses.keys(), key=lambda x: int(x[1:]))

    for score in range(5):
        y_data = []
        hover_text = []
        for q_id in question_ids:
            count = sum(1 for s in responses[q_id] if s == score)
            y_data.append(count)
            hover_text.append(
                f"{questions[q_id]}<br>"
                f"Count: {count}"
            )
        category, color = get_category_and_colour(score)
        fig.add_trace(go.Bar(
            x=question_ids,
            y=y_data,
            name=category,
            marker_color=color,
            text=[f"{count}" if count > 0 else "" for count in y_data],
            textposition='auto',
            hovertext=hover_text,
            hoverinfo='text',
            offsetgroup=score
        ))

    fig.update_layout(
        barmode='group',
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(
            family=THEME['font_family'],
            size=13
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Questions",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            tickangle=45,
            rangeslider=dict(visible=False) # TODO: fix scroll bar for section A charts
        ),
        yaxis=dict(
            title="Number of Responses",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        )

    )

    return fig


@dash_app.callback(
    Output('section-breakdown-a', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_a(data):
    return create_section_figure(data, 1)  # Index 1 is releasing_potential


@dash_app.callback(
    Output('section-breakdown-b', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_b(data):
    return create_section_figure(data, 2)  # Index 2 is embedding_research


@dash_app.callback(
    Output('section-breakdown-c', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_c(data):
    return create_section_figure(data, 3)  # Index 3 is linkages_leadership


@dash_app.callback(
    Output('section-breakdown-d', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_d(data):
    return create_section_figure(data, 4)  # Index 4 is inclusive_research


@dash_app.callback(
    Output('section-breakdown-e', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_e(data):
    return create_section_figure(data, 5)  # Index 5 is digital_capability


def create_demographic_chart(data, question_label, sort_by_value=False):
    if not data or 'survey_responses' not in data:
        return {}

    question = get_demographic_question(question_label)
    if not question:
        print(f"Question not found: {question_label}")
        return {}

    question_idx = None
    for idx, field in enumerate(DEMOGRAPHIC_CONFIG['sections'][0]['fields']):
        if field['label'] == question_label:
            question_idx = idx
            break

    if question_idx is None:
        return {}

    response_counts = defaultdict(int)

    for response in data['survey_responses']:
        if 'fields' in response and 'answers' in response['fields']:
            try:
                answer = response['fields']['answers'][6][question_idx].title()
                response_counts[answer] += 1
            except (IndexError, KeyError):
                continue

    items = list(response_counts.items())
    if sort_by_value:
        items.sort(key=lambda x: x[1], reverse=True)

    labels, values = zip(*items) if items else ([], [])

    colors = colour_palette[:len(labels)]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0,
        marker=dict(
            colors=colors
        ),
        textinfo='value+percent',
        textfont=dict(
            family=THEME['font_family'],
            size=13
        ),
        textposition='auto',
    )])

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(
            family=THEME['font_family'],
            size=15
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.6,
            xanchor="center",
            x=0.5,
        )
    )

    return fig


@dash_app.callback(
    Output('gender-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_gender_chart(data):
    return create_demographic_chart(data, "Your Gender")


@dash_app.callback(
    Output('band-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_band_chart(data):
    return create_demographic_chart(data, "What is your current Band/Grade", sort_by_value=True)


@dash_app.callback(
    Output('qualification-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_qualification_chart(data):
    return create_demographic_chart(data, "Please indicate your highest qualification")


@dash_app.callback(
    Output('ethnicity-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_ethnicity_chart(data):
    return create_demographic_chart(data, "What is your ethnicity?", sort_by_value=True)


def get_maturity_level(score):
    rounded_score = round(score)
    if rounded_score == 5:
        return "Established"
    elif rounded_score == 4:
        return "Substantial Progress"
    elif rounded_score == 3:
        return "Early Progress"
    elif rounded_score == 2:
        return "Planned"
    else:
        return "Not Yet Planned"


def create_section_summary(data, section_idx):
    if not data or 'survey_responses' not in data:
        return ""

    questions = get_section_questions(section_idx)
    if not questions:
        return ""

    section_letter = list(questions.keys())[0][0]

    question_scores = {}
    for q_id in questions:
        scores = []
        for response in data['survey_responses']:
            section_data = get_section_data(response, section_idx)
            q_idx = int(q_id[1:]) - 1
            if q_idx < len(section_data) and section_data[q_idx].isdigit():
                scores.append(int(section_data[q_idx]))
        if scores:
            question_scores[q_id] = scores

    if not question_scores:
        return ""

    all_scores = [s for scores in question_scores.values() for s in scores]
    section_avg = np.mean(all_scores)
    maturity_level = get_maturity_level(section_avg)

    question_analysis = {}
    for q_id, scores in question_scores.items():
        high_scores = sum(1 for s in scores if s >= 4)
        low_scores = sum(1 for s in scores if s <= 3)
        total_scores = len(scores)

        question_analysis[q_id] = {
            'high_prop': (high_scores / total_scores) * 100,
            'low_prop': (low_scores / total_scores) * 100,
            'avg_score': np.mean(scores)
        }

    high_performing = sorted(
        [(q, analysis) for q, analysis in question_analysis.items() if analysis['high_prop'] >= 50],
        key=lambda x: x[1]['high_prop'],
        reverse=True
    )[:5]

    low_performing = sorted(
        [(q, analysis) for q, analysis in question_analysis.items() if analysis['low_prop'] >= 50],
        key=lambda x: x[1]['low_prop'],
        reverse=True
    )[:5]

    summary_parts = []

    overview = (
        f"Section {section_letter} demonstrates an overall maturity score of "
        f"{round(section_avg)} out of 5, placing it at the <b>'{maturity_level}'</b> level. "
    )
    summary_parts.append(overview)

    if high_performing:
        questions_text = ', '.join(f"question {q}" for q, analysis in high_performing)
        strengths = f"Areas of strength are demonstrated in {questions_text}. "
        summary_parts.append(strengths)

    if low_performing:
        questions_text = ', '.join(f"question {q}" for q, analysis in low_performing)
        development = f"Opportunities for improvement are identified in {questions_text}. "
        summary_parts.append(development)


    if maturity_level in ["Established", "Substantial Progress"]:
        recommendation = (
            "To maintain and build upon this strong performance, focus on sustaining "
            "existing practices while exploring innovative approaches for further advancement. "
        )
    else:
        recommendation = (
            "To enhance maturity in this section, prioritize developing structured "
            "approaches and implementing systematic improvements across identified areas. "
        )
    summary_parts.append(recommendation)


    full_summary = f"<p>{''.join(summary_parts)}</p>"

    return full_summary


@dash_app.callback(
    Output('section-summary-a', 'children'),
    [Input('stored-data', 'data')]
)
def update_section_a_summary(data):
    if not data:
        return "No data available"
    return html.Div([
        dcc.Markdown(create_section_summary(data, section_idx=1),
                     dangerously_allow_html=True)
    ])


@dash_app.callback(
    Output('section-summary-b', 'children'),
    [Input('stored-data', 'data')]
)
def update_section_b_summary(data):
    if not data:
        return "No data available"
    return html.Div([
        dcc.Markdown(create_section_summary(data, section_idx=2),
                     dangerously_allow_html=True)
    ])


@dash_app.callback(
    Output('section-summary-c', 'children'),
    [Input('stored-data', 'data')]
)
def update_section_c_summary(data):
    if not data:
        return "No data available"
    return html.Div([
        dcc.Markdown(create_section_summary(data, section_idx=3),
                     dangerously_allow_html=True)
    ])


@dash_app.callback(
    Output('section-summary-d', 'children'),
    [Input('stored-data', 'data')]
)
def update_section_d_summary(data):
    if not data:
        return "No data available"
    return html.Div([
        dcc.Markdown(create_section_summary(data, section_idx=4),
                     dangerously_allow_html=True)
    ])


@dash_app.callback(
    Output('section-summary-e', 'children'),
    [Input('stored-data', 'data')]
)
def update_section_e_summary(data):
    if not data:
        return "No data available"
    return html.Div([
        dcc.Markdown(create_section_summary(data, section_idx=5),
                     dangerously_allow_html=True)
    ])
def calculate_section_stats(data, section_idx):
    all_scores = []
    for response in data['survey_responses']:
        if 'fields' in response and 'answers' in response['fields']:
            try:
                section_data = response['fields']['answers'][section_idx][0]
                scores = [float(score) for score in section_data if score.isdigit()]
                all_scores.extend(scores)
            except (IndexError, KeyError) as e:
                print(f"Error processing response for section {section_idx}: {str(e)}")
                continue

    try:
        mode_value = stats.mode(all_scores, keepdims=False)[0]
        statistics = [
            {'statistic': 'Mean Score', 'value': f"{np.mean(all_scores):.2f}"},
            {'statistic': 'Minimum', 'value': f"{min(all_scores):.1f}"},
            {'statistic': 'Maximum', 'value': f"{max(all_scores):.1f}"},
            {'statistic': 'Mode', 'value': f"{mode_value:.1f}"}
        ]
        return statistics
    except Exception as e:
        print(f"Error calculating statistics for section {section_idx}: {str(e)}")
        return []


@dash_app.callback(
    Output('section-a-stats', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_a_stats(data):
    return calculate_section_stats(data, 1)

@dash_app.callback(
    Output('section-b-stats', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_b_stats(data):
    return calculate_section_stats(data, 1)


@dash_app.callback(
    Output('section-c-stats', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_c_stats(data):
    return calculate_section_stats(data, 1)


@dash_app.callback(
    Output('section-d-stats', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_d_stats(data):
    return calculate_section_stats(data, 1)

@dash_app.callback(
    Output('section-e-stats', 'data'),
    [Input('stored-data', 'data')]
)
def update_section_e_stats(data):
    return calculate_section_stats(data, 1)

@dash_app.callback(
    [Output('gender-filter', 'options'),
     Output('band-filter', 'options'),
     Output('qualification-filter', 'options'),
     Output('ethnicity-filter', 'options')],
    [Input('stored-data', 'data')]
)
def update_filter_options(data):
    demographic_fields = DEMOGRAPHIC_CONFIG['sections'][0]['fields']

    gender_options = [{'label': opt, 'value': opt}
                      for opt in next(field['options']
                                      for field in demographic_fields if field['label'] == 'Your Gender')]

    band_options = [{'label': opt, 'value': opt}
                    for opt in next(field['options']
                                    for field in demographic_fields if
                                    field['label'] == 'What is your current Band/Grade')]

    qualification_options = [{'label': opt, 'value': opt}
                             for opt in next(field['options']
                                             for field in demographic_fields if
                                             field['label'] == 'Please indicate your highest qualification')]

    ethnicity_options = [{'label': opt, 'value': opt}
                         for opt in next(field['options']
                                         for field in demographic_fields if
                                         field['label'] == 'What is your ethnicity?')]

    return gender_options, band_options, qualification_options, ethnicity_options


@dash_app.callback(
    [Output('gender-filter', 'value'),
     Output('ethnicity-filter', 'value'),
     Output('qualification-filter', 'value'),
     Output('band-filter', 'value')],
    [Input('clear-filters', 'n_clicks')],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    return None, None, None, None


#TODO: add HTML button for exporting PDF