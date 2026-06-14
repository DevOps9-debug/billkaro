<template>
  <div>
    <div class="sec-hdr">
      <h1 class="page-title" style="margin:0;">Dashboard</h1>
    </div>

    <div class="card" style="margin-bottom:1rem;">
      <div style="display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap;">
        <div class="form-group">
          <label>From</label>
          <input v-model="dateFrom" type="date" @change="load">
        </div>
        <div class="form-group">
          <label>To</label>
          <input v-model="dateTo" type="date" @change="load">
        </div>
        <button class="btn btn-sm" @click="setThisMonth">This month</button>
        <button class="btn btn-sm" @click="setLastMonth">Last month</button>
        <button class="btn btn-sm" @click="setAllTime">All time</button>
        <span style="font-size:13px;color:var(--text-muted);margin-left:auto;">{{ data?.period_label }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <template v-else>
      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Bills in period</div>
          <div class="metric-value">{{ data?.summary?.count ?? 0 }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Taxable amount</div>
          <div class="metric-value" style="font-size:16px;">{{ fmt(data?.summary?.subtotal) }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">GST collected</div>
          <div class="metric-value" style="font-size:16px;">{{ fmt(data?.summary?.gst_total) }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Total billed</div>
          <div class="metric-value" style="font-size:16px;color:var(--accent);">{{ fmt(data?.summary?.grand_total) }}</div>
        </div>
        <div class="metric">
          <div class="metric-label">IGST bills</div>
          <div class="metric-value">{{ data?.summary?.igst_count ?? 0 }}</div>
          <div class="metric-sub">inter-state</div>
        </div>
        <div class="metric">
          <div class="metric-label">CGST+SGST bills</div>
          <div class="metric-value">{{ data?.summary?.cgst_count ?? 0 }}</div>
          <div class="metric-sub">intra-state</div>
        </div>
      </div>

      <div class="card">
        <div class="sec-hdr">
          <span style="font-size:14px;font-weight:600;">Recent invoices</span>
          <RouterLink to="/invoices" class="btn btn-sm">View all</RouterLink>
        </div>
        <div v-if="!data?.recent?.length" class="empty">
          No invoices yet. <RouterLink to="/invoice/new">Create your first one →</RouterLink>
        </div>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th>Invoice #</th><th>Date</th><th>Customer</th><th>Tax</th><th>Total</th></tr></thead>
            <tbody>
              <tr v-for="inv in data.recent" :key="inv.id" class="row-link" @click="$router.push('/invoices/'+inv.id)">
                <td style="font-weight:600;">{{ inv.number }}</td>
                <td>{{ inv.date }}</td>
                <td>{{ inv.cust_name }}</td>
                <td><span :class="['badge', inv.tax_type === 'IGST' ? 'badge-igst' : 'badge-sgst']">{{ inv.tax_type }}</span></td>
                <td style="font-weight:600;">{{ fmt(inv.grand_total) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const data = ref(null)
const loading = ref(true)
const dateFrom = ref('')
const dateTo = ref('')

function pad(n) { return String(n).padStart(2, '0') }
function toIso(d) { return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}` }

function setThisMonth() {
  const now = new Date()
  dateFrom.value = toIso(new Date(now.getFullYear(), now.getMonth(), 1))
  dateTo.value = toIso(new Date(now.getFullYear(), now.getMonth() + 1, 0))
  load()
}

function setLastMonth() {
  const now = new Date()
  dateFrom.value = toIso(new Date(now.getFullYear(), now.getMonth() - 1, 1))
  dateTo.value = toIso(new Date(now.getFullYear(), now.getMonth(), 0))
  load()
}

function setAllTime() {
  dateFrom.value = '2000-01-01'
  dateTo.value = toIso(new Date())
  load()
}

const fmt = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const res = await axios.get('/dashboard', { params })
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  setThisMonth()
})
</script>
