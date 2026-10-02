import { test, expect, vi } from "vitest";
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

// --- disabled fields and sections (#741) ---

const textField = (label, disabled = false) => ({
  type: "text",
  name: label,
  label,
  required: false,
  disabled,
});

const section = (title, ...fields) => ({ title, type: "sort", description: "", fields });

function renderSections(sections) {
  render(SurveyResponseComponent, { props: { config: { sections } } });
  return userEvent.setup();
}

test("Sections with only disabled fields are skipped (#741)", async () => {
  const user = renderSections([
    section("First", textField("Q1")),
    section("Hidden", textField("Q2", true), textField("Q3", true)),
    section("Last", textField("Q4")),
  ]);

  await user.click(screen.getByRole("button", { name: /Next/ }));
  expect(screen.getByText("Q4")).toBeInTheDocument();
  // The hidden section was the last but one, so this is now the final page
  expect(screen.queryByRole("button", { name: /Next/ })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Submit/ })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: /Previous/ }));
  expect(screen.getByText("Q1")).toBeInTheDocument();
});

test("A trailing fully disabled section does not add a blank page (#741)", async () => {
  renderSections([
    section("First", textField("Q1")),
    section("Demographics", textField("Q2", true)),
  ]);

  expect(screen.queryByRole("button", { name: /Next/ })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Submit/ })).toBeInTheDocument();
});

test("A section with some enabled fields is shown without the disabled ones", () => {
  renderSections([section("Mixed", textField("Enabled Q"), textField("Disabled Q", true))]);

  expect(screen.getByText("Enabled Q")).toBeInTheDocument();
  expect(screen.queryByText("Disabled Q")).not.toBeInTheDocument();
});

test("A survey with every field disabled can still be submitted", async () => {
  const user = renderSections([section("Only", textField("Q1", true))]);
  const submit = vi.fn((e) => e.preventDefault());
  document.addEventListener("submit", submit);

  await user.click(screen.getByRole("button", { name: /Submit/ }));

  expect(submit).toHaveBeenCalled();
  expect(screen.queryByText("Values are incorrect or missing", { exact: false })).not.toBeInTheDocument();
  document.removeEventListener("submit", submit);
});

test("Answers for skipped sections are submitted as null so they match the config", async () => {
  const user = renderSections([
    section("First", textField("Q1")),
    section("Hidden", textField("Q2", true), textField("Q3", true)),
    section("Last", textField("Q4")),
  ]);
  await user.type(screen.getByLabelText("Q1"), "a");
  await user.click(screen.getByRole("button", { name: /Next/ }));
  await user.type(screen.getByLabelText("Q4"), "b");

  const value = JSON.parse(document.querySelector("input[name=value]").value);
  expect(value).toEqual([["a"], [null, null], ["b"]]);
});
