<template>
  <div>
    <h1 class="page-title">New Invoice</h1>
    <div class="card">
      <div class="form-row cols-2">
        <div class="form-group"><label>Invoice number</label><input v-model="invoiceNumber"></div>
        <div class="form-group"><label>Date</label><input v-model="invDate" type="date"></div>
      </div>
      <div class="form-row cols-1">
        <div class="form-group"><label>PO Number (optional)</label><input v-model="poNumber" placeholder="Customer's Purchase Order number"></div>
      </div>
      <div class="form-row cols-1">
        <div class="form-group">
          <label>Customer</label>
          <select v-model="selectedCustomerId" @change="onCustomerChange">
            <option value="">— select customer —</option>
            <option v-for="c in store.customers" :key="c.id" :value="c.id">{{ c.name }} ({{ c.gstin }})</option>
          </select>
        </div>
      </div>

      <div v-if="selectedCustomer" class="cust-bar show">
        GSTIN: <strong>{{ selectedCustomer.gstin }}</strong> &nbsp;|&nbsp;
        State: <strong>{{ selectedCustomer.state }}</strong> &nbsp;|&nbsp;
        Tax: <strong :style="{color: isIntra ? 'var(--success-text)' : 'var(--warn-text)'}">{{ isIntra ? 'CGST + SGST (intra-state)' : 'IGST (inter-state)' }}</strong>
      </div>

      <div style="font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Items</div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">
        Search by item name, code, HSN, or any custom field (e.g. drawing no).
      </div>

      <div v-for="(line, idx) in lines" :key="idx" class="inv-line">
        <div class="lf line-num">
          <span class="line-num-badge">{{ idx + 1 }}</span>
        </div>
        <div class="lf item-search-wrap" style="flex:2;min-width:180px;position:relative;">
          <label>Item (search by name / code / HSN / drg no)</label>
          <input
            v-model="line.searchText"
            @input="onSearchInput(line)"
            @focus="line.showDropdown = true"
            @blur="onBlur(line)"
            placeholder="Type to search..."
            autocomplete="off"
          >
          <div v-if="line.showDropdown && filteredItems(line).length" class="item-dropdown">
            <div
              v-for="it in filteredItems(line)" :key="it.id"
              class="item-option"
              @mousedown.prevent="selectItem(line, it)"
            >
              <div class="item-option-name">{{ it.name }}</div>
              <div class="item-option-meta">
                <span v-if="it.code">Code: {{ it.code }}</span>
                <span v-if="it.hsn">HSN: {{ it.hsn }}</span>
                <span v-for="(val, ci) in (it.custom_values || [])" :key="ci">
                  <template v-if="val">{{ store.customColumns[ci]?.name }}: {{ val }}</template>
                </span>
                <span style="margin-left:auto;font-weight:600;">₹{{ it.price }}</span>
              </div>
            </div>
          </div>
          <div v-else-if="line.showDropdown && line.searchText && !filteredItems(line).length" class="item-dropdown">
            <div class="item-option" style="color:var(--text-muted);cursor:default;">No matching items</div>
          </div>
        </div>
        <div class="lf"><label>HSN</label><input v-model="line.hsn" readonly style="width:65px;"></div>
        <div v-for="(col, ci) in store.customColumns" :key="col.id" class="lf">
          <label>{{ col.name }}</label>
          <input v-model="line.custom_values[ci]" :placeholder="'—'" style="width:100px;">
        </div>
        <div class="lf"><label>Qty</label><input v-model.number="line.quantity" type="number" min="0.01" style="width:75px;" @input="calcTotals"></div>
        <div class="lf"><label>Rate ₹</label><input v-model.number="line.rate" type="number" min="0" style="width:90px;" @input="calcTotals"></div>
        <button class="btn btn-sm btn-danger" @click="removeLine(idx)" style="padding:4px 7px;margin-bottom:1px;"><i class="ti ti-x"></i></button>
      </div>

      <button class="btn btn-sm" @click="addLine" style="margin-top:4px;"><i class="ti ti-plus"></i> Add item</button>

      <div class="inv-totals">
        <div class="tot-row"><span>Subtotal</span><span>{{ fmt(totals.subtotal) }}</span></div>
        <template v-if="isIntra">
          <div class="tot-row"><span>CGST ({{ gstRate / 2 }}%)</span><span>{{ fmt(totals.cgst) }}</span></div>
          <div class="tot-row"><span>SGST ({{ gstRate / 2 }}%)</span><span>{{ fmt(totals.sgst) }}</span></div>
        </template>
        <template v-else>
          <div class="tot-row"><span>IGST ({{ gstRate }}%)</span><span>{{ fmt(totals.igst) }}</span></div>
        </template>
        <div class="tot-row grand"><span>Grand Total</span><span>{{ fmt(totals.grand) }}</span></div>
      </div>

      <div style="display:flex;gap:8px;margin-top:1rem;">
        <button class="btn btn-primary" @click="save" :disabled="saving">
          <i class="ti ti-device-floppy"></i> {{ saving ? 'Saving...' : 'Save & Preview' }}
        </button>
        <button class="btn" @click="reset"><i class="ti ti-refresh"></i> Reset</button>
      </div>
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAppStore } from '../store'
import { useRouter } from 'vue-router'

const store = useAppStore()
const router = useRouter()
const saving = ref(false)
const toast = ref('')
const invDate = ref(new Date().toISOString().split('T')[0])
const poNumber = ref('')
const selectedCustomerId = ref('')
const lines = ref([])
const invoiceNumber = ref('Loading...')
const totals = ref({ subtotal: 0, cgst: 0, sgst: 0, igst: 0, grand: 0 })
async function loadPreviewNumber() {
  try {
    const res = await axios.get('/invoices/next-number')
    invoiceNumber.value = res.data.number
  } catch (e) {
    invoiceNumber.value = ''
  }
}

onMounted(async () => {
  await loadPreviewNumber()
  addLine()
})

const gstRate = computed(() => parseInt(store.settings.gst_rate || 18))

const selectedCustomer = computed(() =>
  store.customers.find(c => c.id == selectedCustomerId.value) || null
)

const isIntra = computed(() => {
  if (!selectedCustomer.value) return true
  const myCode = (store.settings.gstin || '03').substring(0, 2)
  const custCode = selectedCustomer.value.gstin.substring(0, 2)
  return myCode === custCode
})

function addLine() {
  lines.value.push({
    item_id: '',
    item_name: '',
    hsn: '',
    quantity: 1,
    rate: '',
    unit: '',
    custom_values: store.customColumns.map(() => ''),
    searchText: '',
    showDropdown: false,
  })
}

function removeLine(idx) {
  lines.value.splice(idx, 1)
  calcTotals()
}

function onSearchInput(line) {
  line.showDropdown = true
  if (line.item_id && line.searchText !== itemLabel(getItemById(line.item_id))) {
    line.item_id = ''
  }
}

function onBlur(line) {
  setTimeout(() => { line.showDropdown = false }, 150)
}

function getItemById(id) {
  return store.items.find(i => i.id == id)
}

function itemLabel(item) {
  if (!item) return ''
  return item.code ? `${item.name} (${item.code})` : item.name
}

function filteredItems(line) {
  const q = (line.searchText || '').trim().toLowerCase()
  if (!q) return store.items.slice(0, 8)
  return store.items.filter(it => {
    if (it.name?.toLowerCase().includes(q)) return true
    if (it.code?.toLowerCase().includes(q)) return true
    if (it.hsn?.toLowerCase().includes(q)) return true
    if (it.custom_values?.some(v => (v || '').toLowerCase().includes(q))) return true
    return false
  }).slice(0, 8)
}

function selectItem(line, item) {
  line.item_id = item.id
  line.item_name = item.name
  line.hsn = item.hsn || ''
  line.rate = item.price
  line.unit = item.unit || ''
  line.searchText = itemLabel(item)
  line.showDropdown = false
  store.customColumns.forEach((col, ci) => {
    line.custom_values[ci] = item.custom_values?.[ci] || ''
  })
  calcTotals()
}

function onCustomerChange() { calcTotals() }

function calcTotals() {
  const sub = lines.value.reduce((s, l) => s + (l.quantity || 0) * (l.rate || 0), 0)
  const gst = sub * gstRate.value / 100
  const intra = isIntra.value
  totals.value = {
    subtotal: sub,
    cgst: intra ? gst / 2 : 0,
    sgst: intra ? gst / 2 : 0,
    igst: intra ? 0 : gst,
    grand: sub + gst,
  }
}

function fmt(n) {
  return '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function showToast(msg) { toast.value = msg; setTimeout(() => toast.value = '', 2500) }

async function save() {
  const validLines = lines.value.filter(l => l.quantity > 0 && l.rate > 0)
  if (!validLines.length) return showToast('Add at least one item with qty and rate')
  if (!selectedCustomerId.value) return showToast('Select a customer')

  const payload = {
    customer_id: selectedCustomerId.value,
    date: invDate.value,
    invoice_number: invoiceNumber.value || null,
    po_number: poNumber.value || null,
    lines: validLines.map(l => ({
      item_id: l.item_id || null,
      item_name: l.item_name || (l.searchText || 'Item'),
      hsn: l.hsn,
      quantity: l.quantity,
      rate: l.rate,
      unit: l.unit || '',
      custom_values: l.custom_values,
    })),
  }

  saving.value = true
  try {
    const res = await axios.post('/invoices', payload)
    showToast('Invoice saved!')
    setTimeout(() => router.push('/invoices/' + res.data.id), 500)
  } catch (e) {
    showToast(e.response?.data?.message || e.response?.data?.detail || 'Error saving invoice')
  } finally {
    saving.value = false
  }
}

async function reset() {
  selectedCustomerId.value = ''
  invDate.value = new Date().toISOString().split('T')[0]
  poNumber.value = ''
  lines.value = []
  totals.value = { subtotal: 0, cgst: 0, sgst: 0, igst: 0, grand: 0 }
  await loadPreviewNumber()
  addLine()
}
</script>

<style scoped>
.item-search-wrap { position: relative; }
.item-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 2px;
  background: var(--bg-surface);
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  box-shadow: var(--shadow);
  z-index: 50;
  max-height: 260px;
  overflow-y: auto;
}
.item-option {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
}
.item-option:last-child { border-bottom: none; }
.item-option:hover { background: var(--bg-info); }
.item-option-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.item-option-meta {
  display: flex; gap: 10px; flex-wrap: wrap;
  font-size: 11px; color: var(--text-muted); margin-top: 2px;
}
</style>