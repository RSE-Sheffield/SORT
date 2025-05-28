<script lang="ts">
    import * as _ from "lodash-es"
    import type {SurveyConfig, SurveyStats} from "../interfaces.ts";
    import LikertHistogram from "./graph/LikertHistogram.svelte";
    import {
        formatNumber,
        getHighestHistogramValue,
        getHistogramMean, getSortMaturityLabel,
    } from "../misc.svelte.ts";
    type QM = {
        index: number;
        mean: number;
    }

    interface Props {
        config: SurveyConfig;
        surveyStats: SurveyStats;
        sectionIndex: number,
        fieldIndex: number
    }
    let {config, surveyStats, sectionIndex, fieldIndex}: Props = $props();

    let sectionConfig = $derived(config.sections[sectionIndex]);
    let fieldConfig = $derived(config.sections[sectionIndex].fields[fieldIndex]);
    let questionMeanSorted: QM[] = $derived.by(()=>{
        const qm = [];
        for(let i =0; i < surveyStats.sections[sectionIndex].fields[fieldIndex].histograms.length; i++){
            qm.push({
                index: i,
                mean: getHistogramMean(surveyStats.sections[sectionIndex].fields[fieldIndex].histograms[i])
            })
        }
        return _.orderBy(qm, ["mean"], ["asc"]);
    })
    let strongestAreas: string = $derived.by(()=>{
        const strongestList = questionMeanSorted.slice(-2);
        const output: string[] = [];
        strongestList.map(qm => {
            output.push(fieldConfig.sublabels[qm.index]);
        })
        return output.join(", ");
    })
    let weakestAreas: string = $derived.by(()=>{
        const weakestList = questionMeanSorted.slice(0,2);
        const output: string[] = [];
        weakestList.map(qm => {
            output.push(fieldConfig.sublabels[qm.index]);
        })
        return output.join(", ");
    })

</script>
<p>
    Section {sectionConfig.title} demonstrates an overall score <strong>
    of {formatNumber(surveyStats.sections[sectionIndex].fields[fieldIndex].mean)} out of
    {getHighestHistogramValue(surveyStats.sections[sectionIndex].fields[fieldIndex].histograms[0])}</strong> indicating maturity
    ranking of <strong>{getSortMaturityLabel(surveyStats.sections[sectionIndex].fields[fieldIndex].mean)}</strong>.
    Areas of strength are demonstrated in questions <strong>{strongestAreas}</strong>.
    Areas of improvements are identified in questions <strong>{weakestAreas}</strong>.
</p>
<LikertHistogram fieldConfig={fieldConfig}
                                 fieldStats={surveyStats.sections[sectionIndex].fields[fieldIndex]}></LikertHistogram>
<table class="table table-bordered mt-4">
    <thead>
    <tr>

        <th scope="col" style="text-align: center">Statistic</th>
        <th scope="col" style="text-align: center">Value</th>

    </tr>
    </thead>
    <tbody>
    <tr>
        <td style="text-align: center">Mean</td>
        <td style="text-align: center">{formatNumber(surveyStats.sections[sectionIndex].fields[fieldIndex].mean)}</td>
    </tr>
    <tr>
        <td style="text-align: center">Min</td>
        <td style="text-align: center">{surveyStats.sections[sectionIndex].fields[fieldIndex].min}</td>
    </tr>
    <tr>
        <td style="text-align: center">Max</td>
        <td style="text-align: center">{surveyStats.sections[sectionIndex].fields[fieldIndex].max}</td>
    </tr>
    </tbody>
</table>
