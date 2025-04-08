"""
Utility functions for survey the data. It includes functions for filtering, demographic analysis,
section summarising, and creating charts to display the results and maturity levels
"""

import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
from scipy import stats
from .constants import MATURITY_LEVELS, GRAPH_LAYOUT, THEME, COLOUR_PALETTE


def get_age_group(age):
    """
    Utility function to transform the age category into groups
    """
    try:
        if age is None or age == "" or age == "Prefer not to say":
            return "Not Specified"

        age_num = int(float(age.strip()))

        if age_num < 25:
            return "Under 25"
        elif age_num < 35:
            return "25-34"
        elif age_num < 45:
            return "35-44"
        elif age_num < 55:
            return "45-54"
        elif age_num < 65:
            return "55-64"
        else:
            return "65+"
    except (ValueError, TypeError, AttributeError):
        return "Not Specified"


def get_section_questions(section_idx, app):
    """
    Get questions for a section from the survey stored in the app
    """
    try:
        section = app.sections[section_idx]
        section_config = section["config"]
        section_letter = section["letter"]

        # Get the likert field from the section
        likert_field = next(
            (field for field in section_config["fields"] if field["type"] == "likert"),
            None
        )

        if not likert_field:
            return {}

        # Create questions dictionary
        questions = {}
        for i, text in enumerate(likert_field.get("sublabels", [])):
            q_id = f"{section_letter}{i + 1}"
            questions[q_id] = text

        return questions
    except Exception as e:
        print(f"Error in get_section_questions: {str(e)}")
        return {}


def process_section_data(response, section_idx, app=None):
    """
    Process and extract section data from a response
    Returns a list of answer values for the section
    """
    try:
        original_index = section_idx
        if app and section_idx < len(app.sections):
            section = app.sections[section_idx]
            original_index = section.get("original_index", section_idx + 1) - 1

        if 'answers' in response and len(response['answers']) > original_index:
            section_data = response['answers'][original_index]

            if isinstance(section_data, list) and section_data:
                return section_data[0]

            return []
    except (IndexError, KeyError) as e:
        print(f"Error processing section data: {str(e)}")

    return []


def validate_score(score, min_val=0, max_val=4):

    try:
        if isinstance(score, str) and score.strip().isdigit():
            numeric_score = float(score)
            return min_val <= numeric_score <= max_val, numeric_score
        elif isinstance(score, (int, float)):
            return min_val <= score <= max_val, float(score)
        return False, None
    except (ValueError, TypeError):
        return False, None


def calculate_section_statistics(data, section_idx, app):

    all_scores = []

    if not data or "survey_responses" not in data:
        return []

    for response in data["survey_responses"]:
        try:
            section_data = process_section_data(response, section_idx, app)


            for score in section_data:
                is_valid, numeric_score = validate_score(score)
                if is_valid:
                    all_scores.append(numeric_score)

        except Exception as e:
            print(f"Error processing response for statistics: {str(e)}")
            continue

    if not all_scores:
        return [
            {"statistic": "Mean Score", "value": "0.0"},
            {"statistic": "Minimum", "value": "0.0"},
            {"statistic": "Maximum", "value": "0.0"},
            {"statistic": "Mode", "value": "0.0"}
        ]

    try:
        mode_result = stats.mode(all_scores, keepdims=False)
        mode_value = mode_result[0]

        return [
            {"statistic": "Mean Score", "value": f"{np.mean(all_scores):.1f}"},
            {"statistic": "Minimum", "value": f"{min(all_scores):.1f}"},
            {"statistic": "Maximum", "value": f"{max(all_scores):.1f}"},
            {"statistic": "Mode", "value": f"{mode_value:.1f}"}
        ]
    except Exception as e:
        print(f"Error calculating statistics: {str(e)}")
        return []


def get_maturity_level(score):

    score_int = int(np.floor(score))
    score_int = max(0, min(4, score_int))
    return MATURITY_LEVELS[score_int]


def filter_survey_data(survey_responses, filters, dash_app):

    if not filters:
        return survey_responses

    filtered_responses = []
    demographic_fields = dash_app.demographic_fields

    demographic_section_idx = None
    for idx, section in enumerate(dash_app.survey.survey_config.get("sections", [])):
        if section.get("type") == "demographic":
            demographic_section_idx = idx
            break

    if demographic_section_idx is None:
        return survey_responses

    field_positions = {}
    for field in demographic_fields:
        field_positions[field["id"]] = field["index"]

    for response in survey_responses:
        if 'answers' not in response or len(response['answers']) <= demographic_section_idx:
            continue

        try:
            demographic_data = response['answers'][demographic_section_idx]

            match = True
            for filter_id, filter_value in filters.items():
                field = next((f for f in demographic_fields if f["id"] == filter_id), None)
                if not field:
                    continue

                position = field["index"]

                # Ensure position is valid
                if position >= len(demographic_data):
                    match = False
                    break

                if filter_id.lower == 'age' and 'transform' in field:
                    age_group = field["transform"](demographic_data[position])
                    if age_group != filter_value:
                        match = False
                        break
                elif demographic_data[position] != filter_value:
                    match = False
                    break

            if match:
                filtered_responses.append(response)

        except (IndexError, TypeError) as e:
            print(f"Error filtering response: {e}")
            continue

    return filtered_responses


def calculate_section_averages(responses, app):
    section_averages = {}
    sections = app.sections

    for section in sections:
        section_scores = []
        section_idx = section["index"]
        section_id = section["id"]

        for response in responses:
            if "answers" in response:
                try:
                    section_data = process_section_data(response, section_idx, app)
                    valid_scores = []

                    for score in section_data:
                        is_valid, numeric_score = validate_score(score)
                        if is_valid:
                            valid_scores.append(numeric_score)

                    if valid_scores:
                        section_scores.append(np.mean(valid_scores))
                except (IndexError, KeyError, TypeError) as e:
                    print(f"Error calculating section average: {e}")
                    continue

        section_averages[section_id] = (
            np.mean(section_scores) if section_scores else 0
        )

    return section_averages


def create_section_summary(data, section_idx, app):

    if not data or "survey_responses" not in data:
        return ""

    questions = get_section_questions(section_idx, app)
    if not questions:
        return ""

    section = app.sections[section_idx]
    section_letter = section["letter"]
    section_title = section["title"]

    question_scores = {}
    for q_id in questions:
        scores = []
        for response in data["survey_responses"]:
            section_data = process_section_data(response, section_idx, app)
            q_idx = int(q_id[1:]) - 1

            if 0 <= q_idx < len(section_data):
                is_valid, score = validate_score(section_data[q_idx])
                if is_valid:
                    scores.append(int(score))  # Convert to int for summary analysis

        if scores:
            question_scores[q_id] = scores

    if not question_scores:
        return ""

    all_scores = [s for scores in question_scores.values() for s in scores]
    if not all_scores:
        return ""

    section_avg = np.mean(all_scores)
    maturity_level = get_maturity_level(section_avg)

    question_analysis = {}
    for q_id, scores in question_scores.items():
        high_scores = sum(1 for s in scores if s >= 3)
        low_scores = sum(1 for s in scores if s <= 2)
        total_scores = len(scores)

        if total_scores > 0:
            question_analysis[q_id] = {
                "high_prop": (high_scores / total_scores) * 100,
                "low_prop": (low_scores / total_scores) * 100,
                "avg_score": np.mean(scores),
            }

    high_performing = sorted(
        [
            (q, analysis)
            for q, analysis in question_analysis.items()
            if analysis["high_prop"] >= 50
        ],
        key=lambda x: x[1]["high_prop"],
        reverse=True,
    )[:5]

    low_performing = sorted(
        [
            (q, analysis)
            for q, analysis in question_analysis.items()
            if analysis["low_prop"] >= 50
        ],
        key=lambda x: x[1]["low_prop"],
        reverse=True,
    )[:5]

    summary_parts = []

    overview = (
        f"Section {section_letter} ({section_title}) demonstrates an overall maturity score of "
        f"{round(section_avg)} out of 4, placing it at the <b>'{maturity_level}'</b> level. "
    )
    summary_parts.append(overview)

    if high_performing:
        questions_text = ", ".join(f"question {q}" for q, analysis in high_performing)
        strengths = f"Areas of strength are demonstrated in {questions_text}. "
        summary_parts.append(strengths)

    if low_performing:
        questions_text = ", ".join(f"question {q}" for q, analysis in low_performing)
        development = (
            f"Opportunities for improvement are identified in {questions_text}. "
        )
        summary_parts.append(development)

    if maturity_level in ["Established", "Substantial Progress"]:
        recommendation = (
            "To maintain and build upon this strong performance, focus on sustaining "
            "existing practices while exploring innovative approaches for further advancement. "
        )
    else:
        recommendation = (
            "To enhance maturity in this section, prioritise developing structured "
            "approaches and implementing systematic improvements across identified areas. "
        )
    summary_parts.append(recommendation)

    full_summary = f"<p>{''.join(summary_parts)}</p>"

    return full_summary


def create_section_figure(data, section_idx, app):

    if not data or "survey_responses" not in data:
        return {}

    questions = get_section_questions(section_idx, app)
    if not questions:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No question data available for this section",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(**GRAPH_LAYOUT)
        return fig

    section_letter = list(questions.keys())[0][0]
    responses = defaultdict(list)

    # Collect valid responses for each question
    for response in data["survey_responses"]:
        section_data = process_section_data(response, section_idx, app)

        if not section_data:
            continue

        for q_idx, score in enumerate(section_data):
            is_valid, numeric_score = validate_score(score)
            if is_valid:
                question_id = f"{section_letter}{q_idx + 1}"
                responses[question_id].append(int(numeric_score))

    if not responses:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No response data available for this section",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(**GRAPH_LAYOUT)
        return fig

    fig = go.Figure()
    question_ids = sorted(responses.keys(), key=lambda x: int(x[1:]))

    for score in range(5):  # 0-4 for maturity levels
        y_data = []
        hover_text = []
        for q_id in question_ids:
            count = sum(1 for s in responses[q_id] if s == score)
            y_data.append(count)
            question_text = questions.get(q_id, f"Question {q_id}")
            hover_text.append(f"{question_text}<br>Count: {count}")

        fig.add_trace(
            go.Bar(
                x=question_ids,
                y=y_data,
                name=MATURITY_LEVELS[score],
                marker_color=COLOUR_PALETTE[score],
                text=[f"{count}" if count > 0 else "" for count in y_data],
                textposition="auto",
                hovertext=hover_text,
                hoverinfo="text",
                offsetgroup=score,
            )
        )

    fig.update_layout(
        {
            **GRAPH_LAYOUT,
            "xaxis": {**GRAPH_LAYOUT["xaxis"], "title": "Questions"},
            "yaxis": {**GRAPH_LAYOUT["yaxis"], "title": "Number of Responses"},
        }
    )

    return fig


def create_demographic_chart(data, question_label, dash_app):

    if not data or "survey_responses" not in data:
        return {}

    demographic_fields = dash_app.demographic_fields
    field = next((f for f in demographic_fields if f["label"] == question_label), None)

    if not field:
        return {}

    field_idx = field["index"]
    field_id = field["id"]
    has_transform = "transform" in field and field["transform"] is not None

    demographic_section_idx = None
    for idx, section in enumerate(dash_app.survey.survey_config.get("sections", [])):
        if section.get("type") == "demographic":
            demographic_section_idx = idx
            break

    if demographic_section_idx is None:
        return {}

    response_counts = defaultdict(int)

    for response in data["survey_responses"]:
        if "answers" in response and len(response["answers"]) > demographic_section_idx:
            try:
                demographic_data = response["answers"][demographic_section_idx]

                if field_idx < len(demographic_data):
                    raw_answer = demographic_data[field_idx]

                    if isinstance(raw_answer, (list, tuple)):
                        for ans in raw_answer:
                            if ans is not None and ans != "":
                                answer = field["transform"](ans) if field_id == "age" and has_transform else str(
                                    ans).title()
                                response_counts[answer] += 1
                    else:
                        if raw_answer is None or raw_answer == "":
                            answer = "Not Specified"
                        else:
                            if field_id == "age" and has_transform:
                                answer = field["transform"](raw_answer)
                            else:
                                answer = str(raw_answer).title()

                        response_counts[answer] += 1
            except (IndexError, KeyError, AttributeError) as e:
                print(f"Error processing demographic data: {str(e)}")
                continue

    if not response_counts:
        return {}

    if field_id == "age":
        age_order = ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+", "Not Specified"]
        ordered_counts = {}
        for age_group in age_order:
            if age_group in response_counts:
                ordered_counts[age_group] = response_counts[age_group]

        for key, value in response_counts.items():
            if key not in ordered_counts:
                ordered_counts[key] = value

        labels = list(ordered_counts.keys())
        values = list(ordered_counts.values())
    else:
        labels = list(response_counts.keys())
        values = list(response_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                customdata=labels,
                hole=0,
                marker=dict(colors=COLOUR_PALETTE[: len(labels)]),
                textinfo="percent",
                textfont=dict(
                    family=THEME["font_family"],
                    size=14
                ),
                textposition="inside",
                sort=False,
                hovertemplate='<b>%{customdata}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ]
    )

    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=0, b=50, pad=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=THEME["font_family"], size=14),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="left",
            x=0.1,
        )
    )
    return fig
