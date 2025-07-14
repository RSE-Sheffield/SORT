import { test } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import Likert from "../../../src/lib/components/input/Likert.svelte";

test("Likert", () => {
  render(Likert, {
    props: {
      config: {
        description: "My likert description",
        sublabels: ["Test sublabel A", "Test sublabel B", "Test sublabel C"],
      },
    },
  });
});
