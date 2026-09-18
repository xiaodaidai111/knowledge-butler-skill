<template>
  <div ref="el" class="echart-root" :style="{ height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { init as initEChart } from '../lib/echarts.js'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '260px' },
  // 若提供该字段，点击图表元素时会将该字段对应的值作为事件抛出
  clickField: { type: String, default: '' }
})
const emit = defineEmits(['click'])

const el = ref(null)
let chart = null
let resizeObserver = null

const render = () => {
  // 只守 chart 不够：父组件的 option 在数据为空或组件卸载途中可能瞬间算成 null，
  // 此时 setOption(null, true) 会在 echarts 内部 legacyCopyOverallTrans 里抛
  // "Cannot read properties of null (reading '0')"。这里把 option 一起守掉。
  if (!chart || !props.option || typeof props.option !== 'object') return
  chart.setOption(props.option, true)
}

onMounted(async () => {
  await nextTick()
  if (!el.value) return
  chart = initEChart(el.value)
  chart.setOption(props.option, true)
  if (props.clickField) {
    chart.on('click', (params) => {
      if (!params) return
      const data = params.data || {}
      if (props.clickField in data) emit('click', data[props.clickField])
      else if (params.name) emit('click', params.name)
    })
  }
  // 容器尺寸变化时自适应（面板显隐、侧栏折叠等场景）
  // 尺寸为 0 时不能 resize：面板切走/hover 折叠的瞬间，echarts 会在
  // legacyCopyOverallTrans 里拿到 null 的坐标系变换矩阵并抛
  // "Cannot read properties of null (reading '0')"。
  resizeObserver = new ResizeObserver(() => {
    const node = el.value
    if (!chart || !node?.isConnected) return
    if (node.clientWidth === 0 || node.clientHeight === 0) return
    chart.resize()
  })
  resizeObserver.observe(el.value)
})

watch(() => props.option, () => render(), { deep: true })

onBeforeUnmount(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  if (chart) { chart.dispose(); chart = null }
})

defineExpose({ resize: () => chart && chart.resize() })
</script>

<style scoped>
.echart-root {
  width: 100%;
  min-height: 0;
}
</style>
