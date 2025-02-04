
from django_plotly_dash import DjangoDash
from dash import html, dcc, dash_table, Input, Output
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np

# Define theme colours
THEME = {
    'primary': '#440099',
    'primary_bg': '#DACCEB',
    'btn_primary': '#6933AD',
    'text_color': '#555',
    'font_family': 'Source Sans Pro, sans-serif',
    'bg_color': '#f8f9fa'
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
        0: "#d73027",  # Red for Not yet planned
        1: "#fc8d59",  # Orange for Planned
        2: "#fee08b",  # Yellow for Early progress
        3: "#91cf60",  # Light green for Substantial Progress
        4: "#1a9850"  # Dark green for Established
    }

    return categories[score_int], colours[score_int]

dash_app.layout = html.Div([
    dcc.Store(id='stored-data', storage_type='memory'),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label('Select Response:', style={
                        'fontFamily': THEME['font_family'],
                        'marginRight': '10px'
                    }),
                    dcc.Dropdown(
                        id='response-selector',
                        options=[
                            {'label': 'Average', 'value': 'average'}
                        ],
                        value='average',
                        clearable=False,
                        style={
                            'width': '100px',
                            'fontFamily': THEME['font_family']
                        }
                    )
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'right',
                    'marginTop': '5px'
                })
            ])
        ]),

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
                html.Div([
                    html.H5('Ranking Matrix',
                            style={
                                'fontFamily': THEME['font_family'],
                                'fontWeight': 'normal',
                                'padding': '20px',
                            }),
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
                            'boxShadow': '1px 1px 5px rgba(0, 0, 0, 0.2)',
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'fontFamily': THEME['font_family'],
                            'fontSize': '14px',
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
                        },
                        css=[{
                            'selector': '.dash-table-container',
                            'rule': 'width: 100%; max-width: 100%;'
                        }],
                        fill_width=True
                    )
                ], style={'padding': '0px'})
            ])
        ]),

        # Legend for Ranking Matrix
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Span(style={
                            'display': 'inline-block',
                            'width': '15px',
                            'height': '15px',
                            'backgroundColor': '#d73027',
                            'marginRight': '5px',
                            'verticalAlign': 'middle'
                        }),
                        html.Span('Not yet planned', style={
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
                            'backgroundColor': '#fc8d59',
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
                            'backgroundColor': '#fee08b',
                            'marginRight': '5px',
                            'verticalAlign': 'middle'
                        }),
                        html.Span('Early progress', style={
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
                            'backgroundColor': '#91cf60',
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
                            'backgroundColor': '#1a9850',
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
                    'width': '100%',
                    'marginTop': '20px'
                })
            ])
        ]),


        # Table
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Title in card header style
                    html.Div([
                        html.H5('Summary Statistics',
                               style={
                                   'fontFamily': THEME['font_family'],
                                   'fontWeight': 'normal',
                                   'padding': '20px',
                               })
                    ]),

                    dash_table.DataTable(
                        id='section-table',
                        columns=[
                            {'name': 'Section', 'id': 'Section', 'width': '50%'},
                            {'name': 'Average Score', 'id': 'Average Score',
                             'type': 'numeric', 'format': {'specifier': '.1f'}, 'width': '50%'}
                        ],
                        style_table={
                            'width': '100%',
                            'borderRadius': '1rem',
                            'boxShadow': '1px 1px 5px rgba(0, 0, 0, 0.2)',
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px',
                            'fontFamily': THEME['font_family'],
                            'fontSize': '14px',
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
                        },
                        style_data={
                            'backgroundColor': 'white',
                            'border': '1px solid #ddd'
                        },
                        style_data_conditional=[{
                            'if': {'row_index': 'odd'},
                            'backgroundColor': THEME['bg_color']
                        }],
                        css=[{
                            'selector': '.dash-table-container',
                            'rule': 'width: 100%; max-width: 100%;'
                        }],
                        fill_width=True
                    )
                ], style={'padding': '0px'})
            ])
        ]),

        dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5('Section Breakdown',
                               style={
                                   'fontFamily': THEME['font_family'],
                                   'fontWeight': 'normal',
                                   'padding': '20px',
                               }),
                        dcc.Graph(
                            figure={},
                            id='section-breakdown-chart',
                            config={'displayModeBar': False},
                        )
                    ], style={'marginTop': '5px'})
                ])
        ]),
    ], fluid=True)
])




@dash_app.callback(
    [Output('stored-data', 'data'),
     Output('response-selector', 'options')],
    [Input('response-selector', 'value')]
)
def initialise_data(selected_response):
    # Assume dash_app.initial_arguments contains all survey responses
    all_responses = dash_app.initial_arguments.get('survey_responses', [])

    # Populate dropdown options
    response_options = [
        {'label': 'Average', 'value': 'average'}
    ]
    response_options.extend([
        {'label': f'Response {response["pk"]}', 'value': str(response["pk"])}
        for response in all_responses
    ])

    # If no specific response is selected or 'average' is chosen
    if selected_response == 'average' or not selected_response:
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
            'survey_responses': all_responses  # Add this line
        }, response_options

    # If a specific response is selected
    else:
        selected_response_data = next(
            (response for response in all_responses if str(response['pk']) == selected_response),
            None
        )

        if selected_response_data:
            section_averages = {}
            for section in ['releasing_potential', 'embedding_research', 'linkages_leadership', 'inclusive_research', 'digital_capability']:
                # For a single response, take the mean of its numerical answers
                section_scores = list(selected_response_data['fields']['answers'][section].values())[:-1]
                section_averages[section] = np.mean(section_scores)

            return {
                'section_averages': section_averages,
                'survey_responses': all_responses
            }, response_options

    # Fallback
    return {}, response_options

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
    print("\n=== Matrix Debug ===")
    print("Creating matrix with data:", data)

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
    Output('section-breakdown-chart', 'figure'),
    [Input('stored-data', 'data')]
)
def update_section_breakdown_chart(data):
    if not data:
        return {}

    df = pd.DataFrame([
        {'Section': k.replace('_', ' ').title(), 'Average Score': v}
        for k, v in data['section_averages'].items()
    ]).sort_values(by='Average Score', ascending=False)

    figure = {
        'data': [{
            'type': 'bar',
            'x': df['Section'].tolist(),
            'y': df['Average Score'].tolist(),
            'marker': {'color': 'rgb(26, 118, 255)'}
        }],
        'layout': {
            'height': 400,
            'xaxis': {'title': 'Section'},
            'yaxis': {'title': 'Average Score'},
            'margin': {'l': 50, 'r': 50, 't': 30, 'b': 50},
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white'
        }
    }

    return figure