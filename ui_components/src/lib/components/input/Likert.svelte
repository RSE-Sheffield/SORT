<script lang="ts">
  import DOMPurify  from "dompurify";
  import LikertRow from "./LikertRow.svelte";
  import LikertItem from "./LikertItem.svelte";
  import RequiredBadge from "../RequiredBadge.svelte";


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

  let _likertRows: LikertRow[] = $state([]);
  let likertRows = $derived(_likertRows.filter(Boolean));

  let _likertItems: LikertItem[] = $state([]);
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
    <span id="question-label">{config.label}</span>{#if config.required}<RequiredBadge />{/if}
    {#if config.description || config.description.length > 0}<p class="form-text">{@html DOMPurify.sanitize(config.description)}</p>{/if}
    <table class="table table-striped d-none d-sm-block" style="width: 100%;">
        <thead>
        <tr>
            <th>Statement</th>
            {#each config.options as option, index (index)}
                <th scope="col">{option}</th>
            {/each}

        </tr>

        </thead>
        <tbody>
        {#each config.sublabels as sublabel, sublabelIndex (sublabelIndex)}
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
        {#each config.sublabels as sublabel, sublabelIndex (sublabelIndex)}
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
