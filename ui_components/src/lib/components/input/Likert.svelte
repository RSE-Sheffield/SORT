<script>
  import LikertRow from "./LikertRow.svelte";
  import LikertItem from "./LikertItem.svelte";

  let {config, value = $bindable(), viewerMode = false} = $props();

  if (value === null || value === undefined) {
    value = []
  }

  let compsValue = $state(value);
  $effect(() => {
    let output = [];
    for (let i = 0; i < config.sublabels.length; i++) {
      let outValue = "";
      if (i in compsValue) {
        outValue = compsValue[i];
      }
      output.push(outValue);
    }
    value = output;
  });

  let _likertRows = $state([]);
  let likertRows = $derived(_likertRows.filter(Boolean));

  let _likertItems = $state([]);
  let likertItems = $derived(_likertItems.filter(Boolean));


  export function validate() {
    let isValid = true;
    for(let i = 0; i < likertRows.length; i++){
        if(!likertRows[i].validate()){
          isValid = false;
        }
    }
    return isValid;
  }

</script>

<div class="form-label">
    {config.label}{#if config.required}<span style="color: red">*</span>{/if}
    {#if config.description || config.description.length > 0}<p class="form-text">{config.description}</p>{/if}
    <table class="table table-striped d-none d-sm-block" style="width: 100%;">
        <thead>
        <tr>
            <th>Statement</th>
            {#each config.options as option}
                <th scope="col">{option}</th>
            {/each}

        </tr>

        </thead>
        <tbody>
        {#each config.sublabels as sublabel, sublabelIndex }
            <tr>
                <LikertRow config={config}
                           sublabelIndex={sublabelIndex}
                           bind:value={compsValue[sublabelIndex]}
                           bind:this={_likertRows[sublabelIndex]}
                           viewerMode={viewerMode}
                />
            </tr>
        {/each}
        </tbody>
    </table>
    <div class="d-block d-sm-none">
        {#each config.sublabels as sublabel, sublabelIndex }
            <LikertItem config={config}
                           sublabelIndex={sublabelIndex}
                           bind:value={compsValue[sublabelIndex]}
                           bind:this={_likertItems[sublabelIndex]}
                            viewerMode={viewerMode}
            />

        {/each}
        <hr/>
    </div>
</div>
