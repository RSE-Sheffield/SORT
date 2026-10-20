<script lang="ts">
  import DOMPurify from "dompurify";
  import { getUniqueID, getUniqueIDArray } from "../../misc.svelte.ts";
  import RequiredBadge from "../RequiredBadge.svelte";
  import type { FieldConfig } from "../../interfaces.ts";

  interface Props {
    config: FieldConfig;
    value: string;
    viewerMode: boolean;
  }

  let { config, value = $bindable(), viewerMode = false }: Props = $props();

  const componentId = getUniqueIDArray(config.options.length);
  const otherOptionComponentId = getUniqueID();
  const defaultOtherValue =
    value && config.options.indexOf(value) < 0 ? value : "";

  // Sentinel used as the radio's value so it stays stable while the user types
  const OTHER_SENTINEL = "__other__";

  let isValid = $state<boolean | null>(null);
  let otherValue = $state(defaultOtherValue);
  let otherRadio: HTMLInputElement | null = $state(null);

  // When the component loads with a pre-existing custom value, select "Other"
  let radioGroup = $state(defaultOtherValue ? OTHER_SENTINEL : value);

  $effect(() => {
    // Keep the external `value` in sync:
    // - "Other" selected → expose the typed text
    // - standard option selected → expose the option string
    if (radioGroup === OTHER_SENTINEL) {
      value = otherValue;
    } else {
      value = radioGroup;
    }
  });

  export function validate() {
    if (config.hasOtherOption && otherRadio && otherRadio.checked && !value) {
      // Ensure there's always a value in the other option if it's selected
      isValid = false;
      return false;
    } else if (config.required && !value) {
      isValid = false;
      return false;
    }

    isValid = true;
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
    <RequiredBadge />
  {/if}
  {#if config.description && config.description.length > 0}<p class="form-text">
      {@html DOMPurify.sanitize(config.description)}
    </p>{/if}

  {#each config.options as option, index (index)}
    <div class="form-check">
      <input
        class={{
          "form-check-input": true,
          "is-valid": isValid === true,
          "is-invalid": isValid === false,
        }}
        type="radio"
        value={option}
        id={componentId[index]}
        bind:group={radioGroup}
        disabled={viewerMode}
      />
      <label class="form-check-label" for={componentId[index]}>{option}</label>
      {#if !config.hasOtherOption && config.options && index >= config.options.length - 1}
        <!-- Feedback on the last component only -->
        {@render errorElem()}
      {/if}
    </div>
  {/each}
  {#if config.hasOtherOption}
    <div class="form-check">
      <input
        class={{
          "form-check-input": true,
          "is-valid": isValid === true,
          "is-invalid": isValid === false,
        }}
        type="radio"
        value={OTHER_SENTINEL}
        id={otherOptionComponentId}
        bind:group={radioGroup}
        bind:this={otherRadio}
        disabled={viewerMode}
      />
      <label class="form-check-label" for={otherOptionComponentId}>Other</label>
      <input
        class="form-control"
        bind:value={otherValue}
        placeholder="Enter custom value"
        disabled={viewerMode}
        oninput={() => {
          radioGroup = OTHER_SENTINEL;
        }}
      />

      <!-- If there's an "Other" option, it's always the last element -->
      {@render errorElem()}
    </div>
  {/if}
</div>
