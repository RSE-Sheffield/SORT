<script>
    let { config, sublabelIndex, value = $bindable() } = $props();
</script>

{#each config.options as option, optionIndex }
    <td>
        <div class="form-check">
            <input class="form-check-input" type="radio" value={option} name={config.name + "__" + Number(sublabelIndex).toString()} bind:group={value}/>
        </div>
    </td>
{/each}
