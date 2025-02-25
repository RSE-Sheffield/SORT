from dash.dependencies import Input, Output
from dash import html, dcc
from .utils import (
    filter_survey_data,
    calculate_section_averages,
    create_section_figure,
    calculate_section_statistics,
    create_section_summary,
    create_demographic_chart,
)
from .constants import MATURITY_LEVELS, COLOUR_PALETTE

from .config import SECTIONS, DEMOGRAPHIC_FIELDS


def register_callbacks(dash_app):
    @dash_app.callback(
        Output("stored-data", "data"),
        [Input(f'{field["id"]}-filter', "value") for field in DEMOGRAPHIC_FIELDS],
    )
    def update_stored_data(*filter_values):

        all_responses = dash_app.initial_arguments.get("survey_responses", [])

        filters = {
            field["id"]: value
            for field, value in zip(DEMOGRAPHIC_FIELDS, filter_values)
            if value is not None
        }

        filtered_responses = filter_survey_data(all_responses, filters)

        section_averages = calculate_section_averages(filtered_responses)

        return {
            "section_averages": section_averages,
            "survey_responses": filtered_responses,
        }

    @dash_app.callback(
        [Output(f'{field["id"]}-filter', "options") for field in DEMOGRAPHIC_FIELDS],
        [Input("stored-data", "data")],
    )
    def update_filter_options(data):

        options = []

        for field in DEMOGRAPHIC_FIELDS:
            if field["id"] == "age":

                options.append([
                    {"label": opt, "value": opt}
                    for opt in ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"]
                ])
            else:

                options.append([
                    {"label": opt, "value": opt}
                    for opt in field["config"]["options"]
                ])

        return options

    # Clear filters callback
    @dash_app.callback(
        [Output(f'{field["id"]}-filter', "value") for field in DEMOGRAPHIC_FIELDS],
        [Input("clear-filters", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_filters(n_clicks):

        return [None] * len(DEMOGRAPHIC_FIELDS)

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

            # Calculate completion rate
            completed = sum(
                1
                for response in data["survey_responses"]
                if "fields" in response
                and "answers" in response["fields"]
                and len(response["fields"]["answers"]) >= 6
            )
            completion_rate = completed / total_responses * 100

            # Calculate average score
            all_scores = []
            for section in SECTIONS:
                section_stats = calculate_section_statistics(data, section["index"])
                if section_stats:
                    mean_score = float(
                        next(
                            stat["value"]
                            for stat in section_stats
                            if stat["statistic"] == "Mean Score"
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

    # Register section callbacks for each section
    for section in SECTIONS:
        # Section breakdown graph
        @dash_app.callback(
            Output(f'section-breakdown-{section["letter"].lower()}', "figure"),
            [Input("stored-data", "data")],
        )
        def update_section_breakdown(data, section=section):

            return create_section_figure(data, section["index"])

        # Section statistics
        @dash_app.callback(
            Output(f'section-{section["letter"].lower()}-stats', "data"),
            [Input("stored-data", "data")],
        )
        def update_section_stats(data, section=section):

            return calculate_section_statistics(data, section["index"])

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
                        create_section_summary(data, section["index"]),
                        dangerously_allow_html=True,
                    )
                ]
            )

    # Demographic chart callbacks
    for field in DEMOGRAPHIC_FIELDS:

        @dash_app.callback(
            Output(f'{field["id"]}-chart', "figure"), [Input("stored-data", "data")]
        )
        def update_demographic_chart(data, field=field):

            return create_demographic_chart(data, field["label"])

    # Ranking matrix callback
    @dash_app.callback(Output("ranking-matrix", "data"), [Input("stored-data", "data")])
    def update_ranking_matrix(data):

        if not data or "section_averages" not in data:
            return []

        return [
            {
                "survey": "Current Survey",
                **{
                    section["id"]: MATURITY_LEVELS[
                        int(data["section_averages"][section["id"]])
                    ]
                    for section in SECTIONS
                },
            }
        ]

    # Matrix styles callback
    @dash_app.callback(
        Output("ranking-matrix", "style_data_conditional"),
        [Input("stored-data", "data")],
    )
    def update_matrix_styles(data):

        if not data or "section_averages" not in data:
            return []

        styles = []
        for section in SECTIONS:
            if section["id"] in data["section_averages"]:
                level = MATURITY_LEVELS[int(data["section_averages"][section["id"]])]
                styles.append(
                    {
                        "if": {
                            "column_id": section["id"],
                            "filter_query": f'{{{section["id"]}}} = "{level}"',
                        },
                        "backgroundColor": COLOUR_PALETTE[
                            int(data["section_averages"][section["id"]])
                        ],
                        "color": "black" if level == "Early Progress" else "white",
                    }
                )

        return styles
