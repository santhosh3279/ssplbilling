<template>
  <div class="rounded-lg bg-[var(--color-surface)] p-3">
    <div class="mb-1 text-xs font-semibold">{{ spec.title }}</div>
    <div ref="el"></div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Chart } from 'frappe-charts/dist/frappe-charts.min.esm'

// spec: { chart_type: 'bar'|'line'|'pie', title, labels: [], datasets: [{ name, values }] }
// built on the server (ai_chat_export.make_chart) from live data, never typed by the model.
const props = defineProps({ spec: { type: Object, required: true } })
const el = ref(null)
let chart = null

const inr = (v) => '₹' + Math.round(Number(v) || 0).toLocaleString('en-IN')

onMounted(() => {
  const { chart_type, labels, datasets } = props.spec
  const money = !/qty/i.test(datasets.map((d) => d.name).join(' '))
  chart = new Chart(el.value, {
    type: chart_type === 'line' ? 'line' : chart_type === 'pie' ? 'pie' : 'bar',
    height: 260,
    data: {
      labels,
      // A pie shows one series.
      datasets: chart_type === 'pie' ? datasets.slice(0, 1) : datasets,
    },
    colors: ['#3b82f6', '#16a34a', '#f97316', '#a855f7', '#dc2626'],
    axisOptions: { xIsSeries: chart_type === 'line', xAxisMode: 'tick' },
    lineOptions: { hideDots: labels.length > 40, regionFill: 0 },
    barOptions: { spaceRatio: 0.4 },
    tooltipOptions: { formatTooltipY: (v) => (money ? inr(v) : Number(v).toLocaleString('en-IN')) },
  })
})

onBeforeUnmount(() => chart?.destroy?.())
</script>
