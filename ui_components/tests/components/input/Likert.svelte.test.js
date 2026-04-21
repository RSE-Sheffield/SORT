import { test } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import Likert from "../../../src/lib/components/input/Likert.svelte";

test("Likert", () => {
  render(Likert, {
    props: {
      config: {
        description: "My likert description",
        options: ["1", "2", "3", "4", "5"],
        sublabels: ["Test sublabel A", "Test sublabel B", "Test sublabel C"],
        required: false,
      },
    },
  });
});
