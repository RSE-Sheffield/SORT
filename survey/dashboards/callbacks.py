"""
Dash callbacks for the survey dashboard

Defines and registers the interactive callbacks of the dashboard's
functionality, including filtering, metrics calculation, visualisations,
and section summaries. All callbacks are registered to the provided dash_app instance.
"""

from dash.dependencies import Input, Output, State
from dash import html, dcc
from .utils import (
    filter_survey_data,
    calculate_section_averages,
    create_section_figure,
    calculate_section_statistics,
    create_section_summary,
    create_demographic_chart,
    get_maturity_level
)
from .constants import MATURITY_LEVELS, COLOUR_PALETTE


def register_callbacks(dash_app):
    sections = dash_app.sections
    demographic_fields = dash_app.demographic_fields

    @dash_app.callback(
        Output("stored-data", "data"),
        [Input(f'{field["id"]}-filter', "value") for field in demographic_fields],
    )
    def update_stored_data(*filter_values):
        all_responses = getattr(dash_app, 'survey_responses', [])

        filters = {
            field["id"]: value
            for field, value in zip(demographic_fields, filter_values)
            if value is not None
        }

        filtered_responses = filter_survey_data(all_responses, filters, dash_app)
        section_averages = calculate_section_averages(filtered_responses, dash_app)

        return {
            "section_averages": section_averages,
            "survey_responses": filtered_responses,
        }

    @dash_app.callback(
        [Output(f'{field["id"]}-filter', "options") for field in demographic_fields],
        [Input("stored-data", "data")],
    )
    def update_filter_options(data):
        options = []

        for field in demographic_fields:
            if field["id"] == "age":
                options.append([
                    {"label": opt, "value": opt}
                    for opt in ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"]
                ])
            else:
                options.append([
                    {"label": opt, "value": opt}
                    for opt in field["options"]
                ])

        return options

    # Clear filters callback
    @dash_app.callback(
        [Output(f'{field["id"]}-filter', "value") for field in demographic_fields],
        [Input("clear-filters", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_filters(n_clicks):
        return [None] * len(demographic_fields)

    # Metrics callbacks
    @dash_app.callback(
        [
            Output("total-responses", "children"),
            Output("completion-rate", "children"),
            Output("average-score", "children"),
        ],
        [Input("stored-data", "data")],
    )
    def update_metrics(data):
        if not data or "survey_responses" not in data:
            return "0", "0%", "0.0"

        try:
            total_responses = len(data["survey_responses"])
            if total_responses == 0:
                return "0", "0%", "0.0"

            completed = sum(
                1
                for response in data["survey_responses"]
                if "answers" in response and len(response["answers"]) >= len(sections)
            )

            completion_rate = completed / total_responses * 100

            all_scores = []

            for section in sections:
                section_stats = calculate_section_statistics(data, section["index"], dash_app)
                if section_stats:
                    mean_score = float(
                        next(
                            (stat["value"] for stat in section_stats if stat["statistic"] == "Mean Score"),
                            0
                        )
                    )
                    all_scores.append(mean_score)

            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

            return (
                f"{total_responses:,}",
                f"{completion_rate:.0f}%",
                f"{avg_score:.1f}",
            )

        except Exception as e:
            print(f"Error in update_metrics: {str(e)}")
            return "0", "0%", "0.0"

    for section in sections:
        # Section breakdown graph
        @dash_app.callback(
            Output(f'section-breakdown-{section["letter"].lower()}', "figure"),
            [Input("stored-data", "data")],
        )
        def update_section_breakdown(data, section=section):
            return create_section_figure(data, section["index"], dash_app)

        # Section statistics
        @dash_app.callback(
            Output(f'section-{section["letter"].lower()}-stats', "data"),
            [Input("stored-data", "data")],
        )
        def update_section_stats(data, section=section):
            return calculate_section_statistics(data, section["index"], dash_app)

        # Section summary
        @dash_app.callback(
            Output(f'section-summary-{section["letter"].lower()}', "children"),
            [Input("stored-data", "data")],
        )
        def update_section_summary(data, section=section):
            if not data:
                return "No data available"
            return html.Div(
                [
                    dcc.Markdown(
                        create_section_summary(data, section["index"], dash_app),
                        dangerously_allow_html=True,
                    )
                ]
            )

    # Register callbacks
    for i, field in enumerate(demographic_fields):
        @dash_app.callback(
            Output(f'{field["id"]}-chart', "figure"),
            [Input("stored-data", "data")]
        )
        def update_demographic_chart(data, _field=field):
            result = create_demographic_chart(data, _field["label"], dash_app)
            return result

    @dash_app.callback(
        Output("ranking-matrix", "data"),
        [Input("stored-data", "data")]
    )
    def update_ranking_matrix(data):
        if not data or "section_averages" not in data:
            return []

        sections = dash_app.sections

        matrix_data = {
            "survey": "Current Survey"
        }

        for section in sections:
            section_id = section["id"]
            section_avg = data["section_averages"].get(section_id, 0)

            matrix_data[section_id] = get_maturity_level(section_avg)

        return [matrix_data]

    # Matrix styles callback
    @dash_app.callback(
        Output("ranking-matrix", "style_data_conditional"),
        [Input("stored-data", "data")],
    )
    def update_matrix_styles(data):
        if not data or "section_averages" not in data:
            return []

        styles = []
        for section in sections:
            if section["id"] in data["section_averages"]:
                level_idx = int(min(4, max(0, data["section_averages"][section["id"]])))
                level = MATURITY_LEVELS[level_idx]
                styles.append(
                    {
                        "if": {
                            "column_id": section["id"],
                            "filter_query": f'{{{section["id"]}}} = "{level}"',
                        },
                        "backgroundColor": COLOUR_PALETTE[level_idx],
                        "color": "black" if level == "Early Progress" else "white",
                    }
                )

        return styles

    # Update comments callback
    @dash_app.callback(
        [
            Output(f"toggle-comments-{section['letter'].lower()}", "children") for section in sections
        ] +
        [
            Output(f"comments-panel-{section['letter'].lower()}", "children") for section in sections
        ],
        [Input("stored-data", "data")],
    )
    def update_comments(data):

        if not data or "survey_responses" not in data:
            return [f"Section {s['letter']} Comments (0)" for s in sections] + ["No comments available."] * len(
                sections)

        updated_labels = []
        updated_contents = []

        for section in sections:
            section_index = section["index"]

            section_comments = []

            for response in data["survey_responses"]:
                if "answers" in response and isinstance(response["answers"], list):

                    if len(response["answers"]) > section_index:
                        section_answer = response["answers"][section_index]
                        if isinstance(section_answer, list) and len(section_answer) > 1:
                            comment = section_answer[1]
                            if isinstance(comment, str) and comment.strip():
                                section_comments.append(comment.strip())

            num_comments = len(section_comments)
            label_text = f"Additional Comments: ({num_comments})"
            updated_labels.append(label_text)

            if section_comments:

                comment_items = []
                for i, comment in enumerate(section_comments, 1):
                    comment_items.append(
                        html.Div([
                            html.Span(f"{i}. ",
                                      style={
                                          "marginRight": "5px",
                                          "float": "left",
                                          "width": "25px"
                                      }),
                            html.Div(comment,
                                     style={
                                         "overflow": "auto",
                                         "wordWrap": "break-word",
                                         "wordBreak": "break-word",
                                         "display": "block",
                                         "marginLeft": "30px"
                                     })
                        ], style={"marginBottom": "15px", "clear": "both"})
                    )

                updated_contents.append(html.Div(comment_items))
            else:
                updated_contents.append("No additional comments recorded.")

        return updated_labels + updated_contents

    for section in sections:

        def create_toggle_callback(section_id):
            @dash_app.callback(
                Output(f"collapse-comments-{section_id}", "is_open"),
                [Input(f"comments-card-{section_id}", "n_clicks"),
                 Input(f"toggle-comments-{section_id}", "n_clicks")],
                [State(f"collapse-comments-{section_id}", "is_open")],
                prevent_initial_call=True,
            )
            def toggle_callback(card_clicks, header_clicks, is_open):
                # toggle whenever either the card or the header is clicked
                if card_clicks or header_clicks:
                    return not is_open
                return is_open

            return toggle_callback

        section_letter = section['letter'].lower()
        create_toggle_callback(section_letter)
