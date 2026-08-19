import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/svelte";
import SortLikertStats from "../../src/lib/components/SortLikertStats.svelte";
import { generateStatsFromSurveyResponses } from "../../src/lib/misc.svelte.ts";
import { sortSurveyConfig, validResponse } from "../fixtures/surveyConfig.js";

const SECTION_INDEX = 1;
const FIELD_INDEX = 0;

test("SortLikertStats summarises a section score", () => {
  const config = sortSurveyConfig();
  const surveyStats = generateStatsFromSurveyResponses(config, [validResponse()]);

  render(SortLikertStats, {
    config,
    surveyStats,
    sectionIndex: SECTION_INDEX,
    fieldIndex: FIELD_INDEX,
  });

  expect(screen.getByText(/demonstrates an overall score/)).toBeInTheDocument();
  expect(screen.getByText(/Substantial progress/)).toBeInTheDocument();
});

test("SortLikertStats explains a section with no score", () => {
  const config = sortSurveyConfig();
  const response = validResponse();
  response[SECTION_INDEX][FIELD_INDEX] = ["Agree", "Agree", "Agree"];
  const surveyStats = generateStatsFromSurveyResponses(config, [response]);

  render(SortLikertStats, {
    config,
    surveyStats,
    sectionIndex: SECTION_INDEX,
    fieldIndex: FIELD_INDEX,
  });

  expect(screen.getByText(/No overall score is available/)).toBeInTheDocument();
});

// Stats can be missing entirely for a field, e.g. an unrecognised field type or a
// section absent from every stored response.
test("SortLikertStats renders when the field has no stats", () => {
  render(SortLikertStats, {
    config: sortSurveyConfig(),
    surveyStats: { sections: [] },
    sectionIndex: SECTION_INDEX,
    fieldIndex: FIELD_INDEX,
  });

  expect(screen.getByText(/No overall score is available/)).toBeInTheDocument();
  expect(screen.getByText("Areas of strength")).toBeInTheDocument();
});

test("SortLikertStats renders when the stats are null", () => {
  render(SortLikertStats, {
    config: sortSurveyConfig(),
    surveyStats: null,
    sectionIndex: SECTION_INDEX,
    fieldIndex: FIELD_INDEX,
  });

  expect(screen.getByText(/No overall score is available/)).toBeInTheDocument();
});
