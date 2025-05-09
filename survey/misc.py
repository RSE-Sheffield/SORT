test_survey_config = {
    "sections": [
        {
            "title": "Welcome",
            "type": "consent",
            "fields": [
                {
                    "type": "radio",
                    "name": "consent",
                    "label": "Your agreement to complete the survey",
                    "required": True,
                    "options": [
                        ["Yes", "I agree to complete the survey"],
                        ["No", "I do not agree"],
                    ],
                }
            ],
        },
        {
            "title": "Section 1",
            "description": "",
            "fields": [
                {
                    "type": "char",
                    "name": "char_field",
                    "label": "Char field",
                },
                {
                    "type": "text",
                    "name": "text_field",
                    "label": "Text field",
                },
                {
                    "type": "checkbox",
                    "name": "checkbox_field",
                    "label": "Checkbox field",
                    "options": [["Value 1", "Label 1"], ["Value 2", "Label 2"]],
                },
                {
                    "type": "radio",
                    "name": "radio_field",
                    "label": "Radio field",
                    "options": [["Value 1", "Label 1"], ["Value 2", "Label 2"]],
                },
            ],
        },
        {
            "title": "Section 2",
            "description": "",
            "fields": [
                {
                    "type": "char",
                    "name": "char_field",
                    "label": "Char field",
                },
                {
                    "type": "text",
                    "name": "text_field",
                    "label": "Text field",
                },
                {
                    "type": "checkbox",
                    "name": "checkbox_field",
                    "label": "Checkbox field",
                    "options": [["Value 1", "Label 1"], ["Value 2", "Label 2"]],
                },
                {
                    "type": "radio",
                    "name": "radio_field",
                    "label": "Radio field",
                    "options": [["Value 1", "Label 1"], ["Value 2", "Label 2"]],
                },
            ],
        },
    ]
}
