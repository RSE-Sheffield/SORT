import {test} from "vitest";
import "@testing-library/jest-dom";
import {render} from "@testing-library/svelte";
import EditableTextArea from "../../../src/lib/components/input/EditableTextArea.svelte";

test("EditableTextArea", async () => {
    const value = "This is some text"
    render(EditableTextArea, {
        props: {
            value: value,
        }
    });
});
