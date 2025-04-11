<script lang="ts">
    import * as _ from "lodash-es"

    interface ActionItem {
        currentPosition: string;
        action: string;
        outcomes: string;
        personResponsible: string;
        deadline: string;
    }


    let {data, updateUrl, csrf, viewOnly = false} = $props();
    let initData = []
    if (typeof data === "string" && data.length > 0) {
        try {
            initData = JSON.parse(data);
        } catch (e) {
            console.log(e);
        }

    } else if (Array.isArray(data)) {
        initData = data
    }

    let actions: ActionItem[] = $state(initData);
    let actionStr = $derived(JSON.stringify(actions));


    function handleAddItem() {
        actions.push({
            currentPosition: "",
            action: "",
            outcomes: "",
            personResponsible: "",
            deadline: ""
        })
    }

    function handleDeleteRow(index) {
        actions = actions.toSpliced(index, 1);
    }
</script>
<div>
    <div class="table-responsive">
        <table class="table" style="width: 100%">
            <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Current position</th>
                <th scope="col">Proposed action</th>
                <th scope="col">Measurable outcomes</th>
                <th scope="col">Person responsible</th>
                <th scope="col">Deadline</th>

                <th scope="col"></th>
            </tr>
            </thead>
            <tbody>
            {#each actions as action, index}
                {#if viewOnly}
                    <tr>
                        <th scope="row">{index}</th>
                        <td>{action.currentPosition}</td>
                        <td>{action.action}</td>
                        <td>{action.outcomes}</td>
                        <td>{action.personResponsible}</td>
                        <td>{action.deadline}</td>
                        <td></td>
                    </tr>
                {:else}
                    <tr>
                        <th scope="row">{index}</th>
                        <td><textarea class="form-control" bind:value={action.currentPosition}></textarea></td>
                        <td><textarea class="form-control" bind:value={action.action}></textarea></td>
                        <td><textarea class="form-control" bind:value={action.outcomes}></textarea></td>
                        <td><input type="text" class="form-control" bind:value={action.personResponsible}/></td>
                        <td><input type="date" class="form-control" bind:value={action.deadline}/></td>
                        <td>
                            <button class="btn btn-danger" onclick={()=>{handleDeleteRow(index)}} title="Delete"
                                    aria-label="Delete row">
                                <i class='bx bx-x'></i>
                            </button>
                        </td>
                    </tr>
                {/if}
            {/each}
            </tbody>
        </table>
    </div>
    {#if !viewOnly}
        <div class="d-flex justify-content-end">
            <button class="btn-primary btn" onclick={handleAddItem}><i class='bx bx-plus'></i> Add item to plan</button>
        </div>
    {/if}

    {#if !viewOnly}
        <div>
            <form method="post" action={updateUrl}>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}"/>
                <input type="hidden" name="data" value={actionStr}/>
                <button type="submit" name="submit" value="Submit" class="btn btn-primary"><i class="bx bx-save"></i>
                    Save plan
                </button>
            </form>
        </div>
    {/if}


</div>
