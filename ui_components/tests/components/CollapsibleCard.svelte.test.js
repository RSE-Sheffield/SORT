import {mount, unmount} from "svelte";
import {test} from 'vitest';
import CollapsibleCard from "../../src/lib/components/CollapsibleCard.svelte";

test("CollapsibleCard", () => {
    const component = mount(CollapsibleCard, {
        target: document.body,
    });
    unmount(component);
});
