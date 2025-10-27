import { test } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import LikertRow from "../../../src/lib/components/input/LikertRow.svelte";

test("LikertRow", () => {
  render(LikertRow, {
    props: {
      config: {
        options: ["1", "2", "3", "4", "5"],
        sublabels: ["Test sublabel A", "Test sublabel B", "Test sublabel C"],
        required: false,
      },
      sublabelIndex: 0,
    },
  });
});
