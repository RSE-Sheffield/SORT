import {test} from "vitest";
import "@testing-library/jest-dom";
import {render} from "@testing-library/svelte";
import Checkbox from "../../../src/lib/components/input/Checkbox.svelte";

test("Checkbox", async () => {
    render(Checkbox, {
        props: {
            config: {
                description: "",
                options: [
                    "Yes, I agree to complete the survey"
                ]
            }
        }
    });
});
