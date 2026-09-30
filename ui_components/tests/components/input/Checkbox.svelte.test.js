import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import Checkbox from "../../../src/lib/components/input/Checkbox.svelte";

test("Checkbox", () => {
  render(Checkbox, {
    props: {
      config: {
        description: "",
        options: ["Yes, I agree to complete the survey"],
      },
    },
  });
});

test("Checkbox renders without a description", () => {
  render(Checkbox, {
    props: {
      config: {
        options: ["Yes, I agree to complete the survey"],
      },
    },
  });
});

test.each([
  { required: true, value: undefined, expected: false },
  { required: true, value: [], expected: false },
  { required: true, value: ["A"], expected: true },
  { required: false, value: undefined, expected: true },
  { required: false, value: [], expected: true },
  { required: false, value: ["A"], expected: true },
])(
  "validate() with required=$required and value=$value returns $expected",
  ({ required, value, expected }) => {
    const { component } = render(Checkbox, {
      props: {
        config: { description: "", options: ["A", "B"], required },
        value,
      },
    });
    expect(component.validate()).toBe(expected);
  },
);
