import { describe, test, expect } from "vitest";
import {
  generateStatsFromSurveyResponses,
  getSortMaturityLabel,
  MATURITY_LABEL_UNKNOWN,
} from "../../src/lib/misc.svelte.ts";
import {
  checkboxField,
  likertField,
  radioField,
  sortSurveyConfig,
  textareaField,
  validResponse,
} from "../fixtures/surveyConfig.js";

describe("generateStatsFromSurveyResponses", () => {
  test("returns null when there are no responses", () => {
    expect(generateStatsFromSurveyResponses(sortSurveyConfig(), [])).toBeNull();
    expect(generateStatsFromSurveyResponses(sortSurveyConfig(), null)).toBeNull();
    expect(generateStatsFromSurveyResponses(sortSurveyConfig(), undefined)).toBeNull();
  });

  test("summarises a well-formed response", () => {
    const stats = generateStatsFromSurveyResponses(sortSurveyConfig(), [validResponse()]);

    // One entry per configured section and field
    expect(stats.sections).toHaveLength(2);
    expect(stats.sections[0].fields).toHaveLength(2);
    expect(stats.sections[1].fields).toHaveLength(2);

    // Likert: one histogram per sub-label, mean over all of them
    expect(stats.sections[1].fields[0].histograms).toHaveLength(3);
    expect(stats.sections[1].fields[0].mean).toBeCloseTo(3);

    // Free text is collected verbatim
    expect(stats.sections[1].fields[1].values).toEqual(["Some comments"]);
  });

  // Regression test for the report page crashing with
  // "Cannot read properties of undefined (reading 'length')" when a stored response
  // holds fewer fields than the survey configuration describes. See GitHub issue #710.
  test("tolerates a response with fewer fields than the configuration", () => {
    const response = validResponse();
    // Drop the second consent checkbox, as responses recorded before that question was
    // added to the configuration do.
    response[0] = [["Yes, I agree"]];

    const stats = generateStatsFromSurveyResponses(sortSurveyConfig(), [response]);

    expect(stats.sections[0].fields).toHaveLength(2);
    // The missing answer contributes nothing rather than throwing
    expect(stats.sections[0].fields[1].histogram.every((v) => v.count === 0)).toBe(true);
  });

  test("tolerates a response with fewer sections than the configuration", () => {
    const stats = generateStatsFromSurveyResponses(sortSurveyConfig(), [[[["Yes, I agree"]]]]);

    expect(stats.sections).toHaveLength(2);
    expect(stats.sections[1].fields[0].histograms).toHaveLength(3);
    expect(stats.sections[1].fields[1].values).toEqual([]);
  });

  test("tolerates a likert field with no sub-labels", () => {
    const config = sortSurveyConfig();
    delete config.sections[1].fields[0].sublabels;

    const stats = generateStatsFromSurveyResponses(config, [validResponse()]);

    expect(stats.sections[1].fields[0].histograms).toEqual([]);
    expect(stats.sections[1].fields[0].mean).toBeUndefined();
  });

  test("treats a checkbox answer stored as a bare string as one selected option", () => {
    const response = validResponse();
    response[0][0] = "Yes, I agree";

    const stats = generateStatsFromSurveyResponses(sortSurveyConfig(), [response]);

    const histogram = stats.sections[0].fields[0].histogram;
    expect(histogram).toEqual([{ option: "Yes, I agree", count: 1 }]);
  });

  test("keeps field indices aligned when a field type is not recognised", () => {
    const config = sortSurveyConfig();
    config.sections[1].fields = [
      { type: "date", label: "When?", options: [], sublabels: [] },
      likertField("Rate the following", ["Leadership"]),
    ];
    const responses = [[[["Yes, I agree"], ["I have read and agree"]], ["2026-01-01", ["3"]]]];

    const stats = generateStatsFromSurveyResponses(config, responses);

    // The unrecognised field still occupies its slot, so the likert stats stay at
    // index 1 where the components look for them.
    expect(stats.sections[1].fields).toHaveLength(2);
    expect(stats.sections[1].fields[1].histograms).toHaveLength(1);
  });

  test("leaves the mean undefined when an option is not numeric", () => {
    const config = {
      sections: [
        {
          title: "Demographics",
          type: "demographic",
          description: "",
          fields: [radioField("Pay band", ["Band 5", "Not applicable"])],
        },
      ],
    };

    const stats = generateStatsFromSurveyResponses(config, [[["Not applicable"]]]);

    expect(stats.sections[0].fields[0].mean).toBeUndefined();
  });

  test("tolerates a configuration with no sections", () => {
    expect(generateStatsFromSurveyResponses({}, [[[]]])).toEqual({ sections: [] });
    expect(generateStatsFromSurveyResponses({ sections: [] }, [[[]]])).toEqual({
      sections: [],
    });
  });

  test("does not report a mean for a field with no answers at all", () => {
    const config = {
      sections: [
        {
          title: "Comments",
          type: "sort",
          description: "",
          fields: [checkboxField("Pick one", ["0", "1"]), textareaField("Why?")],
        },
      ],
    };

    const stats = generateStatsFromSurveyResponses(config, [[[]]]);

    expect(stats.sections[0].fields[0].mean).toBeUndefined();
    expect(stats.sections[0].fields[1].values).toEqual([]);
  });
});

describe("getSortMaturityLabel", () => {
  test("labels a score", () => {
    expect(getSortMaturityLabel(0)).toBe("Not yet planned");
    expect(getSortMaturityLabel(4)).toBe("Established");
  });

  test("reports a missing score rather than throwing", () => {
    expect(getSortMaturityLabel(undefined)).toBe(MATURITY_LABEL_UNKNOWN);
    expect(getSortMaturityLabel(null)).toBe(MATURITY_LABEL_UNKNOWN);
    expect(getSortMaturityLabel(NaN)).toBe(MATURITY_LABEL_UNKNOWN);
  });

  test("still rejects a score outside the scale", () => {
    expect(() => getSortMaturityLabel(5)).toThrow(RangeError);
    expect(() => getSortMaturityLabel("2")).toThrow(TypeError);
  });
});
