<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const parse = (h) => {
  let input = {}, result = {}
  try { input = JSON.parse(h.input_json) } catch { /* 忽略坏行 */ }
  try { result = JSON.parse(h.result_json) } catch { /* 忽略坏行 */ }
  return { ...h, input, result }
}
const opened = ref(null)
const openRow = async (h) => {
  opened.value = parse(await getJSON('/api/history/' + h.id))
}
onMounted(async () => { items.value = (await getJSON('/api/history')).items.map(parse) })
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <thead><tr><th>#</th><th>时间</th><th>起终</th><th>途经站(当时)</th><th>换乘</th><th>加价(当时)</th><th>应付</th></tr></thead>
      <tbody>
        <tr v-for="h in items" :key="h.id" style="cursor:pointer" @click="openRow(h)">
          <td>#{{ h.id }}</td>
          <td>{{ h.created_at }}</td>
          <td>{{ h.input.start }} → {{ h.input.end }}</td>
          <td>{{ h.result.path ? h.result.path.join(' → ') : '—' }}</td>
          <td>{{ h.result.transfer_count ?? '—' }}</td>
          <td>¥{{ h.result.surcharge_total ?? 0 }}</td>
          <td>¥{{ h.result.fare }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="opened" class="panel">
      <h3>记录 #{{ opened.id }} 当时结果</h3>
      <p>换乘 {{ opened.result.transfer_count }} · 加价 ¥{{ opened.result.surcharge_total }} · 基础 ¥{{ opened.result.base_fare }} · 应付 ¥{{ opened.result.fare }}</p>
      <p class="muted" v-if="opened.result.path">{{ opened.result.path.join(' → ') }}</p>
    </div>
  </div>
</template>
