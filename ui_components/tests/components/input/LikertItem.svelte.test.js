import {test} from "vitest";
import "@testing-library/jest-dom";
import {render} from "@testing-library/svelte";
import LikertItem from "../../../src/lib/components/input/LikertItem.svelte";

test("LikertItem", async () => {
    render(LikertItem, {
        props: {
            config: {
                options: [
                    "1", "2", "3", "4", "5"
                ],
                sublabelIndex: 0,
                sublabels: ["My sub-label",],
            }
        }
    });
});
