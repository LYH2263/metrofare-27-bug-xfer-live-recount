<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const persist = ref(false)
const out = ref(null)
const error = ref('')
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
const run = async () => {
  error.value = ''
  try {
    out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: persist.value })
  } catch (e) {
    error.value = e.message
  }
}
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
      <label class="muted"><input type="checkbox" v-model="persist" /> 写入记录</label>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p class="path-line">
          <template v-for="(st, i) in out.path" :key="i">
            <span class="station-chip">{{ st }}</span><span v-if="i < out.path.length - 1" class="edge-line">—{{ out.edge_lines[i] }}→</span>
          </template>
        </p>
        <p v-if="out.transfer_count > 0">
          换乘 {{ out.transfer_count }} 次:
          <span v-for="(t, i) in out.transfers" :key="i" class="transfer-chip">
            在 {{ t.at }} 由 {{ t.from_line }} 换 {{ t.to_line }}<template v-if="t.surcharge">(+¥{{ t.surcharge }})</template>
          </span>
        </p>
        <p v-else class="muted">全程同线,无需换乘</p>
        <p>站数 {{ out.hops }} · 基础票价 ¥{{ out.base_fare }} · 加价合计 ¥{{ out.surcharge_total }}</p>
        <p>应付 <span class="hero-num">¥{{ out.fare }}</span><span v-if="out.run_id" class="muted"> · 已落库 #{{ out.run_id }}</span></p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
