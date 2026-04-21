import {test} from "vitest";
import "@testing-library/jest-dom";
import {render} from "@testing-library/svelte";
import Select from "../../../src/lib/components/input/Select.svelte";

test("Select", () => {
    render(Select, {
        props: {config: {description:"My select field", required: true}},
    });
});
