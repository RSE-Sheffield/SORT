<script lang="ts">
  import {getUniqueIDArray} from "../../misc.svelte.ts";
  import DOMPurify  from "dompurify";

  let {config, value = $bindable(), viewerMode = false} = $props();

  const componentId = getUniqueIDArray(config.options.length);

  let isValid = $state(false);
  let isInvalid = $state(false);

  function setIsValid(valid: boolean) {
    isValid = valid;
    isInvalid = !valid;
  }

  export function validate() {
    if (config.required && !value) {
      setIsValid(false);
      return false;
    }

    setIsValid(true);
    return true;
  }
</script>
<div class={{"form-label":true }}>
    {config.label}{#if config.required}<span style="color: red">*</span>{/if}
    {#if config.description || config.description.length > 0}<p class="form-text">{@html DOMPurify.sanitize(config.description)}</p>{/if}
    {#each config.options as option, index}
        <div class="form-check">
            <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                   type="checkbox"
                   value={option}
                   bind:group={value}
                   aria-label={option}
                   id={componentId[index]}
                   disabled={viewerMode}
            />
            <label class="form-check-label" for={componentId[index]}>{option}</label>
            {#if config.options && index >= config.options.length - 1}
            <!-- Feedback on the last component only -->
            <div class="invalid-feedback">
                At least one option must be selected.
            </div>
            {/if}
        </div>
    {/each}
</div>
