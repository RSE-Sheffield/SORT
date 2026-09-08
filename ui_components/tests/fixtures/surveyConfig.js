/**
 * Survey configuration and response fixtures shared by the report tests.
 *
 * These mirror the real shapes produced by Survey.update() in survey/models.py:
 * a consent section of checkboxes, one or more "sort" sections whose first field is a
 * likert table, and a trailing demographic section.
 */

export const likertOptions = ["0", "1", "2", "3", "4"];

export function likertField(label, sublabels) {
  return {
    type: "likert",
    label,
    description: "",
    required: true,
    sublabels,
    options: likertOptions,
  };
}

export function checkboxField(label, options) {
  return {
    type: "checkbox",
    label,
    description: "",
    required: true,
    sublabels: [],
    options,
  };
}

export function textareaField(label) {
  return {
    type: "textarea",
    label,
    description: "",
    required: false,
    sublabels: [],
    options: [],
  };
}

export function radioField(label, options) {
  return {
    type: "radio",
    label,
    description: "",
    required: true,
    sublabels: [],
    options,
  };
}

/**
 * A survey with a consent section (two checkboxes) and one sort section
 * (a likert table plus a free-text comment box).
 */
export function sortSurveyConfig() {
  return {
    sections: [
      {
        title: "Welcome",
        type: "consent",
        description: "",
        fields: [
          checkboxField("Do you agree to complete the survey?", ["Yes, I agree"]),
          checkboxField("Do you consent to research use?", ["I have read and agree"]),
        ],
      },
      {
        title: "Research culture",
        type: "sort",
        description: "",
        fields: [
          likertField("Rate the following", ["Leadership", "Capacity", "Training"]),
          textareaField("Any comments?"),
        ],
      },
    ],
  };
}

/**
 * A well-formed response to sortSurveyConfig(), indexed
 * [sectionIndex][fieldIndex].
 */
export function validResponse() {
  return [
    [["Yes, I agree"], ["I have read and agree"]],
    [["2", "3", "4"], "Some comments"],
  ];
}
