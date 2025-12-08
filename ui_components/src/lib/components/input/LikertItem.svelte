<script lang="ts">
  import {getUniqueIDArray} from "../../misc.svelte.ts";

  let {config, sublabelIndex, value = $bindable(), viewerMode = false} = $props();

  const radioIds = getUniqueIDArray(config.options.length);

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

<fieldset class={{
  "bg-light": sublabelIndex % 2 < 1,
  "pb-3": true,
  "pt-3": true,
  "ps-2": true,
  "pe-2": true,
  "border-0": true}}
     style="border-bottom: black 1px">

    <legend class="row mb-2">
        <div class="col">
            <span class={{"is-valid": isValid, "is-invalid": isInvalid}}>{config.sublabels[sublabelIndex]}</span>
            <span class="invalid-feedback">A value must be selected</span>
        </div>
    </legend>
    <div class="row">
        {#each config.options as option, index (option)}
            <div class="col">
                <div class="form-check">
                    <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                           type="radio"
                           id={radioIds[index]}
                           value={option}
                           bind:group={value}
                           required={config.required}
                           disabled={viewerMode}
                           aria-label="Score {option}"
                    />
                    <label class="form-check-label" for={radioIds[index]}>
                        Score {option}
                    </label>
                </div>
            </div>
        {/each}
    </div>

</fieldset>


