import { test } from "vitest";
import "@testing-library/jest-dom";
import { render } from "@testing-library/svelte";
import Text from "../../../src/lib/components/input/Text.svelte";

test("Text", () => {
  render(Text, {
    props: { config: { description: "My text field", required: true } },
  });
});
