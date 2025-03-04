import numpy as np
import plotly.graph_objects as go
from collections import defaultdict
from scipy import stats
from .constants import MATURITY_LEVELS, GRAPH_LAYOUT, THEME, COLOUR_PALETTE
from .config import SECTIONS, DEMOGRAPHIC_CONFIG, get_age_group


def get_section_questions(section_idx):

    if section_idx < 1 or section_idx > len(SECTIONS):
        return {}

    try:
        section = next(s for s in SECTIONS if s["index"] == section_idx)
        section_config = section["config"]

        # Get the likert field from the section
        likert_field = next(
            field for field in section_config["fields"] if field["type"] == "likert"
        )

        # Create questions dictionary
        questions = {}
        for i, text in enumerate(likert_field["sublabels"]):
            q_id = f"{section['letter']}{i + 1}"
            questions[q_id] = text

        return questions
    except Exception as e:
        print(f"Error in get_section_questions for section {section_idx}: {str(e)}")
        return {}


def process_section_data(response, section_idx):
    if 'answers' in response and len(response['answers']) > section_idx:
        try:
            section_data = response['answers'][section_idx]
            if isinstance(section_data, list) and section_data:
                return section_data[0]
        except (IndexError, KeyError):
            pass

    return []


def calculate_section_statistics(data, section_idx):

    all_scores = []
    for response in data["survey_responses"]:
        try:
            section_data = process_section_data(response, section_idx)
            scores = [float(score) for score in section_data if score.isdigit()]
            all_scores.extend(scores)
        except Exception as e:
            print(f"Error processing response for section {section_idx}: {str(e)}")
            continue

    if not all_scores:
        return []

    try:
        mode_value = stats.mode(all_scores, keepdims=False)[0]
        return [
            {"statistic": "Mean Score", "value": f"{np.mean(all_scores):.2f}"},
            {"statistic": "Minimum", "value": f"{min(all_scores):.1f}"},
            {"statistic": "Maximum", "value": f"{max(all_scores):.1f}"},
            {"statistic": "Mode", "value": f"{mode_value:.1f}"},
        ]
    except Exception as e:
        print(f"Error calculating statistics: {str(e)}")
        return []


def get_maturity_level(score):

    score_int = int(np.floor(score))
    score_int = max(0, min(4, score_int))
    return MATURITY_LEVELS[score_int]



def filter_survey_data(survey_responses, filters):
    """Filter survey responses based on demographic filters."""
    if not filters:
        return survey_responses

    filtered_responses = []

    field_positions = {
        'age': 0,
        'gender': 1,
        'band': 3,
        'qualification': 4,
        'ethnicity': 5
    }

    for response in survey_responses:
        if 'answers' not in response or len(response['answers']) < 7:
            continue

        try:
            demographic_data = response['answers'][6]

            # Check if response matches all filters
            match = True
            for filter_id, filter_value in filters.items():
                position = field_positions.get(filter_id)
                if position is None:
                    continue

                # Special case for age which needs transformation
                if filter_id == 'age':
                    age_group = get_age_group(demographic_data[position])
                    if age_group != filter_value:
                        match = False
                        break
                # Direct comparison for other fields
                elif demographic_data[position] != filter_value:
                    match = False
                    break

            if match:
                filtered_responses.append(response)

        except (IndexError, TypeError):
            continue

    return filtered_responses


def calculate_section_averages(responses):
    section_averages = {}

    for section in SECTIONS:
        section_scores = []
        for response in responses:
            if "answers" in response:
                try:
                    section_data = response["answers"][section["index"]][0]
                    scores = [float(score) for score in section_data if score.isdigit()]
                    if scores:
                        section_scores.append(np.mean(scores))
                except (IndexError, KeyError, TypeError):
                    pass

        section_averages[section["id"]] = (
            np.mean(section_scores) if section_scores else 0
        )

    return section_averages


def create_section_summary(data, section_idx):
    if not data or "survey_responses" not in data:
        return ""

    questions = get_section_questions(section_idx)
    if not questions:
        return ""

    section_letter = list(questions.keys())[0][0]

    question_scores = {}
    for q_id in questions:
        scores = []
        for response in data["survey_responses"]:
            section_data = process_section_data(response, section_idx)
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
        high_scores = sum(1 for s in scores if s >= 3)
        low_scores = sum(1 for s in scores if s <= 2)
        total_scores = len(scores)

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
        f"Section {section_letter} demonstrates an overall maturity score of "
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
            "To enhance maturity in this section, prioritize developing structured "
            "approaches and implementing systematic improvements across identified areas. "
        )
    summary_parts.append(recommendation)

    full_summary = f"<p>{''.join(summary_parts)}</p>"

    return full_summary


def get_demographic_field_index(field_label):
    for idx, field in enumerate(DEMOGRAPHIC_CONFIG["sections"][0]["fields"]):
        if field["label"] == field_label:
            return idx
    return None


def create_section_figure(data, section_idx):
    if not data or "survey_responses" not in data:
        return {}

    questions = get_section_questions(section_idx)
    if not questions:
        return {}

    section_letter = list(questions.keys())[0][0]
    responses = defaultdict(list)

    for response in data["survey_responses"]:
        section_data = process_section_data(response, section_idx)
        for q_idx, score in enumerate(section_data):
            if score.isdigit():
                question_id = f"{section_letter}{q_idx + 1}"
                responses[question_id].append(int(score))

    fig = go.Figure()
    question_ids = sorted(responses.keys(), key=lambda x: int(x[1:]))

    for score in range(5):
        y_data = []
        hover_text = []
        for q_id in question_ids:
            count = sum(1 for s in responses[q_id] if s == score)
            y_data.append(count)
            hover_text.append(f"{questions[q_id]}<br>" f"Count: {count}")

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



def create_demographic_chart(data, question_label):
    if not data or "survey_responses" not in data:
        return {}

    field_idx = get_demographic_field_index(question_label)
    if field_idx is None:
        return {}

    response_counts = defaultdict(int)
    for response in data["survey_responses"]:
        if "answers" in response:
            try:
                answer = response["answers"][6][field_idx].title()
                response_counts[answer] += 1
            except (IndexError, KeyError, AttributeError):
                pass

    if not response_counts:
        return {}

    labels = list(response_counts.keys())
    values = list(response_counts.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=COLOUR_PALETTE[: len(labels)]),
                textinfo="value+percent",
                textfont=dict(family=THEME["font_family"], size=13),
                textposition="inside",
            )
        ]
    )

    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, t=30, b=30, pad=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=THEME["font_family"], size=15),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
        uniformtext=dict(mode="hide", minsize=12),
    )

    return fig
