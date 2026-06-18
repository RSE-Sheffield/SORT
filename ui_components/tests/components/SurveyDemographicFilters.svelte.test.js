import { test, expect, vi } from "vitest";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/svelte";
import { tick } from "svelte";
import SurveyDemographicFilters from "../../src/lib/components/SurveyDemographicFilters.svelte";
import { TextType } from "../../src/lib/interfaces.ts";

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

// Regression test for the bug where a disabled demographic field caused every
// field after it to be dropped from the filters (the loop used `break` instead
// of `continue`). See GitHub issue #598.
test("SurveyDemographicFilters renders enabled fields after a disabled one", () => {
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

// Issue #605: allow selecting multiple categories at once (e.g. several
// hospital sites within a Trust).
const siteConfig = {
  sections: [
    {
      title: "Demographics",
      type: "demographic",
      description: "",
      fields: [
        radioField("What is your hospital site?", [
          "Royal Hallamshire",
          "Northern General",
          "Weston Park",
        ]),
      ],
    },
  ],
};

const siteResponses = [
  [["Royal Hallamshire"]],
  [["Northern General"]],
  [["Weston Park"]],
];

test("renders a checkbox per option instead of a single select", () => {
  render(SurveyDemographicFilters, {
    props: { config: siteConfig, responses: siteResponses },
  });

  expect(screen.getByLabelText("Royal Hallamshire")).toBeInTheDocument();
  expect(screen.getByLabelText("Northern General")).toBeInTheDocument();
  expect(screen.getByLabelText("Weston Park")).toBeInTheDocument();
  // No single-select dropdown.
  expect(document.querySelector("select")).toBeNull();
});

test("ticking multiple options keeps responses matching either value", async () => {
  const onFilterChange = vi.fn();
  render(SurveyDemographicFilters, {
    props: { config: siteConfig, responses: siteResponses, onFilterChange },
  });

  await fireEvent.click(screen.getByLabelText("Royal Hallamshire"));
  await fireEvent.click(screen.getByLabelText("Northern General"));

  const [filtered, activeFilters] =
    onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1];

  // Union of the two selected sites — Weston Park excluded.
  expect(filtered).toEqual([
    [["Royal Hallamshire"]],
    [["Northern General"]],
  ]);
  expect(activeFilters).toEqual([
    {
      label: "What is your hospital site?",
      value: "Royal Hallamshire, Northern General",
    },
  ]);
});

test("with nothing ticked, all responses pass through", async () => {
  const onFilterChange = vi.fn();
  render(SurveyDemographicFilters, {
    props: { config: siteConfig, responses: siteResponses, onFilterChange },
  });

  // Tick then untick — back to the empty "All" default.
  const box = screen.getByLabelText("Royal Hallamshire");
  await fireEvent.click(box);
  await fireEvent.click(box);

  const [filtered, activeFilters] =
    onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1];

  expect(filtered).toEqual(siteResponses);
  expect(activeFilters).toEqual([]);
});

test("clearing filters resets a categorical selection back to All", async () => {
  const onFilterChange = vi.fn();
  let clearFilters;
  const onClearFiltersCallback = (cb) => {
    clearFilters = cb;
  };
  render(SurveyDemographicFilters, {
    props: {
      config: siteConfig,
      responses: siteResponses,
      onFilterChange,
      onClearFiltersCallback,
    },
  });

  await fireEvent.click(screen.getByLabelText("Royal Hallamshire"));

  // Selection narrowed the set down to the one matching site.
  let [filtered, activeFilters] =
    onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1];
  expect(filtered).toEqual([[["Royal Hallamshire"]]]);
  expect(activeFilters).toHaveLength(1);

  // Clearing restores all responses and removes the active filter.
  clearFilters();
  await tick();
  [filtered, activeFilters] =
    onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1];
  expect(filtered).toEqual(siteResponses);
  expect(activeFilters).toEqual([]);
  // The checkbox is unticked again.
  expect(screen.getByLabelText("Royal Hallamshire").checked).toBe(false);
});

// A report can mix numeric (range) and categorical (checkbox) filters; they
// must both render and apply together.
test("mixes a numeric range filter with a categorical checkbox filter", async () => {
  const config = {
    sections: [
      {
        title: "Demographics",
        type: "demographic",
        description: "",
        fields: [
          {
            type: "text",
            label: "What is your age?",
            description: "",
            required: false,
            sublabels: [],
            options: [],
            textType: TextType.integer,
            disabled: false,
            hasOtherOption: false,
          },
          radioField("What is your hospital site?", [
            "Royal Hallamshire",
            "Northern General",
          ]),
        ],
      },
    ],
  };
  // responses[responseIndex][sectionIndex][fieldIndex]
  const responses = [
    [["30", "Royal Hallamshire"]],
    [["45", "Northern General"]],
  ];

  const onFilterChange = vi.fn();
  render(SurveyDemographicFilters, {
    props: { config, responses, onFilterChange },
  });

  // Both filter kinds render: a range slider and the option checkboxes.
  expect(document.querySelector('input[type="range"]')).not.toBeNull();
  expect(screen.getByLabelText("Royal Hallamshire")).toBeInTheDocument();
  expect(screen.getByLabelText("Northern General")).toBeInTheDocument();

  // Selecting a category narrows the set; the (untouched, full-range) numeric
  // filter leaves the matching response in place.
  await fireEvent.click(screen.getByLabelText("Royal Hallamshire"));

  const [filtered, activeFilters] =
    onFilterChange.mock.calls[onFilterChange.mock.calls.length - 1];
  expect(filtered).toEqual([[["30", "Royal Hallamshire"]]]);
  expect(activeFilters).toEqual([
    { label: "What is your hospital site?", value: "Royal Hallamshire" },
  ]);
});
