import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/svelte";
import SortSummaryMatrix from "../../src/lib/components/SortSummaryMatrix.svelte";
import { generateStatsFromSurveyResponses } from "../../src/lib/misc.svelte.ts";
import { sortSurveyConfig, validResponse } from "../fixtures/surveyConfig.js";

test("SortSummaryMatrix shows a maturity label per sort section", () => {
  const config = sortSurveyConfig();
  const surveyStats = generateStatsFromSurveyResponses(config, [validResponse()]);

  render(SortSummaryMatrix, { config, surveyStats });

  expect(screen.getByText("Research culture")).toBeInTheDocument();
  expect(screen.getByText(/Substantial progress/)).toBeInTheDocument();
  // The consent section is not a sort section, so it gets no column
  expect(screen.queryByText("Welcome")).not.toBeInTheDocument();
});

// main.ts mounts this component directly with whatever
// generateStatsFromSurveyResponses() returned, which is null when a survey has no
// responses. Reading the stats at component init used to throw before the guard.
test("SortSummaryMatrix renders an empty state when there are no stats", () => {
  render(SortSummaryMatrix, { config: sortSurveyConfig(), surveyStats: null });

  expect(screen.getByText("Statistics not available")).toBeInTheDocument();
});

test("SortSummaryMatrix renders when the config has no sections", () => {
  render(SortSummaryMatrix, { config: {}, surveyStats: { sections: [] } });

  expect(screen.getByText("Statistics not available")).toBeInTheDocument();
});

test("SortSummaryMatrix reports a section with no numeric answers as unavailable", () => {
  const config = sortSurveyConfig();
  // Answers present but not numeric, so the section has no mean score
  const response = validResponse();
  response[1][0] = ["Strongly agree", "Agree", "Agree"];
  const surveyStats = generateStatsFromSurveyResponses(config, [response]);

  render(SortSummaryMatrix, { config, surveyStats });

  expect(screen.getByText("Research culture")).toBeInTheDocument();
  expect(screen.getByText(/Not available/)).toBeInTheDocument();
});
