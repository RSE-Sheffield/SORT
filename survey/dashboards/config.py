import os
import json
from django.conf import settings

SORT_CONFIG_PATH = os.path.join(
    settings.BASE_DIR, "data", "survey_config", "sort_only_config.json"
)
DEMOGRAPHIC_CONFIG_PATH = os.path.join(
    settings.BASE_DIR, "data", "survey_config", "demography_only_config.json"
)

with open(SORT_CONFIG_PATH, "r") as f:
    SURVEY_CONFIG = json.load(f)

with open(DEMOGRAPHIC_CONFIG_PATH, "r") as f:
    DEMOGRAPHIC_CONFIG = json.load(f)


ALL_SECTIONS = {
    "sort": SURVEY_CONFIG["sections"],
    "demographic": DEMOGRAPHIC_CONFIG["sections"],
}

def get_age_group(age):
    try:
        age_num = int(age)
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
    except (ValueError, TypeError):
        return "Unknown age"

# Survey sections configuration
SECTIONS = [
    {
        "id": "releasing_potential",
        "letter": "A",
        "title": "Releasing Potential",
        "index": 1,
        "config": SURVEY_CONFIG["sections"][0],
    },
    {
        "id": "embedding_research",
        "letter": "B",
        "title": "Embedding Research",
        "index": 2,
        "config": SURVEY_CONFIG["sections"][1],
    },
    {
        "id": "linkages_leadership",
        "letter": "C",
        "title": "Linkages and Leadership",
        "index": 3,
        "config": SURVEY_CONFIG["sections"][2],
    },
    {
        "id": "inclusive_research",
        "letter": "D",
        "title": "Inclusive Research",
        "index": 4,
        "config": SURVEY_CONFIG["sections"][3],
    },
    {
        "id": "digital_capability",
        "letter": "E",
        "title": "Digital Capability",
        "index": 5,
        "config": SURVEY_CONFIG["sections"][4],
    },
]

# Demographic fields configuration
DEMOGRAPHIC_FIELDS = [
    {
        "id": "gender",
        "label": "Your Gender",
        "placeholder": "Select Gender",
        "config": DEMOGRAPHIC_CONFIG["sections"][0]["fields"][1],
        "index": 1
    },

    {
        "id": "age",
        "label": "Your Age",
        "placeholder": "Select Age",
        "config": DEMOGRAPHIC_CONFIG["sections"][0]["fields"][2],
        "index": 2 ,
        "transform": get_age_group,
        "options": ["Under 25", "25-34", "35-44", "45-54", "55-64", "65+"],
    },

    {
        "id": "band",
        "label": "What is your current Band/Grade",
        "placeholder": "Select Band/Grade",
        "config": DEMOGRAPHIC_CONFIG["sections"][0]["fields"][3],
        "index": 3
    },
    {
        "id": "qualification",
        "label": "Please indicate your highest qualification",
        "placeholder": "Select Qualification",
        "config": DEMOGRAPHIC_CONFIG["sections"][0]["fields"][4],
        "index": 4
    },
    {
        "id": "ethnicity",
        "label": "What is your ethnicity?",
        "placeholder": "Select Ethnicity",
        "config": DEMOGRAPHIC_CONFIG["sections"][0]["fields"][5],
        "index": 5
    },
]