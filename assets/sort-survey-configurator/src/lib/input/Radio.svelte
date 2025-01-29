<script>
  let {config, value = $bindable()} = $props();
</script>

{#each config.options as option}
<div class="form-check">
    <label class="form-check-label">
        {option}
        <input class="form-check-input" type="radio" name={config.name} value={option} bind:group={value}>
    </label>
</div>
{/each}
