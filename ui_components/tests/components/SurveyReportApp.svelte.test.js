import { test, expect, vi, beforeEach, afterEach } from "vitest";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/svelte";
import SurveyReportApp from "../../src/lib/components/SurveyReportApp.svelte";
import { sortSurveyConfig, validResponse } from "../fixtures/surveyConfig.js";

let consoleError;

beforeEach(() => {
  consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
  consoleError.mockRestore();
});

test("SurveyReportApp renders the report for well-formed responses", () => {
  render(SurveyReportApp, { config: sortSurveyConfig(), responses: [validResponse()] });

  expect(screen.getByText("Summary Ranking Matrix")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Research culture" })).toBeInTheDocument();
  expect(consoleError).not.toHaveBeenCalled();
});

test("SurveyReportApp reports that there are no statistics without responses", () => {
  render(SurveyReportApp, { config: sortSurveyConfig(), responses: [] });

  expect(screen.getByText("No statistics available.")).toBeInTheDocument();
});

// Regression test for the production report page crashing with
// "Cannot read properties of undefined (reading 'length')". A response recorded before
// a question was added to the survey configuration holds fewer answers than there are
// fields, and that must not take down the whole report. See GitHub issue #710.
test("SurveyReportApp still renders when a response is missing answers", () => {
  const shortResponse = validResponse();
  shortResponse[0] = [["Yes, I agree"]]; // second consent checkbox never recorded
  shortResponse[1] = [["2", "3"]]; // one likert row and the comment box missing

  render(SurveyReportApp, {
    config: sortSurveyConfig(),
    responses: [validResponse(), shortResponse],
  });

  expect(screen.getByText("Summary Ranking Matrix")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Research culture" })).toBeInTheDocument();
  expect(consoleError).not.toHaveBeenCalled();
});

test("SurveyReportApp renders when the survey has no configuration", () => {
  render(SurveyReportApp, { config: { sections: [] }, responses: [validResponse()] });

  expect(screen.getByText("Summary Ranking Matrix")).toBeInTheDocument();
  expect(consoleError).not.toHaveBeenCalled();
});
