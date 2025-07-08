import {test} from "vitest";
import "@testing-library/jest-dom";
import {render} from "@testing-library/svelte";
import Radio from "../../../src/lib/components/input/Radio.svelte";

test("Radio", () => {
    render(Radio, {
        props: {config: {description: "My radio field", options: ["Option A", "Option B", "Option C"]}},
    });
});
