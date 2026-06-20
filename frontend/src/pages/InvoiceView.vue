<template>
  <div>
    <div class="sec-hdr">
      <h1 class="page-title" style="margin:0;">Invoice</h1>
      <div style="display:flex;gap:8px;">
        <button class="btn" @click="$router.back()"><i class="ti ti-arrow-left"></i> Back</button>
        <button class="btn btn-success" @click="downloadPdf" :disabled="downloading">
          <i class="ti ti-download"></i> {{ downloading ? 'Preparing...' : 'Download PDF' }}
        </button>
        <button class="btn btn-primary" @click="print"><i class="ti ti-printer"></i> Print</button>
        <button class="btn" @click="toggleCancel" :disabled="cancelling">
          <i :class="inv.status === 'cancelled' ? 'ti ti-rotate' : 'ti ti-ban'"></i> {{ inv.status === 'cancelled' ? 'Restore' : 'Cancel Invoice' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="inv" id="print-area">

      <div v-if="inv.status === 'cancelled'" style="background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;border-radius:8px;padding:8px 14px;font-weight:700;text-align:center;margin-bottom:14px;letter-spacing:0.05em;">
        CANCELLED
      </div>

      <!-- 3 copies -->
      <div v-for="(copyLabel, ci) in ['Original for Recipient', 'Duplicate for Transporter', 'Triplicate for Supplier']" :key="ci" class="invoice-copy card invoice-paper">

        <!-- Title -->
        <div style="display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #333;padding-bottom:12px;margin-bottom:16px;">
          <div style="font-size:18px;font-weight:700;">Tax Invoice</div>
          <div style="text-align:right;">
            <div style="font-size:13px;color:#555;">{{ inv.number }} &nbsp;|&nbsp; {{ inv.date }}{{ inv.po_number ? ' | PO: ' + inv.po_number : '' }}</div>
            <div style="font-size:12px;font-weight:700;color:#185FA5;margin-top:3px;">{{ copyLabel }}</div>
          </div>
        </div>

        <!-- From + Bill To -->
        <div style="display:grid;grid-template-columns:1fr 1px 1fr;gap:0;margin-bottom:16px;border:2px solid #333;border-radius:8px;overflow:hidden;">
          <div style="padding:10px 14px;font-size:13px;">
            <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;">From</div>
            <div style="font-weight:700;">{{ settings.biz_name || '—' }}</div>
            <div v-if="settings.about" style="color:#888;font-style:italic;">{{ settings.about }}</div>
            <div v-if="settings.address" style="color:#888;">{{ settings.address }}</div>
            <div style="color:#888;">GSTIN: {{ settings.gstin || '—' }}{{ settings.phone ? ' | ' + settings.phone : '' }}{{ settings.email ? ' | ' + settings.email : '' }}</div>
          </div>
          <div style="width:2px;background:#333;"></div>
          <div style="padding:10px 14px;font-size:13px;">
            <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;">Bill To</div>
            <div style="font-weight:700;">{{ inv.customer_name }}</div>
            <div v-if="inv.customer_vendor_code" style="color:#888;">Vendor Code: {{ inv.customer_vendor_code }}</div>
            <div style="color:#888;">GSTIN: {{ inv.customer_gstin }}</div>
            <div v-if="inv.customer_address" style="color:#888;">{{ inv.customer_address }}</div>
            <div style="color:#888;">{{ inv.customer_state }}</div>
          </div>
        </div>

        <!-- Lines table -->
        <div style="overflow-x:auto;margin-bottom:14px;">
          <table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #bbb;">
            <thead style="background:#fff;">
              <tr>
                <th style="padding:7px 9px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;width:30px;">#</th>
                <th style="padding:7px 9px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;">Item</th>
                <th style="padding:7px 9px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;">HSN</th>
                <th v-for="col in inv.col_snapshot" :key="col" style="padding:7px 9px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;">{{ col }}</th>
                <th style="padding:7px 9px;text-align:right;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;">Qty</th>
                <th style="padding:7px 9px;text-align:right;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;border-right:1px solid #bbb;">Rate</th>
                <th style="padding:7px 9px;text-align:right;font-size:10px;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2px solid #333;">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(line, li) in inv.lines" :key="line.id" style="border-bottom:1px solid #999;">
                <td style="padding:8px 9px;color:#888;border-right:1px solid #bbb;">{{ li + 1 }}</td>
                <td style="padding:8px 9px;border-right:1px solid #bbb;">{{ line.item_name }}</td>
                <td style="padding:8px 9px;color:#888;border-right:1px solid #bbb;">{{ line.hsn }}</td>
                <td v-for="(col, ci2) in inv.col_snapshot" :key="col" style="padding:8px 9px;color:#888;border-right:1px solid #bbb;">{{ line.custom_values?.[ci2] || '—' }}</td>
                <td style="padding:8px 9px;text-align:right;border-right:1px solid #bbb;">{{ line.quantity }} {{ line.unit }}</td>
                <td style="padding:8px 9px;text-align:right;border-right:1px solid #bbb;">{{ fmt(line.rate) }}</td>
                <td style="padding:8px 9px;text-align:right;font-weight:600;">{{ fmt(line.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div style="font-size:12px;color:#555;margin-bottom:8px;">
          <strong>Amount in Words:</strong> {{ amountInWords(inv.grand_total) }}
        </div>

        <!-- Totals -->
        <div style="display:flex;justify-content:flex-end;margin-bottom:16px;">
          <div style="min-width:250px;font-size:13px;border:1px solid #bbb;border-radius:6px;padding:8px 12px;">
            <div style="display:flex;justify-content:space-between;padding:3px 0;color:#888;border-bottom:1px solid #ddd;">Subtotal<span>{{ fmt(inv.subtotal) }}</span></div>
            <template v-if="inv.is_intra_state">
              <div style="display:flex;justify-content:space-between;padding:3px 0;color:#888;border-bottom:1px solid #ddd;">CGST ({{ inv.gst_rate / 2 }}%)<span>{{ fmt(inv.cgst) }}</span></div>
              <div style="display:flex;justify-content:space-between;padding:3px 0;color:#888;border-bottom:1px solid #ddd;">SGST ({{ inv.gst_rate / 2 }}%)<span>{{ fmt(inv.sgst) }}</span></div>
            </template>
            <template v-else>
              <div style="display:flex;justify-content:space-between;padding:3px 0;color:#888;border-bottom:1px solid #ddd;">IGST ({{ inv.gst_rate }}%)<span>{{ fmt(inv.igst) }}</span></div>
            </template>
            <div style="display:flex;justify-content:space-between;padding:9px 0 3px;font-size:16px;font-weight:700;border-top:2px solid #333;margin-top:6px;">
              Grand Total<span style="color:#185FA5;">{{ fmt(inv.grand_total) }}</span>
            </div>
          </div>
        </div>

        <!-- Tax breakdown -->
        <div v-if="inv.tax_breakdown && inv.tax_breakdown.length" style="margin-bottom:16px;overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;font-size:12px;border:1px solid #bbb;">
            <thead>
              <tr style="background:#fff;">
                <th style="padding:6px 9px;text-align:left;border-bottom:2px solid #333;border-right:1px solid #bbb;">HSN/SAC</th>
                <th style="padding:6px 9px;text-align:right;border-bottom:2px solid #333;border-right:1px solid #bbb;">Tax Rate</th>
                <th style="padding:6px 9px;text-align:right;border-bottom:2px solid #333;border-right:1px solid #bbb;">Taxable Amt</th>
                <th style="padding:6px 9px;text-align:right;border-bottom:2px solid #333;border-right:1px solid #bbb;">CGST Amt</th>
                <th style="padding:6px 9px;text-align:right;border-bottom:2px solid #333;border-right:1px solid #bbb;">SGST Amt</th>
                <th style="padding:6px 9px;text-align:right;border-bottom:2px solid #333;">Total Tax</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in inv.tax_breakdown" :key="row.hsn" style="border-bottom:1px solid #999;">
                <td style="padding:6px 9px;border-right:1px solid #bbb;">{{ row.hsn }}</td>
                <td style="padding:6px 9px;text-align:right;border-right:1px solid #bbb;">{{ row.rate }}%</td>
                <td style="padding:6px 9px;text-align:right;border-right:1px solid #bbb;">{{ fmt(row.taxable) }}</td>
                <td style="padding:6px 9px;text-align:right;border-right:1px solid #bbb;">{{ fmt(row.cgst) }}</td>
                <td style="padding:6px 9px;text-align:right;border-right:1px solid #bbb;">{{ fmt(row.sgst) }}</td>
                <td style="padding:6px 9px;text-align:right;font-weight:600;">{{ fmt(row.cgst + row.sgst) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Bank details -->
        <div v-if="settings.bank_name" style="font-size:12px;color:#888;background:#fff;padding:9px 14px;border-radius:8px;border:1px solid #bbb;">
          Bank: {{ settings.bank_name }} &nbsp;|&nbsp; A/C: {{ settings.bank_account }} &nbsp;|&nbsp; IFSC: {{ settings.bank_ifsc }}
        </div>

        <div v-if="settings.terms_conditions" style="font-size:11px;color:#777;margin-top:10px;white-space:pre-line;">
          <strong>Terms & Conditions:</strong><br>
          {{ settings.terms_conditions }}
        </div>

        <!-- Signature -->
        <div style="display:flex;justify-content:flex-end;margin-top:50px;">
          <div style="text-align:center;width:220px;">
            <div style="font-weight:600;margin-bottom:35px;">for {{ settings.biz_name || '' }}</div>
            <div style="border-top:1px solid #333;padding-top:6px;font-size:12px;color:#555;">
              Authorized Signatory
            </div>
          </div>
        </div>

      </div><!-- end invoice-copy -->

    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useAppStore } from '../store'

const route = useRoute()
const store = useAppStore()
const inv = ref(null)
const loading = ref(true)
const downloading = ref(false)
const cancelling = ref(false)
const toast = ref('')

const settings = computed(() => store.settings)

onMounted(async () => {
  document.title = 'Invoice'
  try {
    const res = await axios.get('/invoices/' + route.params.id)
    inv.value = res.data
  } finally {
    loading.value = false
  }
})

const fmt = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function showToast(msg) { toast.value = msg; setTimeout(() => toast.value = '', 2500) }

async function downloadPdf() {
  downloading.value = true
  try {
    const res = await axios.get('/invoices/' + route.params.id + '/pdf', { responseType: 'blob' })
    const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `invoice-${inv.value?.number || route.params.id}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(blobUrl)
  } catch (e) {
    showToast('Error generating PDF')
  } finally {
    downloading.value = false
  }
}

function print() {
  window.print()
}

const ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
  "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
  "Seventeen", "Eighteen", "Nineteen"]
const TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

function twoDigits(n) {
  if (n < 20) return ONES[n]
  return TENS[Math.floor(n / 10)] + (n % 10 ? " " + ONES[n % 10] : "")
}

function threeDigits(n) {
  if (n >= 100) return ONES[Math.floor(n / 100)] + " Hundred" + (n % 100 ? " " + twoDigits(n % 100) : "")
  return twoDigits(n)
}

function amountInWords(amount) {
  let rupees = Math.floor(amount)
  const paise = Math.round((amount - rupees) * 100)
  let words
  if (rupees === 0) {
    words = "Zero"
  } else {
    const parts = []
    const crore = Math.floor(rupees / 10000000); rupees %= 10000000
    const lakh = Math.floor(rupees / 100000); rupees %= 100000
    const thousand = Math.floor(rupees / 1000); rupees %= 1000
    const hundred = rupees
    if (crore) parts.push(threeDigits(crore) + " Crore")
    if (lakh) parts.push(threeDigits(lakh) + " Lakh")
    if (thousand) parts.push(threeDigits(thousand) + " Thousand")
    if (hundred) parts.push(threeDigits(hundred))
    words = parts.join(" ")
  }
  let result = "Rupees " + words + " Only"
  if (paise) result = "Rupees " + words + " and " + twoDigits(paise) + " Paise Only"
  return result
}

async function toggleCancel() {
  const action = inv.value.status === 'cancelled' ? 'restore' : 'cancel'
  if (!confirm(`Are you sure you want to ${action} this invoice?`)) return
  cancelling.value = true
  try {
    const res = await axios.patch('/invoices/' + route.params.id + '/cancel')
    inv.value.status = res.data.status
  } finally {
    cancelling.value = false
  }
}
</script>

<style>
.invoice-paper { background: #fff !important; color: #111 !important; }
.invoice-copy { margin-bottom: 40px; }

@media print {
  .sidebar, .sec-hdr { display: none !important; }
  .main-content { padding: 0 !important; }
  .invoice-copy {
    page-break-after: always;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 20px !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .invoice-copy:last-child {
    page-break-after: avoid;
  }
}
</style>