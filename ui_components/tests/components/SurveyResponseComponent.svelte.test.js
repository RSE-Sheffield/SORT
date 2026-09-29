import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/svelte";
import SurveyResponseComponent from "../../src/lib/components/SurveyResponseComponent.svelte";
import consentConfig from "../../../data/survey_config/consent_only_config.json";

const INTERNAL_CONSENT =
  "Yes, I agree to submit my data for internal use within the organisation.";
const RESEARCH_CONSENT = consentConfig.sections[0].fields[1].options[0];

function renderSurvey() {
  const config = structuredClone({
    sections: [
      ...consentConfig.sections,
      {
        title: "Next section",
        type: "sort",
        description: "",
        fields: [
          { type: "text", name: "dummy", label: "Dummy question", required: false },
        ],
      },
    ],
  });
  render(SurveyResponseComponent, { props: { config } });
  return userEvent.setup();
}

test("Respondent can proceed after agreeing to internal use only (#729)", async () => {
  const user = renderSurvey();

  await user.click(screen.getByLabelText(INTERNAL_CONSENT));
  await user.click(screen.getByRole("button", { name: /Next/ }));

  expect(screen.getByText("Dummy question")).toBeInTheDocument();
});

test("Respondent cannot proceed without agreeing to internal use", async () => {
  const user = renderSurvey();

  await user.click(screen.getByRole("button", { name: /Next/ }));

  expect(screen.queryByText("Dummy question")).not.toBeInTheDocument();
  expect(screen.getByText("Values are incorrect or missing", { exact: false })).toBeInTheDocument();
});

test("Ticking then unticking a required checkbox does not satisfy it", async () => {
  const user = renderSurvey();
  const checkbox = screen.getByLabelText(INTERNAL_CONSENT);

  // Tick every other box so that only the unticked one can block the page
  await user.click(screen.getByLabelText(RESEARCH_CONSENT));
  await user.click(checkbox);
  await user.click(checkbox);
  await user.click(screen.getByRole("button", { name: /Next/ }));

  expect(screen.queryByText("Dummy question")).not.toBeInTheDocument();
});
