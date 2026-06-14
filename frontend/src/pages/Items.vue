<template>
  <div>
    <h1 class="page-title">Items / Products</h1>

    <!-- Custom Columns -->
    <div class="card">
      <div style="font-size:14px;font-weight:600;margin-bottom:4px;">Custom columns</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">Drag to reorder. They appear in this order on items and invoices.</div>

      <div id="col-list">
        <div v-if="!store.customColumns.length" style="font-size:12px;color:var(--text-tertiary);margin-bottom:10px;">No custom columns yet.</div>
        <div
          v-for="(col, idx) in store.customColumns" :key="col.id"
          class="col-row"
          draggable="true"
          :class="{ 'drag-over': dragOver === idx }"
          @dragstart="dragStart(idx)"
          @dragover.prevent="dragOver = idx"
          @dragleave="dragOver = null"
          @drop="dropCol(idx)"
        >
          <i class="ti ti-grip-vertical drag-handle"></i>
          <span class="col-name">{{ col.name }}</span>
          <span class="col-pos">{{ idx === 0 ? 'after HSN code' : 'after "' + store.customColumns[idx-1].name + '"' }}</span>
          <button class="btn btn-sm btn-danger" @click="removeCol(col.id)" style="padding:3px 7px;"><i class="ti ti-trash"></i></button>
        </div>
      </div>

      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <input v-model="newColName" placeholder="Column name (e.g. Weight, Grade, Colour)" style="width:270px;padding:7px 10px;font-size:13px;border-radius:7px;border:1px solid #d1d5db;">
        <button class="btn btn-sm btn-primary" @click="addCol"><i class="ti ti-plus"></i> Add column</button>
      </div>
    </div>

    <!-- Add / Edit Item -->
    <div class="card">
      <div style="font-size:14px;font-weight:600;margin-bottom:12px;">{{ editingId ? 'Edit item' : 'Add item' }}</div>
      <div class="form-row cols-3">
        <div class="form-group"><label>Item name</label><input v-model="form.name" placeholder="Steel rod 10mm"></div>
        <div class="form-group"><label>Item / material code</label><input v-model="form.code" placeholder="STL-ROD-10"></div>
        <div class="form-group"><label>HSN code</label><input v-model="form.hsn" placeholder="7214"></div>
      </div>

      <!-- Custom column inputs - appear between HSN and Unit/Price -->
      <div v-if="store.customColumns.length" class="form-row" :style="`grid-template-columns: repeat(${Math.min(store.customColumns.length, 3)}, 1fr)`">
        <div v-for="(col, idx) in store.customColumns" :key="col.id" class="form-group">
          <label>{{ col.name }}</label>
          <input v-model="form.custom_values[idx]" :placeholder="col.name">
        </div>
      </div>

      <div class="form-row cols-2">
        <div class="form-group"><label>Unit</label>
          <select v-model="form.unit">
            <option v-for="u in units" :key="u">{{ u }}</option>
          </select>
        </div>
        <div class="form-group"><label>Unit price (₹)</label><input v-model.number="form.price" type="number" placeholder="850"></div>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-primary" @click="saveItem" :disabled="saving">
          <i :class="editingId ? 'ti ti-device-floppy' : 'ti ti-plus'"></i> {{ saving ? 'Saving...' : (editingId ? 'Update item' : 'Add item') }}
        </button>
        <button v-if="editingId" class="btn" @click="cancelEdit"><i class="ti ti-x"></i> Cancel</button>
      </div>
    </div>

    <!-- Items Table -->
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Code</th><th>HSN</th>
              <th v-for="col in store.customColumns" :key="col.id">{{ col.name }}</th>
              <th>Unit</th><th>Price (₹)</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!store.items.length"><td :colspan="6 + store.customColumns.length"><div class="empty">No items yet</div></td></tr>
            <tr v-for="item in store.items" :key="item.id">
              <td style="font-weight:600;">{{ item.name }}</td>
              <td style="font-family:monospace;font-size:12px;">{{ item.code }}</td>
              <td style="font-family:monospace;font-size:12px;">{{ item.hsn }}</td>
              <td v-for="(col, ci) in store.customColumns" :key="col.id" style="color:var(--text-muted);">
                {{ item.custom_values?.[ci] || '—' }}
              </td>
              <td style="color:var(--text-muted);">{{ item.unit }}</td>
              <td>{{ fmt(item.price) }}</td>
              <td>
                <button class="btn btn-sm" @click="editItem(item)"><i class="ti ti-pencil"></i></button>
                <button class="btn btn-sm btn-danger" @click="delItem(item.id)"><i class="ti ti-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import axios from 'axios'
import { useAppStore } from '../store'

const store = useAppStore()
const saving = ref(false)
const toast = ref('')
const newColName = ref('')
const dragSrc = ref(null)
const dragOver = ref(null)
const units = ['Nos', 'Kg', 'Meter', 'Sq.ft', 'Litre', 'Box', 'Set', 'MT']

const form = ref({ name: '', code: '', hsn: '', price: '', unit: 'Nos', custom_values: [] })
const editingId = ref(null)

watch(() => store.customColumns.length, (len) => {
  while (form.value.custom_values.length < len) form.value.custom_values.push('')
})

const fmt = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function showToast(msg) { toast.value = msg; setTimeout(() => toast.value = '', 2500) }

async function addCol() {
  if (!newColName.value.trim()) return
  await axios.post('/custom-columns', { name: newColName.value.trim() })
  newColName.value = ''
  await store.loadCustomColumns()
  showToast('Column added!')
}

async function removeCol(id) {
  await axios.delete('/custom-columns/' + id)
  await store.loadCustomColumns()
}

function dragStart(idx) { dragSrc.value = idx }

async function dropCol(toIdx) {
  dragOver.value = null
  if (dragSrc.value === null || dragSrc.value === toIdx) return
  const cols = [...store.customColumns]
  const [moved] = cols.splice(dragSrc.value, 1)
  cols.splice(toIdx, 0, moved)
  store.customColumns = cols
  await axios.post('/custom-columns/reorder', { ids: cols.map(c => c.id) })
  dragSrc.value = null
}

async function saveItem() {
  if (!form.value.name || !form.value.price) return showToast('Name and price required')
  saving.value = true
  try {
    if (editingId.value) {
      await axios.put('/items/' + editingId.value, form.value)
      showToast('Item updated!')
      editingId.value = null
    } else {
      await axios.post('/items', form.value)
      showToast('Item added!')
    }
    await store.loadItems()
    form.value = { name: '', code: '', hsn: '', price: '', unit: 'Nos', custom_values: store.customColumns.map(() => '') }
  } catch (e) {
    showToast('Error saving item')
  } finally {
    saving.value = false
  }
}

function editItem(item) {
  editingId.value = item.id
  form.value = {
    name: item.name,
    code: item.code || '',
    hsn: item.hsn || '',
    price: item.price,
    unit: item.unit || 'Nos',
    custom_values: store.customColumns.map((c, i) => item.custom_values?.[i] || ''),
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  form.value = { name: '', code: '', hsn: '', price: '', unit: 'Nos', custom_values: store.customColumns.map(() => '') }
}

async function delItem(id) {
  if (!confirm('Delete this item?')) return
  await axios.delete('/items/' + id)
  await store.loadItems()
}
</script>