<template>
  <div>
    <h1 class="page-title">Customers</h1>

    <div class="card">
      <div style="font-size:14px;font-weight:600;margin-bottom:12px;">{{ editingId ? 'Edit customer' : 'Add customer' }}</div>
      <div class="form-row cols-2">
        <div class="form-group"><label>Business name</label><input v-model="form.name" placeholder="ABC Traders"></div>
        <div class="form-group"><label>GSTIN</label><input v-model="form.gstin" @input="form.gstin = form.gstin.toUpperCase(); detectState()" placeholder="27XXXXX1234Z5" maxlength="15"></div>
      </div>
      <div class="form-row cols-2">
        <div class="form-group"><label>State (auto)</label><input :value="detectedState" readonly></div>
        <div class="form-group"><label>Address</label><input v-model="form.address" placeholder="City, State"></div>
      </div>
      <div class="form-row cols-3" style="margin-bottom:12px;">
        <div class="form-group"><label>Phone (optional)</label><input v-model="form.phone" placeholder="9876543210"></div>
        <div class="form-group"><label>Email (optional)</label><input v-model="form.email" placeholder="buyer@example.com"></div>
        <div class="form-group"><label>Vendor Code (optional)</label><input v-model="form.vendor_code" placeholder="Their code for us"></div>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-primary" @click="save" :disabled="saving">
          <i :class="editingId ? 'ti ti-device-floppy' : 'ti ti-plus'"></i> {{ saving ? 'Saving...' : (editingId ? 'Update customer' : 'Add customer') }}
        </button>
        <button v-if="editingId" class="btn" @click="cancelEdit"><i class="ti ti-x"></i> Cancel</button>
      </div>
    </div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>GSTIN</th><th>State</th><th>Address</th><th>Vendor Code</th><th></th></tr></thead>
          <tbody>
            <tr v-if="!store.customers.length"><td colspan="6"><div class="empty">No customers yet</div></td></tr>
            <tr v-for="c in store.customers" :key="c.id">
              <td style="font-weight:600;">{{ c.name }}</td>
              <td style="font-family:monospace;font-size:12px;">{{ c.gstin }}</td>
              <td>{{ c.state }}</td>
              <td style="color:var(--text-muted);">{{ c.address || '—' }}</td>
              <td style="color:var(--text-muted);">{{ c.vendor_code || '—' }}</td>
              <td>
                <button class="btn btn-sm" @click="editCustomer(c)"><i class="ti ti-pencil"></i></button>
                <button class="btn btn-sm btn-danger" @click="del(c.id)"><i class="ti ti-trash"></i></button>
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
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAppStore } from '../store'

const store = useAppStore()
const saving = ref(false)
const toast = ref('')
const form = ref({ name: '', gstin: '', address: '', phone: '', email: '', vendor_code: '' })
const editingId = ref(null)

const STATE_CODES = {'01':'Jammu & Kashmir','02':'Himachal Pradesh','03':'Punjab','04':'Chandigarh','05':'Uttarakhand','06':'Haryana','07':'Delhi','08':'Rajasthan','09':'Uttar Pradesh','10':'Bihar','18':'Assam','19':'West Bengal','20':'Jharkhand','21':'Odisha','22':'Chhattisgarh','23':'Madhya Pradesh','24':'Gujarat','27':'Maharashtra','29':'Karnataka','30':'Goa','32':'Kerala','33':'Tamil Nadu','36':'Telangana','37':'Andhra Pradesh'}

const detectedState = computed(() => {
  const g = form.value.gstin
  return (g && g.length >= 2) ? (STATE_CODES[g.substring(0, 2)] || '') : ''
})

function detectState() {}

function showToast(msg) {
  toast.value = msg
  setTimeout(() => toast.value = '', 2500)
}

async function save() {
  if (!form.value.name || !form.value.gstin) return showToast('Name and GSTIN required')
  if (form.value.gstin.length !== 15) return showToast('GSTIN must be 15 characters')
  saving.value = true
  try {
    if (editingId.value) {
      await axios.put('/customers/' + editingId.value, form.value)
      showToast('Customer updated!')
      editingId.value = null
    } else {
      await axios.post('/customers', form.value)
      showToast('Customer added!')
    }
    await store.loadCustomers()
    form.value = { name: '', gstin: '', address: '', phone: '', email: '', vendor_code: ''}
  } catch (e) {
    showToast(e.response?.data?.message || e.response?.data?.detail || 'Error saving')
  } finally {
    saving.value = false
  }
}

function editCustomer(c) {
  editingId.value = c.id
  form.value = {
    name: c.name,
    gstin: c.gstin,
    address: c.address || '',
    phone: c.phone || '',
    email: c.email || '',
    vendor_code: c.vendor_code || '',
  }


  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  form.value = { name: '', gstin: '', address: '', phone: '', email: '', vendor_code: ''}
}

async function del(id) {
  if (!confirm('Delete this customer?')) return
  await axios.delete('/customers/' + id)
  await store.loadCustomers()
  showToast('Deleted')
}
</script>