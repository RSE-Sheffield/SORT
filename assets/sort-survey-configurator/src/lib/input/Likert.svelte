<script>
  import LikertRow from "./LikertRow.svelte";

  let {config, value = $bindable()} = $props();

  if(value === null || value === undefined){
    value = []
  }

  let compsValue = $state(value);
  $effect(()=>{
    let output = [];
    for(let i = 0; i < config.sublabels.length; i++){
      let outValue = "";
      if(i in compsValue){
        outValue = compsValue[i];
      }
      output.push(outValue);
    }
    value = output;

  });

</script>

<div>
<table class="table" style="width: 100%;">
    <thead>
        <tr>
            <th ></th>
            {#each config.options as option}
                <th scope="col">{option}</th>
            {/each}

        </tr>

    </thead>
    <tbody>

    {#each config.sublabels as sublabel, sublabelIndex }
        <tr>
            <th >{sublabel}</th>
            <LikertRow config={config} sublabelIndex={sublabelIndex} bind:value={compsValue[sublabelIndex]} />
        </tr>
    {/each}

    </tbody>
</table>

</div>
