<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'

const ladder = ref([])
const rules = ref([])
const lines = ref([])
const blank = { from_line: '', to_line: '', surcharge: 1 }
const form = ref({ ...blank })
const editingId = ref(null)
const error = ref('')

const load = async () => {
  ladder.value = (await getJSON('/api/fare-rules')).items
  rules.value = (await getJSON('/api/transfer-rules')).items
  const stations = (await getJSON('/api/stations')).items
  lines.value = [...new Set(stations.map((s) => s.line).filter(Boolean))]
}
onMounted(load)

const submit = async () => {
  error.value = ''
  try {
    if (editingId.value) {
      await putJSON(`/api/transfer-rules/${editingId.value}`, form.value)
    } else {
      await postJSON('/api/transfer-rules', { ...form.value, active: true })
    }
    editingId.value = null
    form.value = { ...blank }
    await load()
  } catch (e) {
    error.value = e.message
  }
}
const edit = (r) => {
  error.value = ''
  editingId.value = r.id
  form.value = { from_line: r.from_line, to_line: r.to_line, surcharge: r.surcharge }
}
const cancelEdit = () => {
  editingId.value = null
  form.value = { ...blank }
}
const deactivate = async (r) => {
  error.value = ''
  try {
    await postJSON(`/api/transfer-rules/${r.id}/deactivate`, {})
    await load()
  } catch (e) {
    error.value = e.message
  }
}
const enable = async (r) => {
  error.value = ''
  try {
    await putJSON(`/api/transfer-rules/${r.id}`, { active: true })
    await load()
  } catch (e) {
    error.value = e.message
  }
}
</script>
<template>
  <div class="page">
    <h1>票价阶梯(按站数)</h1>
    <table><thead><tr><th>最多站数</th><th>票价</th></tr></thead>
      <tbody><tr v-for="r in ladder" :key="r.id"><td>{{ r.max_hops ?? '以上' }}</td><td>{{ r.price }}</td></tr></tbody></table>

    <h1>换乘加价规则</h1>
    <div class="panel">
      <select v-model="form.from_line">
        <option value="" disabled>离开线路</option>
        <option v-for="l in lines" :key="l" :value="l">{{ l }}</option>
      </select>
      →
      <select v-model="form.to_line">
        <option value="" disabled>进入线路</option>
        <option v-for="l in lines" :key="l" :value="l">{{ l }}</option>
      </select>
      加价 <input v-model.number="form.surcharge" type="number" min="0" step="0.5" style="width:6rem" />
      <button :disabled="!form.from_line || !form.to_line" @click="submit">
        {{ editingId ? `保存 #${editingId}` : '新增规则' }}
      </button>
      <button v-if="editingId" class="ghost" @click="cancelEdit">取消</button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
    <table>
      <thead><tr><th>#</th><th>离开线路</th><th>进入线路</th><th>加价</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="r in rules" :key="r.id" :class="{ muted: !r.active }">
          <td>#{{ r.id }}</td><td>{{ r.from_line }}</td><td>{{ r.to_line }}</td><td>¥{{ r.surcharge }}</td>
          <td>{{ r.active ? '启用' : '停用' }}</td>
          <td>
            <button class="ghost" @click="edit(r)">编辑</button>
            <button v-if="r.active" class="ghost" @click="deactivate(r)">停用</button>
            <button v-else class="ghost" @click="enable(r)">启用</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
