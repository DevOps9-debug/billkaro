<template>
  <div>
    <div class="sec-hdr">
      <h1 class="page-title" style="margin:0;">All Invoices</h1>
    </div>

    <div class="card">
      <div style="display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap;">
        <div class="form-group">
          <label>From</label>
          <input v-model="dateFrom" type="date">
        </div>
        <div class="form-group">
          <label>To</label>
          <input v-model="dateTo" type="date">
        </div>
        <button class="btn btn-sm" @click="clearRange">Clear</button>
        <div style="margin-left:auto;display:flex;gap:8px;">
          <button class="btn btn-success" @click="exportPdf" :disabled="exportingPdf">
            <i class="ti ti-file-type-pdf"></i> {{ exportingPdf ? 'Preparing...' : 'Download PDF for CA' }}
          </button>
          <button class="btn btn-primary" @click="exportCsv" :disabled="exportingCsv">
            <i class="ti ti-download"></i> {{ exportingCsv ? 'Preparing...' : 'Export CSV' }}
          </button>
        </div>
      </div>
    </div>

    <div class="month-filters">
      <button :class="['month-btn', activeMonth === 'all' ? 'active' : '']" @click="setMonth('all')">All</button>
      <button
        v-for="m in months" :key="m.value"
        :class="['month-btn', activeMonth === m.value ? 'active' : '']"
        @click="setMonth(m.value)"
      >{{ m.label }}</button>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Invoice #</th><th>Date</th><th>Customer</th><th>State</th><th>Tax type</th><th>Subtotal</th><th>GST</th><th>Total</th><th></th></tr></thead>
          <tbody>
            <tr v-if="!filtered.length"><td colspan="9"><div class="empty">No invoices found</div></td></tr>
            <tr v-for="inv in filtered" :key="inv.id" class="row-link" @click="$router.push('/invoices/'+inv.id)">
              <td style="font-weight:600;">
                {{ inv.number }}
                <span v-if="inv.status === 'cancelled'" class="badge" style="background:var(--danger-bg);color:var(--danger);margin-left:6px;">CANCELLED</span>
              </td>
              <td>{{ inv.date }}</td>
              <td>{{ inv.customer_name }}</td>
              <td style="font-size:12px;color:var(--text-muted);">{{ inv.customer_state }}</td>
              <td><span :class="['badge', inv.is_intra_state ? 'badge-sgst' : 'badge-igst']">{{ inv.is_intra_state ? 'CGST+SGST' : 'IGST' }}</span></td>
              <td>{{ fmt(inv.subtotal) }}</td>
              <td style="color:var(--text-muted);">{{ fmt(inv.gst_total) }}</td>
              <td style="font-weight:600;">{{ fmt(inv.grand_total) }}</td>
              <td>
                <button class="btn btn-sm" @click.stop="toggleCancel(inv)" :title="inv.status === 'cancelled' ? 'Restore' : 'Cancel'">
                  <i :class="inv.status === 'cancelled' ? 'ti ti-rotate' : 'ti ti-ban'"></i>
                </button>
                <button class="btn btn-sm btn-danger" @click.stop="del(inv.id)"><i class="ti ti-trash"></i></button>
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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const invoices = ref([])
const activeMonth = ref('all')
const dateFrom = ref('')
const dateTo = ref('')
const exportingCsv = ref(false)
const exportingPdf = ref(false)
const toast = ref('')

function showToast(msg) { toast.value = msg; setTimeout(() => toast.value = '', 2500) }

async function loadInvoices() {
  const res = await axios.get('/invoices')
  invoices.value = res.data
}

onMounted(loadInvoices)

const months = computed(() => {
  const seen = new Set()
  invoices.value.forEach(inv => seen.add(inv.date.substring(0, 7)))
  return [...seen].sort().reverse().map(m => {
    const [yr, mo] = m.split('-')
    return { value: m, label: new Date(yr, mo - 1, 1).toLocaleString('default', { month: 'short', year: 'numeric' }) }
  })
})

function setMonth(m) {
  activeMonth.value = m
  if (m !== 'all') {
    dateFrom.value = ''
    dateTo.value = ''
  }
}

function clearRange() {
  dateFrom.value = ''
  dateTo.value = ''
}

watch([dateFrom, dateTo], ([from, to]) => {
  if (from || to) activeMonth.value = 'all'
})

const filtered = computed(() => {
  let result = invoices.value
  if (activeMonth.value !== 'all') {
    result = result.filter(i => i.date.startsWith(activeMonth.value))
  }
  if (dateFrom.value) result = result.filter(i => i.date >= dateFrom.value)
  if (dateTo.value) result = result.filter(i => i.date <= dateTo.value)
  return result
})

const fmt = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

async function del(id) {
  if (!confirm('Delete this invoice?')) return
  await axios.delete('/invoices/' + id)
  invoices.value = invoices.value.filter(i => i.id !== id)
}

async function toggleCancel(inv) {
  const action = inv.status === 'cancelled' ? 'restore' : 'cancel'
  if (!confirm(`Are you sure you want to ${action} invoice ${inv.number}?`)) return
  const res = await axios.patch('/invoices/' + inv.id + '/cancel')
  inv.status = res.data.status
}

function buildParams() {
  const params = {}
  if (activeMonth.value !== 'all') params.month = activeMonth.value
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  return params
}

async function downloadBlob(url, params, filename) {
  const res = await axios.get(url, { params, responseType: 'blob' })
  const blobUrl = window.URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

async function exportCsv() {
  exportingCsv.value = true
  try {
    await downloadBlob('/invoices/export/csv', buildParams(), `gst-invoices-${Date.now()}.csv`)
  } catch (e) {
    showToast('Error exporting CSV')
  } finally {
    exportingCsv.value = false
  }
}

async function exportPdf() {
  if (!filtered.value.length) {
    showToast('No invoices in this selection')
    return
  }
  exportingPdf.value = true
  try {
    await downloadBlob('/invoices/export/pdf', buildParams(), `gst-invoices-${Date.now()}.pdf`)
  } catch (e) {
    showToast(e.response?.data?.detail || 'Error generating PDF')
  } finally {
    exportingPdf.value = false
  }
}
</script>
