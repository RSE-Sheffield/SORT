<script lang="ts">
  import DOMPurify from "dompurify";
  import {getUniqueID, getUniqueIDArray} from "../../misc.svelte.ts";
  import RequiredBadge from "../RequiredBadge.svelte";
  import type {FieldConfig} from "../../interfaces.ts";

  interface Props {
    config: FieldConfig;
    value: string;
    viewerMode: boolean;
  }

  let {config, value = $bindable(), viewerMode = false}: Props = $props();

  const componentId = getUniqueIDArray(config.options.length);
  const otherOptionComponentId = getUniqueID();
  const defaultOtherValue = value && config.options.indexOf(value) < 0 ? value : "";

  let isValid = $state(false);
  let isInvalid = $state(false);
  let otherValue = $state(defaultOtherValue);
  let otherRadio: HTMLInputElement|null= $state(null);


  $effect(() =>{
    // Prevent the option de-selecting itself when custom value changes
    if(config.hasOtherOption && value &&  config.options.indexOf(value) < 0)
        value = otherValue;
  })

  function setIsValid(valid: boolean) {
    isValid = valid;
    isInvalid = !valid;
  }

  export function validate() {
    if (config.hasOtherOption && otherRadio && otherRadio.checked && !value){
      // Ensure there's always a value in the other option if it's selected
      setIsValid(false);
      return false;
    }
    else if (config.required && !value) {
      setIsValid(false);
      return false;
    }

    setIsValid(true);
    return true;
  }

</script>
{#snippet errorElem()}
    <div class="invalid-feedback">
        {#if config.hasOtherOption && !value && !otherValue}
            The "Other" value must not be empty
        {:else}
            At least one option must be selected.
        {/if}
    </div>
{/snippet}
<div class="form-label">
    {config.label}
    {#if config.required}
        <RequiredBadge/>
    {/if}
    {#if config.description || config.description.length > 0}<p
            class="form-text">{@html DOMPurify.sanitize(config.description)}</p>{/if}

    {#each config.options as option, index (index)}
        <div class="form-check">
            <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                   type="radio"
                   value={option}
                   id={componentId[index]}
                   bind:group={value}
                   placeholder={option}
                   disabled={viewerMode}
            />
            <label class="form-check-label" for="{componentId[index]}">{option}</label>
            {#if !config.hasOtherOption && config.options && index >= config.options.length - 1}
                <!-- Feedback on the last component only -->
                {@render errorElem()}
            {/if}
        </div>
    {/each}
    {#if config.hasOtherOption}
        <div>
            <div class="form-check">
                <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                       type="radio"
                       value={otherValue}
                       id={otherOptionComponentId}
                       bind:group={value}
                       bind:this={otherRadio}
                       disabled={viewerMode}

                />
                <label class="form-check-label" for="{otherOptionComponentId}">Other</label>
                <input
                        class="form-control"
                        bind:value={otherValue} placeholder="Enter custom value"
                />

                <!-- If there's an "Other" option, it's always the last element -->
                {@render errorElem()}
            </div>
        </div>
    {/if}
</div>



