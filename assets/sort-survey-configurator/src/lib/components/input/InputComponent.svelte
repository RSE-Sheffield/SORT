<script lang="ts" module>
    import {TextType} from "../../misc.svelte.js";

    export function getDefaultFieldConfig() {
        return {
            type: "text",
            label: "New Question",
            description: "Question description",
            required: true,
            sublabels: [], // Subquestions for likert
            options: [], // Options for Checkbox, Radio, Select and Likert
            // Text and Textarea options
            enforceValueConstraints: false,
            maxNumChar: 500,
            minNumValue: 0,
            maxNumValue: 100,
            textType: TextType.plain,
        };
    }
</script>
<script lang="ts">
    import Text from "./Text.svelte";
    import TextArea from "./TextArea.svelte";
    import Checkbox from "./Checkbox.svelte";
    import Radio from "./Radio.svelte";
    import Select from "./Select.svelte"
    import Likert from "./Likert.svelte";
    import OptionsList from "./OptionsList.svelte";

    //Constants
    const questionTypes = [
        {label: "Text", value: "text"},
        {label: "Textarea", value: "textarea"},
        {label: "Radio", value: "radio"},
        {label: "Checkbox", value: "checkbox"},
        {label: "Selector", value: "select"},
        {label: "Likert", value: "likert"},
    ]
    const renderComponentTypes = {
        text: Text,
        textarea: TextArea,
        radio: Radio,
        checkbox: Checkbox,
        select: Select,
        likert: Likert
    }
    const componentTypeText = new Set(["text", "textarea"])
    const componentTypeWithOptions = new Set(["radio", "checkbox", "select", "likert"]);
    const componentTypeWithSublabels = new Set(["likert"]);

    // Props
    let {
        config = $bindable(getDefaultFieldConfig()),
        editable = false,
        value = $bindable(),
        onEditRequest = (startEdit: boolean) => {
        },
        onDuplicateRequest = () => {
        },
        onDeleteRequest = () => {
        },
    } = $props();

    //Insert missing keys
    let defaultConfig = getDefaultFieldConfig()
    for (let key in defaultConfig) {
        if (!(key in config)) {
            config[key] = defaultConfig[key];
        }
    }

    // States
    let inEditMode = $state(false);


    let RenderedComponentType = $derived.by(() => {
        if (config.type in renderComponentTypes) {
            return renderComponentTypes[config.type];
        }
        return Text;
    })

    let renderedComponent = $state();

    export function validate() {
        console.log("Validating field" + config.label);
        if(renderedComponent){
            return renderedComponent.validate();
        }

        return false;
    }

    export function getValue() {
        return {name: config.name, value: value};
    }

    export function beginEdit() {
        inEditMode = true;
    }

    export function endEdit() {
        inEditMode = false;
    }


</script>

{#snippet enforceMaxChar()}
    <label class="form-label">
        Maximum characters
        <input type="number" class="form-control" bind:value={config.maxNumChar}/>
    </label>

    <div class="form-check form-switch">
        <label class="form-label">
            Enforce maximum characters
            <input class="form-check-input" type="checkbox" role="switch"
                   bind:checked={config.enforceValueConstraints}>
        </label>
    </div>
{/snippet}

<div>
    {#if editable && inEditMode}

        <div class="card mb-3">
            <div class="card-header" style="text-align: right">
                <button onclick={()=>{onEditRequest(false)}} class="btn btn-link btn-sm" aria-label="Close">
                    <i class='bx bx-radio-circle-marked'></i>
                    <i class='bx bx-collapse-vertical'></i> close
                </button>
            </div>
            <div class="card-body">

                <div class="row mb-3">
                    <div class="col-8">
                        <label class="form-label col-12">
                            Question label
                            <input type="text" class="form-control" bind:value={config.label}/>
                        </label>
                    </div>
                    <div class="col-4">
                        <label class="form-label col-12">
                            Question type
                            <select bind:value={config.type} class="form-select">
                                {#each questionTypes as questionType}
                                    <option value={questionType.value}>{questionType.label} </option>
                                {/each}
                            </select>
                        </label>
                    </div>
                </div>

                <div class="mb-3">
                    <label class="form-label col-12">
                        Description
                        <textarea class="form-control" bind:value={config.description}></textarea>
                    </label>
                </div>


                {#if componentTypeWithSublabels.has(config.type)}
                    <div class="mb-3">
                        <div class="form-label">Sublabels</div>
                        <OptionsList bind:options={config.sublabels} type={config.type}/>
                    </div>
                {/if}

                {#if componentTypeWithOptions.has(config.type)}
                    <div class="mb-3">
                        <div class="form-label">Options</div>
                        <OptionsList bind:options={config.options} type={config.type}/>
                    </div>
                {/if}

                {#if config.type === "text"}
                    <div class="row mb-3">
                        <div class="col">
                            <label class="form-label">Text type
                                <select bind:value={config.textType} class="form-select">
                                    <option value={TextType.plain}>Plain text</option>
                                    <option value={TextType.email}>Email</option>
                                    <option value={TextType.integer}>Whole numbers</option>
                                    <option value={TextType.decimals}>Number with decimals</option>
                                </select>
                            </label>
                        </div>
                        <div class="col">
                            {#if config.textType === TextType.plain}
                                {@render enforceMaxChar()}
                            {:else if config.textType === TextType.integer}
                                <label class="form-label">
                                    Minimum value
                                    <input type="number" class="form-control" bind:value={config.minNumValue}/>
                                </label>
                                <label class="form-label">
                                    Maximum value
                                    <input type="number" class="form-control" bind:value={config.maxNumValue}/>
                                </label>
                                <div class="form-check form-switch">
                                    <label class="form-label">
                                        Enforce value limits
                                        <input class="form-check-input" type="checkbox" role="switch"
                                               bind:checked={config.enforceValueConstraints}>
                                    </label>
                                </div>

                            {:else if config.textType === TextType.decimals}
                                <label class="form-label">
                                    Minimum value
                                    <input type="number" class="form-control" bind:value={config.minNumValue}/>
                                </label>
                                <label class="form-label">
                                    Maximum value
                                    <input type="number" class="form-control" bind:value={config.maxNumValue}/>
                                </label>
                                <div class="form-check form-switch">
                                    <label class="form-label">
                                        Enforce value limits
                                        <input class="form-check-input" type="checkbox" role="switch"
                                               bind:checked={config.enforceValueConstraints}>
                                    </label>
                                </div>
                            {/if}
                        </div>
                    </div>

                {/if}
                {#if config.type === "textarea"}
                    <div class="row mb-3">
                        <div class="col">
                            {@render enforceMaxChar()}
                        </div>
                    </div>
                {/if}


                <div class="form-check form-switch mb-3">
                    <label class="form-label">
                        Required
                        <input type="checkbox" class="form-check-input" role="switch" bind:checked={config.required}/>
                    </label>
                </div>

                <div>
                    <button class="btn btn-primary" onclick={() => {onDuplicateRequest()}}>Duplicate</button>
                    <button class="btn btn-danger" onclick={() => {onDeleteRequest()}}>Delete</button>
                </div>


            </div>
        </div>

    {:else if editable && !inEditMode}
        <a href="/assets/sort-survey-configurator/public" class="card mb-3 sort-form-component"
           onclick={(event)=>{event.preventDefault(); onEditRequest(true)}}>
            <div class="card-body">
                    <RenderedComponentType config={config}></RenderedComponentType>
            </div>
        </a>
    {:else}
            <RenderedComponentType config={config} bind:value={value} bind:this={renderedComponent}></RenderedComponentType>
    {/if}
</div>

<style>
    .sort-form-component{
        text-decoration: none;
    }
    .sort-form-component:hover {
        background: #cec3fa;
    }

</style>
