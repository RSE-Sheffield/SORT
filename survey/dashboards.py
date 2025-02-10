from django_plotly_dash import DjangoDash
from dash import html, dcc, dash_table, Input, Output
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from collections import defaultdict

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
                      external_scripts=['https://cdn.plot.ly/plotly-2.20.0.min.js'] # This line is needed for graphs
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
        4: "#2c7bb6"   # colour-blind safe dark blue
    }

    return categories[score_int], colours[score_int]

# Define the dashboard layout

dash_app.layout = html.Div([
    dcc.Store(id='stored-data', storage_type='memory'),

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
                            }
                            ),
                    html.H3(id='total-responses',
                            style={
                                'fontFamily': THEME['font_family'],
                                'color': THEME['primary'],
                                'marginBottom': '0px',
                                'fontWeight': 'normal',
                                'textAlign': 'center',
                            }
                            )
                ])
            ])
        ], width=4),

        # Completion Rate
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Completion Rate",
                            style={
                                'fontFamily': THEME['font_family'],
                                'color': THEME['text_color'],
                                'marginBottom': '8px',
                                'textAlign': 'center'
                            }
                            ),
                    html.H3(id='completion-rate',
                            style={
                                'fontFamily': THEME['font_family'],
                                'color': THEME['primary'],
                                'marginBottom': '0px',
                                'fontWeight': 'normal',
                                'textAlign': 'center'
                            }
                            )
                ])
            ])
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
                            }
                            ),
                    html.H3(id='average-score',
                            style={
                                'fontFamily': THEME['font_family'],
                                'color': THEME['primary'],
                                'marginBottom': '0px',
                                'fontWeight': 'normal',
                                'textAlign': 'center'
                            }
                            )
                ])
            ])
        ], width=4)
    ], className='g-4', style={'marginTop': '20px', 'marginBottom': '20px'}),

    dbc.Container([

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label('Filter by Gender:',
                          style={
                              'fontFamily': THEME['font_family'],
                              'marginRight': '10px',
                              'color': THEME['text_color']
                          }),
                dcc.Dropdown(
                    id='gender-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Female', 'value': 'female'},
                        {'label': 'Male', 'value': 'male'}
                    ],
                    value='all',
                    clearable=False,
                    style={
                        'width': '200px',
                        'fontFamily': THEME['font_family']
                    }
                )
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'marginBottom': '20px'
            })
        ], width=12)
    ], className='g-4'),

        # Selector
        # dbc.Row([
        #     dbc.Col([
        #         html.Div([
        #             html.Label('Select Response:', style={
        #                 'fontFamily': THEME['font_family'],
        #                 'marginRight': '10px'
        #             }),
        #             dcc.Dropdown(
        #                 id='response-selector',
        #                 options=[
        #                     {'label': 'Average', 'value': 'average'}
        #                 ],
        #                 value='average',
        #                 clearable=False,
        #                 style={
        #                     'width': '100px',
        #                     'fontFamily': THEME['font_family']
        #                 }
        #             )
        #         ], style={
        #             'display': 'flex',
        #             'alignItems': 'center',
        #             'justifyContent': 'right',
        #             'marginTop': '5px'
        #         })
        #     ])
        # ]),

        dbc.Row([
            dbc.Col([
                html.H2(style={
                            'fontFamily': THEME['font_family'],
                            'colour': THEME['text_color'],
                            'fontWeight': 'normal',
                            'marginBottom': '0px',
                            'textAlign': 'center'
                        })
            ])
        ]),

        dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("Consent Responses",
                                    style={
                                        'fontFamily': THEME['font_family'],
                                        'color': THEME['text_color'],
                                        'marginBottom': '0px'
                                    })
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id='consent-chart',
                                    config={'displayModeBar': False}
                                )
                            ])
                        ], style={
                            'borderRadius': '10px',
                            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
                        })
                    ], width=12)
                ]),

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
                ], style={'marginTop': '20px', 'marginBottom': '20px'}),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Gender Distribution",
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
        ]),

        # dbc.Row([
        #     dbc.Col([
        #         html.Div([
        #             html.H5('Ranking Matrix',
        #                     style={
        #                         'fontFamily': THEME['font_family'],
        #                         'fontWeight': 'normal',
        #                         'padding': '20px',
        #                     }),
        #             dash_table.DataTable(
        #                 id='ranking-matrix',
        #                 columns=[
        #                     {'name': '', 'id': 'survey', 'width': '15%'},
        #                     {'name': 'Releasing Potential', 'id': 'releasing_potential', 'width': '17%'},
        #                     {'name': 'Embedding Research', 'id': 'embedding_research', 'width': '17%'},
        #                     {'name': 'Linkages and Leadership', 'id': 'linkages_leadership', 'width': '17%'},
        #                     {'name': 'Inclusive Research', 'id': 'inclusive_research', 'width': '17%'},
        #                     {'name': 'Digital Capability', 'id': 'digital_capability', 'width': '17%'}
        #                 ],
        #                 style_table={
        #                     'width': '100%',
        #                     'borderRadius': '1rem',
        #                     'boxShadow': '1px 1px 5px rgba(0, 0, 0, 0.2)',
        #                 },
        #                 style_cell={
        #                     'textAlign': 'center',
        #                     'padding': '10px',
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '14px',
        #                     'border': '1px solid #ddd',
        #                     'minWidth': '0px',
        #                     'maxWidth': 'none',
        #                     'whiteSpace': 'normal',
        #                     'height': 'auto'
        #                 },
        #                 style_header={
        #                     'backgroundColor': 'white',
        #                     'fontWeight': 'semi-bold',
        #                     'border': '1px solid #ddd',
        #                     'whiteSpace': 'normal',
        #                     'height': 'auto'
        #                 },
        #                 css=[{
        #                     'selector': '.dash-table-container',
        #                     'rule': 'width: 100%; max-width: 100%;'
        #                 }],
        #                 fill_width=True
        #             )
        #         ], style={'padding': '0px'})
        #     ])
        # ]),
        #
        # # Legend for Ranking Matrix
        # dbc.Row([
        #     dbc.Col([
        #         html.Div([
        #             html.Div([
        #                 html.Span(style={
        #                     'display': 'inline-block',
        #                     'width': '15px',
        #                     'height': '15px',
        #                     'backgroundColor': '#d73027',
        #                     'marginRight': '5px',
        #                     'verticalAlign': 'middle'
        #                 }),
        #                 html.Span('Not yet planned', style={
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '12px',
        #                     'marginRight': '10px',
        #                     'verticalAlign': 'middle'
        #                 })
        #             ], style={'display': 'inline-block', 'marginRight': '10px'}),
        #             html.Div([
        #                 html.Span(style={
        #                     'display': 'inline-block',
        #                     'width': '15px',
        #                     'height': '15px',
        #                     'backgroundColor': '#fc8d59',
        #                     'marginRight': '5px',
        #                     'verticalAlign': 'middle'
        #                 }),
        #                 html.Span('Planned', style={
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '12px',
        #                     'marginRight': '10px',
        #                     'verticalAlign': 'middle'
        #                 })
        #             ], style={'display': 'inline-block', 'marginRight': '10px'}),
        #             html.Div([
        #                 html.Span(style={
        #                     'display': 'inline-block',
        #                     'width': '15px',
        #                     'height': '15px',
        #                     'backgroundColor': '#fee08b',
        #                     'marginRight': '5px',
        #                     'verticalAlign': 'middle'
        #                 }),
        #                 html.Span('Early progress', style={
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '12px',
        #                     'marginRight': '10px',
        #                     'verticalAlign': 'middle'
        #                 })
        #             ], style={'display': 'inline-block', 'marginRight': '10px'}),
        #             html.Div([
        #                 html.Span(style={
        #                     'display': 'inline-block',
        #                     'width': '15px',
        #                     'height': '15px',
        #                     'backgroundColor': '#91cf60',
        #                     'marginRight': '5px',
        #                     'verticalAlign': 'middle'
        #                 }),
        #                 html.Span('Substantial Progress', style={
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '12px',
        #                     'marginRight': '10px',
        #                     'verticalAlign': 'middle'
        #                 })
        #             ], style={'display': 'inline-block', 'marginRight': '10px'}),
        #             html.Div([
        #                 html.Span(style={
        #                     'display': 'inline-block',
        #                     'width': '15px',
        #                     'height': '15px',
        #                     'backgroundColor': '#1a9850',
        #                     'marginRight': '5px',
        #                     'verticalAlign': 'middle'
        #                 }),
        #                 html.Span('Established', style={
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '12px',
        #                     'verticalAlign': 'middle'
        #                 })
        #             ], style={'display': 'inline-block'})
        #         ], style={
        #             'textAlign': 'center',
        #             'width': '100%',
        #             'marginTop': '20px'
        #         })
        #     ])
        # ]),
        #
        #
        # # Table
        # dbc.Row([
        #     dbc.Col([
        #         html.Div([
        #             # Title in card header style
        #             html.Div([
        #                 html.H5('Summary Statistics',
        #                        style={
        #                            'fontFamily': THEME['font_family'],
        #                            'fontWeight': 'normal',
        #                            'padding': '20px',
        #                        })
        #             ]),
        #
        #             dash_table.DataTable(
        #                 id='section-table',
        #                 columns=[
        #                     {'name': 'Section', 'id': 'Section', 'width': '50%'},
        #                     {'name': 'Average Score', 'id': 'Average Score',
        #                      'type': 'numeric', 'format': {'specifier': '.1f'}, 'width': '50%'}
        #                 ],
        #                 style_table={
        #                     'width': '100%',
        #                     'borderRadius': '1rem',
        #                     'boxShadow': '1px 1px 5px rgba(0, 0, 0, 0.2)',
        #                 },
        #                 style_cell={
        #                     'textAlign': 'center',
        #                     'padding': '10px',
        #                     'fontFamily': THEME['font_family'],
        #                     'fontSize': '14px',
        #                     'border': '1px solid #ddd',
        #                     'minWidth': '0px',
        #                     'maxWidth': 'none',
        #                     'whiteSpace': 'normal',
        #                     'height': 'auto'
        #                 },
        #                 style_header={
        #                     'backgroundColor': 'white',
        #                     'fontWeight': 'semi-bold',
        #                     'border': '1px solid #ddd',
        #                     'whiteSpace': 'normal',
        #                     'height': 'auto'
        #                 },
        #                 style_data={
        #                     'backgroundColor': 'white',
        #                     'border': '1px solid #ddd'
        #                 },
        #                 style_data_conditional=[{
        #                     'if': {'row_index': 'odd'},
        #                     'backgroundColor': THEME['bg_color']
        #                 }],
        #                 css=[{
        #                     'selector': '.dash-table-container',
        #                     'rule': 'width: 100%; max-width: 100%;'
        #                 }],
        #                 fill_width=True
        #             )
        #         ], style={'padding': '0px'})
        #     ])
        # ]),
        #
    ], fluid=True)
])


@dash_app.callback(
    Output('stored-data', 'data'),
    Input('stored-data', 'data')
)
def initialise_data(_):
    # Get all survey responses
    all_responses = dash_app.initial_arguments.get('survey_responses', [])

    # Calculate averages across all responses
    section_averages = {}
    for section in ['releasing_potential', 'embedding_research', 'linkages_leadership', 'inclusive_research', 'digital_capability']:
        section_scores = [
            np.mean(list(response['fields']['answers'][section].values())[:-1])  # Exclude the text field
            for response in all_responses
        ]
        section_averages[section] = np.mean(section_scores)

    return {
        'section_averages': section_averages,
        'survey_responses': all_responses
    }

@dash_app.callback(
    Output('section-table', 'data'),
    [Input('stored-data', 'data')]
)
def update_table(data):
    if data and 'section_averages' in data:
        # Define the specific order of sections
        section_order = [
            'releasing_potential',
            'embedding_research',
            'linkages_leadership',
            'inclusive_research',
            'digital_capability'
        ]

        # Create DataFrame and sort based on the predefined order
        df = pd.DataFrame([
            {'Section': k.replace('_', ' ').title(), 'Average Score': data['section_averages'][k]}
            for k in section_order
        ])

        return df.to_dict('records')
    return []


@dash_app.callback(
    Output('ranking-matrix', 'data'),
    [Input('stored-data', 'data')]
)
def update_ranking_matrix(data):

    if data and 'section_averages' in data:
        matrix_data = [{
            'survey': 'Current Survey',
            'releasing_potential': get_category_and_colour(data['section_averages']['releasing_potential'])[0],
            'embedding_research': get_category_and_colour(data['section_averages']['embedding_research'])[0],
            'linkages_leadership': get_category_and_colour(data['section_averages']['linkages_leadership'])[0],
            'inclusive_research': get_category_and_colour(data['section_averages']['inclusive_research'])[0],
            'digital_capability': get_category_and_colour(data['section_averages']['digital_capability'])[0]
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
        'Not yet planned': '#d73027',
        'Planned': '#fc8d59',
        'Early progress': '#fee08b',
        'Substantial Progress': '#91cf60',
        'Established': '#1a9850'
    }

    for section in ['releasing_potential', 'embedding_research', 'linkages_leadership',
                    'inclusive_research', 'digital_capability']:
        if section in data['section_averages']:
            category = get_category_and_colour(data['section_averages'][section])[0]
            styles.append({
                'if': {
                    'column_id': section,
                    'filter_query': f'{{{section}}} = "{category}"'
                },
                'backgroundColor': categories[category],
                'color': 'white' if category != 'Early progress' else 'black'
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
        # Total Responses
        total_responses = len(data['survey_responses'])

        # Completion Rate
        completed = sum(1 for response in data['survey_responses']
                        if all(section in response['fields']['answers']
                               for section in ['releasing_potential', 'embedding_research',
                                               'linkages_leadership', 'inclusive_research',
                                               'digital_capability']))
        completion_rate = (completed / total_responses * 100) if total_responses > 0 else 0

        # Average Score
        all_scores = []
        for response in data['survey_responses']:
            for section in ['releasing_potential', 'embedding_research',
                            'linkages_leadership', 'inclusive_research',
                            'digital_capability']:
                if section in response['fields']['answers']:
                    scores = [v for k, v in response['fields']['answers'][section].items()
                              if isinstance(v, (int, float))]
                    if scores:
                        all_scores.extend(scores)

        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        return f"{total_responses}", f"{completion_rate:.0f}%", f"{avg_score:.1f}"

    except Exception as e:
        return "0", "0%", "0.0"

@dash_app.callback(
    Output('consent-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_consent_chart(data):
    if not data or 'survey_responses' not in data:
        return {}

    consent_counts = {
        'q1': {'agree': 0, 'disagree': 0},
        'q2': {'agree': 0, 'disagree': 0},
        'q3': {'agree': 0, 'disagree': 0},
        'q4': {'agree': 0, 'disagree': 0}
    }

    total_responses = len(data['survey_responses'])

    for response in data['survey_responses']:
        if 'answers' in response['fields'] and 'consent' in response['fields']['answers']:
            consent_data = response['fields']['answers']['consent']
            for question in ['q1', 'q2', 'q3', 'q4']:
                if question in consent_data:
                    if consent_data[question]:
                        consent_counts[question]['agree'] += 1
                    else:
                        consent_counts[question]['disagree'] += 1
    questions = ['Question ' + q[1] for q in sorted(consent_counts.keys())]
    agreed = [consent_counts[q]['agree'] for q in sorted(consent_counts.keys())]
    disagreed = [consent_counts[q]['disagree'] for q in sorted(consent_counts.keys())]

    agreed_pct = [f"{(a / total_responses * 100):.1f}%" for a in agreed]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=questions,
        x=agreed,
        name='Agreed',
        orientation='h',
        marker_color='#2c7bb6',  # colour-blind safe blue
        text=agreed_pct,
        textposition='auto',
    ))

    # Update layout
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

def create_section_figure(data, section, section_prefix, exclude_suffix=None):
    if not data or 'survey_responses' not in data:
        return {}

    responses = defaultdict(list)

    for response in data['survey_responses']:
        if ('fields' in response and 'answers' in response['fields'] and
                section in response['fields']['answers']):
            section_data = response['fields']['answers'][section]
            for q_id, score in section_data.items():
                if isinstance(score, (int, float)) and q_id.startswith(section_prefix):
                    if exclude_suffix and not q_id.endswith(exclude_suffix):
                        responses[q_id].append(score)
                    elif not exclude_suffix:
                        responses[q_id].append(score)

    fig = go.Figure()
    question_ids = sorted(responses.keys())

    for score in range(5):
        y_data = []
        for q_id in question_ids:
            count = sum(1 for s in responses[q_id] if int(np.floor(s)) == score)
            y_data.append(count)

        category, color = get_category_and_colour(score)
        fig.add_trace(go.Bar(
            x=question_ids,
            y=y_data,
            name=category,
            marker_color=color,
            text=[f"{count}" if count > 0 else "" for count in y_data],
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
            title="Questions",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            tickangle=45,
            automargin=True,
            tickfont=dict(
                family=THEME['font_family'],
                size=12
            ),
            title_font=dict(
                family=THEME['font_family'],
                size=12
            )
        ),
        yaxis=dict(
            title="Number of Responses",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            tickfont=dict(
                family=THEME['font_family'],
                size=12
            ),
            title_font=dict(
                family=THEME['font_family'],
                size=12
            )
        )
    )
    return fig

@dash_app.callback(
    Output('section-breakdown-a', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_a(data):
    return create_section_figure(data, 'releasing_potential', 'a', '23')

@dash_app.callback(
    Output('section-breakdown-b', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_b(data):
    return create_section_figure(data, 'embedding_research', 'b', '6')

@dash_app.callback(
    Output('section-breakdown-c', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_c(data):
    return create_section_figure(data, 'linkages_leadership', 'c', '5')

@dash_app.callback(
    Output('section-breakdown-d', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_d(data):
    return create_section_figure(data, 'inclusive_research', 'd', '5')

@dash_app.callback(
    Output('section-breakdown-e', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_e(data):
    return create_section_figure(data, 'digital_capability', 'e')

@dash_app.callback(
    Output('gender-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_gender_chart(data):

    if not data or 'survey_responses' not in data:
        return {}

    gender_counts = defaultdict(int)

    for idx, response in enumerate(data['survey_responses']):

        # Check for gender in the answers field
        if 'answers' in response['fields'] and 'gender' in response['fields']['answers']:
            gender = response['fields']['answers']['gender'].title()
            gender_counts[gender] += 1


    fig = go.Figure(data=[go.Pie(
        labels=list(gender_counts.keys()),
        values=list(gender_counts.values()),
        hole=0,
        marker=dict(
            colors=['#f768a1', '#2c7bb6']
        ),
        textinfo='value+percent',
        textfont=dict(
            family=THEME['font_family'],
            size=12
        ),
        textposition='auto',
    )])

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
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
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(
                family=THEME['font_family'],
                size=15
            )
        )
    )

    return fig