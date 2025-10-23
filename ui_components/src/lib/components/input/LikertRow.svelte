<script lang="ts">
  import {getUniqueID, getUniqueIDArray} from "../../misc.svelte.ts";

  let {config, sublabelIndex, value = $bindable(), viewerMode = false} = $props();

  const radioIds = getUniqueIDArray(config.options.length);
  const groupLabelId = getUniqueID();

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

<td>
    <span id={groupLabelId} class={{"is-valid": isValid, "is-invalid": isInvalid}}>{config.sublabels[sublabelIndex]}</span>
    <span class="invalid-feedback">A value must be selected</span>
</td>
{#each config.options as option, index (option)}
    <td>
        <div class="form-check" role="group" aria-labelledby={groupLabelId}>
            <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                   type="radio"
                   id={radioIds[index]}
                   value={option}
                   bind:group={value}
                   required={config.required}
                   disabled={viewerMode}
                   aria-label="Score {option}"
            />
            <label class="form-check-label visually-hidden" for={radioIds[index]}>
                Score {option}
            </label>
        </div>
    </td>
{/each}
