<script lang="ts">
  import DOMPurify  from "dompurify";
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

<div class="likert-container card mb-4 shadow-sm">
    <div class="card-body">
        <div class="form-label mb-3">
            <h5 class="card-title">{config.label}{#if config.required}<span style="color: red">*</span>{/if}</h5>
            {#if config.description || config.description.length > 0}<p class="form-text text-muted">{@html DOMPurify.sanitize(config.description)}</p>{/if}
        </div>
        <div class="table-responsive">
            <table class="table table-striped table-hover d-none d-sm-block" style="width: 100%;">
                <thead class="table-light">
                <tr>
                    <th class="fw-bold">Statement</th>
                    {#each config.options as option, index (index)}
                        <th scope="col" class="text-center">{option}</th>
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
        </div>
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
</div>
