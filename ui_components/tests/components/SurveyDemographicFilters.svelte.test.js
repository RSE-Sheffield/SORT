import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/svelte";
import SurveyDemographicFilters from "../../src/lib/components/SurveyDemographicFilters.svelte";

// Regression test for the bug where a disabled demographic field caused every
// field after it to be dropped from the filters (the loop used `break` instead
// of `continue`). See GitHub issue #598.
test("SurveyDemographicFilters renders enabled fields after a disabled one", () => {
  const radioField = (label, options, disabled = false) => ({
    type: "radio",
    label,
    description: "",
    required: false,
    sublabels: [],
    options,
    disabled,
    hasOtherOption: false,
  });

  const config = {
    sections: [
      {
        title: "Demographics",
        type: "demographic",
        description: "",
        fields: [
          radioField("What is your gender?", ["Male", "Female"]),
          // Disabled field in the middle — previously caused `break`.
          radioField("What is your current pay band?", ["Band 5", "Band 6"], true),
          radioField("What is your profession?", ["Registered Nurse", "Midwife"]),
        ],
      },
    ],
  };

  // responses[responseIndex][sectionIndex][fieldIndex]
  const responses = [[["Female", "Band 5", "Registered Nurse"]]];

  render(SurveyDemographicFilters, { props: { config, responses } });

  // Enabled fields before AND after the disabled one must render.
  expect(screen.getByText("What is your gender?")).toBeInTheDocument();
  expect(screen.getByText("What is your profession?")).toBeInTheDocument();

  // The disabled field must NOT render.
  expect(screen.queryByText("What is your current pay band?")).not.toBeInTheDocument();
});
