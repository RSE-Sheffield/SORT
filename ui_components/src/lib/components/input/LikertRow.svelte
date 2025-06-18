<script lang="ts">

  let {config, sublabelIndex, value = $bindable(), viewerMode = false} = $props();

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
    <span class={{"is-valid": isValid, "is-invalid": isInvalid}}>{config.sublabels[sublabelIndex]}</span>
    <span class="invalid-feedback">A value must be selected</span>
</td>
{#each config.options as option (option)}
    <td>
        <div class="form-check">
            <input class={{"form-check-input": true, "is-valid": isValid, "is-invalid": isInvalid}}
                   type="radio"
                   value={option}
                   bind:group={value}
                   required={config.required}
                   placeholder={option}
                   disabled={viewerMode}
            />
        </div>
    </td>
{/each}
