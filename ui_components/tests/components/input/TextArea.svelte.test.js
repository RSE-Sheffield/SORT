import { test } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import TextArea from "../../../src/lib/components/input/TextArea.svelte";

test("TextArea", () => {
  render(TextArea, {
    props: {
      config: {
        description: "My text area field",
        required: true,
      },
    },
  });
});
