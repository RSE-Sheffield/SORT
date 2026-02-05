import { test, expect } from "vitest";
import "@testing-library/jest-dom";
import userEvent from "@testing-library/user-event";
import { render } from "@testing-library/svelte";
import CollapsibleCard from "../../src/lib/components/CollapsibleCard.svelte";

test("CollapsibleCard", async () => {
  render(CollapsibleCard, {
    props: {
      startCollapsed: true,
    },
  });
  const user = userEvent.setup();
  const toggleButton = document.querySelector(".card .card-header a");

  // Check initial HTML elements
  expect(toggleButton).toBeInTheDocument();
  expect(document.querySelector(".card-body")).not.toBeInTheDocument();

  // Click to expand
  await user.click(toggleButton);
  expect(toggleButton).toHaveTextContent("Collapse");
  expect(document.querySelector(".card-body")).toBeInTheDocument();

  // Click to collapse
  await user.click(toggleButton);
  expect(toggleButton).toHaveTextContent("Expand");
});
