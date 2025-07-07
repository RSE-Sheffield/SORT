import {test, expect} from 'vitest';
import "@testing-library/jest-dom";
import userEvent from '@testing-library/user-event';
import {render, screen} from '@testing-library/svelte';
import CollapsibleCard from "../../src/lib/components/CollapsibleCard.svelte";


test("CollapsibleCard", async () => {
    render(CollapsibleCard, {props: {startCollapsed: true}});
    const user = userEvent.setup();
    const toggleElement = screen.getByRole("link");

    // Make sure it exits
    expect(toggleElement).toBeInTheDocument();

    // Click to expand
    await user.click(toggleElement);

    // Click to collapse
    await user.click(toggleElement);
});
