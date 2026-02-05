<script lang="ts">
    import "./pell-override.scss"
    import * as pell from "pell"
    import DOMPurify from "dompurify";

    interface Props {
        value?: string | null;
    }

    let {
        value = $bindable(),
        readonly = false
    }: Props = $props();
    if (value === null || value === undefined) {
        value = "Placeholder";
    }

    function editor(dom: HTMLElement) {
        // Initialize pell on an HTMLElement
        const editor = pell.init({
            // <HTMLElement>, required
            element: dom,
            // <Function>, required
            // Use the output html, triggered by element's `oninput` event
            onChange: html => {
                value = DOMPurify.sanitize(html);
            },

            // <string>, optional, default = 'div'
            // Instructs the editor which element to inject via the return key
            defaultParagraphSeparator: 'div',

            // <boolean>, optional, default = false
            // Outputs <span style="font-weight: bold;"></span> instead of <b></b>
            styleWithCSS: true,

            // <Array[string | Object]>, string if overwriting, object if customizing/creating
            // action.name<string> (only required if overwriting)
            // action.icon<string> (optional if overwriting, required if custom action)
            // action.title<string> (optional)
            // action.result<Function> (required)
            // Specify the actions you specifically want (in order)
            actions: [
                'bold',
                'italic',
                'underline',
                'strikethrough',
                'heading1',
                'heading2',
                'paragraph',
                {
                    name: 'ulist',
                    icon: "<i class='bx  bx-list-ol' style='font-size: x-large'></i> ",
                    result: () => pell.exec('insertOrderedList')
                },
                {
                    name: 'ulist',
                    icon: "<i class='bx  bx-list-ul' style='font-size: x-large'></i>",
                    result: () => pell.exec('insertUnorderedList')
                },
                'line',
                {
                    name: 'link',
                    icon: "<i class='bx  bx-link' style='font-size: x-large'></i>",
                    result: () => {
                        const url = window.prompt('Enter the link URL')
                        if (url) pell.exec('createLink', url)
                    }
                },
                'image',

            ],

            // classes<Array[string]> (optional)
            // Choose your custom class names
            classes: {
                actionbar: 'pell-actionbar',
                button: 'pell-button',
                content: 'pell-content',
                selected: 'pell-button-selected'
            }
        });
        editor.content.innerHTML = value;

        // Disabled
        editor.content.contentEditable = !readonly;
    }
</script>

<div use:editor></div>


