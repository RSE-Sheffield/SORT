<script lang="ts" module>
    import {type FieldConfig, TextType} from "../../interfaces.ts";


    export type MoveRequestHandler = (srcSectionIndex: number,
                                      srcFieldIndex: number,
                                      destSectionIndex: number,
                                      destFieldIndex: number) => void

    export function getDefaultFieldConfig(): FieldConfig {
        return {
            type: "text",
            label: "New Question",
            description: "",
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

    let isDragging = $state(false);
</script>
<script lang="ts">
    import type {Component} from "svelte";
    import Text from "./Text.svelte";
    import TextArea from "./TextArea.svelte";
    import Checkbox from "./Checkbox.svelte";
    import Radio from "./Radio.svelte";
    import Select from "./Select.svelte"
    import Likert from "./Likert.svelte";
    import OptionsList from "./OptionsList.svelte";
    import {clickOutside} from "../../misc.svelte";
    import {onMount} from "svelte";
    import PellEditor from "./PellEditor.svelte";
    import type {SurveyResponse} from "../../interfaces.ts";
    import grabHandleIcon from "../../../assets/grab_dots.svg"


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
    type InputComponents = Text | TextArea | Radio | Checkbox | Select | Likert;
    const componentTypeText = new Set(["text", "textarea"])
    const componentTypeWithOptions = new Set(["radio", "checkbox", "select", "likert"]);
    const componentTypeWithSublabels = new Set(["likert"]);

    interface Props {
        config: FieldConfig;
        value?: SurveyResponse;
        editable?: boolean;
        viewerMode?: boolean;
        fieldIndex?: number;
        sectionIndex?: number;
        onDuplicateRequest: () => void;
        onDeleteRequest: () => void;
        onMoveRequest: MoveRequestHandler;
    }


    // Props
    let {
        config = $bindable(),
        value = $bindable(),
        editable = false,
        viewerMode = false,
        fieldIndex = -1,
        sectionIndex = -1,
        onDuplicateRequest = () => {
        },
        onDeleteRequest = () => {
        },
        onMoveRequest = (srcSectionIndex, srcFieldIndex, destSectionIndex, destFieldIndex) => {
        },
        canDisableFields = false,
    }: Props = $props();
  
    // Some fields cannot be modified
    const readonly = config.readOnly;

    //Create a field config object or insert missing keys
    if (config === null || config === undefined) {
        config = getDefaultFieldConfig();
    } else {
        config = {
            ...getDefaultFieldConfig(),
            ...config,
        }
    }

    // States
    let inEditMode = $state(false);

    let hasDragOver = $state(false);


    let RenderedComponentType = $derived.by(() => {
        if (config.type in renderComponentTypes) {
            return renderComponentTypes[config.type];
        }
        return Text;
    })


    let renderedComponent: InputComponents | null | undefined = $state();

    export function validate() {
        // Skip disabled fields
        if (config.disabled) {
            return true;
        }
        console.log("Validating field" + (config?.label ?? "Undefined"));
        if (renderedComponent)
            return renderedComponent.validate();
        return false;
    }


    export function beginEdit() {
        if (editable)
            inEditMode = true;
    }

    export function endEdit() {
        inEditMode = false;
    }

    function onDragStartHandler(e: DragEvent) {
        hasDragOver = false;
        isDragging = true;
        if (e.dataTransfer) {
            e.dataTransfer.effectAllowed = "move"
            e.dataTransfer.setData("application/json", JSON.stringify({section: sectionIndex, field: fieldIndex}))
        }
    }

    function onDropHandler(e: DragEvent) {
        e.preventDefault();
        e.stopPropagation(); // Stop drop event propagating to the parent SectionComponent
        if (e.dataTransfer) {
            const moveSource = JSON.parse(e.dataTransfer.getData("application/json"));
            onMoveRequest(moveSource.section, moveSource.field, sectionIndex, fieldIndex)
        }
        isDragging = false;

    }

    function onDragOverHandler(e: DragEvent) {
        e.preventDefault();
        hasDragOver = true;
        if (e.dataTransfer)
            e.dataTransfer.dropEffect = "move";
    }

    function onDragLeaveHandler(){
        hasDragOver = false;
    }

    function onDragEndHandler() {
        endEdit();
        isDragging = false;
    }

    // Input label
    let title = readonly ? 'This field cannot be edited' : 'Click to edit field';

    $effect(()=>{
        if(!isDragging){
            hasDragOver = false;
        }
    })
</script>

{#snippet enforceMaxChar()}
    <label class="form-label">
        Maximum characters
        <input type="number" class="form-control" bind:value={config.maxNumChar} readonly={readonly}/>
    </label>

    <div class="form-check form-switch">
        <label class="form-label">
            Enforce maximum characters
            <input class="form-check-input" type="checkbox" role="switch"
                   bind:checked={config.enforceValueConstraints} readonly={readonly} disabled={readonly}>
        </label>
    </div>
{/snippet}

{#snippet readOnlyBadge()}
<span class="badge badge-secondary text-bg-secondary"
  title="This is a standard field and cannot be modified. You can hide this field by clicking the Disable option below.">
  Read only
</span>
{/snippet}

{#if editable && inEditMode}

    <div role="group"
         class={{"card": true, "mb-3": true, "drag-over-bg": hasDragOver}}
         ondrop={onDropHandler}
         ondragover={onDragOverHandler}
         use:clickOutside={()=>{endEdit()}}
    >
        <div class="card-header" style="display: flex; justify-content: space-between">
            <div></div>
            <button
                    class="btn btn-link"
                    draggable="true"
                    ondragstart={onDragStartHandler}
                    ondrop={onDropHandler}
                    ondragover={onDragOverHandler}
                    ondragend={onDragEndHandler}
                    ondragleave={onDragLeaveHandler}>
                <img src={grabHandleIcon} style="width: 1.5em; height: auto;" alt="Field drag drop handle" title="Drag to move this field">
            </button>
            <button onclick={()=>{endEdit()}} class="btn btn-link btn-sm" aria-label="Close">
                <i class='bx bx-radio-circle-marked'></i>
                <i class='bx bx-collapse-vertical'></i> close
            </button>
        </div>
        {#if config.disabled}
        <div class="alert alert-danger mb-0">
            <span class="badge badge-danger text-bg-danger"
            title="This field is deactivated and will not be shown in the survey.">
                Disabled
            </span>&nbsp;
            This field is deactivated and will not be shown in the survey.
        </div>
        {/if}
        {#if readonly }
        <div class="alert alert-warning" role="alert">
            {@render readOnlyBadge()}
            This field is a standard question and cannot be modified.
        </div>
        {/if}
        <div class="card-body">
            <div class="row mb-3">
                <div class="col-8">
                    <label class="form-label col-12">
                        Question label
                        <input type="text" class="form-control" bind:value={config.label} readonly={readonly} />
                    </label>
                </div>
                <div class="col-4">
                    <label class="form-label col-12">
                        Question type
                        <select bind:value={config.type} class="form-select" disabled={readonly}>
                            {#each questionTypes as questionType (questionType.value)}
                                <option value={questionType.value}>{questionType.label} </option>
                            {/each}
                        </select>
                    </label>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label col-12">
                    Description
                    <PellEditor bind:value={config.description} readonly={readonly}></PellEditor>
                </label>
            </div>


            {#if componentTypeWithSublabels.has(config.type)}
                <div class="mb-3">
                    <div class="form-label">Sublabels</div>
                    <OptionsList bind:options={config.sublabels} type={config.type} readonly={readonly}/>
                </div>
            {/if}

            {#if componentTypeWithOptions.has(config.type)}
                <div class="mb-3">
                    <div class="form-label">Options</div>
                    <OptionsList bind:options={config.options} type={config.type} readonly={readonly}/>
                </div>
            {/if}

            {#if config.type === "text"}
                <div class="row mb-3">
                    <div class="col">
                        <label class="form-label">Text type
                            <select bind:value={config.textType} class="form-select" disabled={readonly}>
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
                                <input type="number" class="form-control" bind:value={config.minNumValue} readonly={readonly}/>
                            </label>
                            <label class="form-label">
                                Maximum value
                                <input type="number" class="form-control" bind:value={config.maxNumValue} readonly={readonly}/>
                            </label>
                            <div class="form-check form-switch">
                                <label class="form-label">
                                    Enforce value limits
                                    <input class="form-check-input" type="checkbox" role="switch"
                                           bind:checked={config.enforceValueConstraints} readonly={readonly} disabled={readonly}>
                                </label>
                            </div>

                        {:else if config.textType === TextType.decimals}
                            <label class="form-label">
                                Minimum value
                                <input type="number" class="form-control" bind:value={config.minNumValue} readonly={readonly}>/>
                            </label>
                            <label class="form-label">
                                Maximum value
                                <input type="number" class="form-control" bind:value={config.maxNumValue} readonly={readonly}/>
                            </label>
                            <div class="form-check form-switch">
                                <label class="form-label">
                                    Enforce value limits
                                    <input class="form-check-input" type="checkbox" role="switch"
                                           bind:checked={config.enforceValueConstraints} readonly={readonly} disabled={readonly}/>
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

            <!-- Required switch -->
            <div class="form-check form-switch mb-3">
                <label class="form-label">
                    Required
                    <input type="checkbox" class="form-check-input" role="switch" bind:checked={config.required}/>
                </label>
            </div>

            {#if canDisableFields }
            <!-- Disabled switch -->
            <div class="form-check form-switch mb-3">
                <label class="form-label">
                    Disabled
                    <input type="checkbox" class="form-check-input" role="switch" bind:checked={config.disabled}/>
                </label>
            </div>
            {/if}

            <div>
                <button class="btn btn-primary" onclick={() => {onDuplicateRequest()}} title="Copy this field">
                    <i class="bx bx-duplicate"></i> Duplicate
                </button>
                {#if !readonly}
                <button class="btn btn-danger" onclick={() => {onDeleteRequest()}}><i class="bx bx-trash"></i> Delete</button>
                {/if}
            </div>
        </div>
    </div>

{:else if editable && !inEditMode}
    <a href="/assets/ui_components/public"
       title={title}
       aria-label={title}
       class={{"card": true, "mb-3": true, "sort-form-component": true, "drag-over-bg": hasDragOver}}
       draggable="true"
       ondragstart={onDragStartHandler}
       ondrop={onDropHandler}
       ondragover={onDragOverHandler}
       ondragleave={onDragLeaveHandler}
       ondragend={onDragEndHandler}
       onclick={(event)=>{event.preventDefault(); beginEdit()}}
    >
        <div class="card-body">
            {#if config.disabled}
            <span class="badge badge-danger text-bg-danger"
            title="This field is deactivated and will not be shown in the survey.">
                Disabled
            </span>
            {/if}
            {#if readonly }
            {@render readOnlyBadge()}
            {/if}
            <RenderedComponentType config={config}></RenderedComponentType>
        </div>
    </a>
{:else if config.disabled}
    <!-- This field is disabled -->
{:else}
    <RenderedComponentType config={config} bind:value={value} bind:this={renderedComponent}
                           viewerMode={viewerMode}></RenderedComponentType>
{/if}


<style>
    .sort-form-component {
        text-decoration: none;
    }

    .sort-form-component:hover {
        background: #cec3fa;
    }

    .drag-over-bg {
        background: #cd8bf8;
    }


</style>
