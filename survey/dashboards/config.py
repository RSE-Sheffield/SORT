"""
Configuration parsers for the survey dashboard

This module extracts structured configuration data from survey models for use
in dashboard creation. It includes functions to process survey sections with
proper labeling and to map demographic fields to standardised formats with
any relevant transformations
"""

from .utils import get_age_group

def get_sections_from_survey(survey):
    """
    Extract survey sections from the survey model's survey_config JSON field
    """
    if not survey or not hasattr(survey, 'survey_config') or not survey.survey_config:
        print(f"Survey has no survey_config")
        return []

    try:
        survey_config = survey.survey_config

        sections = []
        if "sections" in survey_config:
            for idx, section in enumerate(survey_config["sections"]):
                # Only process "sort" type sections
                if section.get("type") == "sort":
                    section_id = section.get("title", "").lower().replace(" ", "_").replace(".", "")
                    if not section_id:
                        section_id = f"section_{idx}"
                    letter = section.get("title", "")[0] if section.get("title") else chr(65 + len(sections))
                    sections.append({
                        "id": section_id,
                        "letter": letter,
                        "title": section.get("title", "").split(". ", 1)[1] if ". " in section.get("title",
                                                                                                   "") else section.get(
                            "title", ""),
                        "original_index": section.get("index", idx + 1),
                        "index": len(sections),
                        "config": section
                    })

        print(f"Extracted {len(sections)} sections from survey_config")
        return sections
    except Exception as e:
        print(f"Error in get_sections_from_survey: {str(e)}")
        return []


def get_demographic_fields_from_survey(survey):
    """
    Extracts the demographic fields directly from the survey model's demography_config JSON field
    """
    if not survey or not hasattr(survey, 'demography_config') or not survey.demography_config:
        print(f"Survey has no demography_config")
        return []

    try:
        demographic_fields = []

        demography_config = survey.demography_config

        demographic_section = None
        for section in demography_config.get("sections", []):
            if section.get("type") == "demographic":
                demographic_section = section
                break

        if demographic_section:

            field_mapping = {
                "Your Gender": {"id": "gender", "index": 1},
                "What is your age": {"id": "age", "index": 0},
                "What is your current Band/Grade": {"id": "band", "index": 3},
                "Please indicate your highest qualification": {"id": "qualification", "index": 4},
                "What is your ethnicity?": {"id": "ethnicity", "index": 5}
                #Ommited other mappings for brevity
            }

            for field in demographic_section.get("fields", []):
                field_label = field.get("label")
                if field_label in field_mapping:
                    mapping = field_mapping[field_label]

                    display_label = mapping["id"].title()

                    options = field.get("options", [])
                    if field_label == "What is your age":
                        options = ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"]
                        transform_func = get_age_group
                    else:
                        transform_func = None

                    demographic_fields.append({
                        "id": mapping["id"],
                        "label": display_label,  #
                        "original_label": field_label,
                        "placeholder": f"Select {display_label}",
                        "options": options,
                        "transform": transform_func,
                        "index": mapping["index"]
                    })

        return demographic_fields
    except Exception as e:
        print(f"Error in get_demographic_fields_from_survey: {e}")
        return []