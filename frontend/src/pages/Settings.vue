<template>
  <div>
    <h1 class="page-title">Business Settings</h1>
    <div class="card">
      <div class="form-row cols-2">
        <div class="form-group"><label>Business name</label><input v-model="form.biz_name" placeholder="Your Manufacturing Co."></div>
        <div class="form-group"><label>Your GSTIN</label><input v-model="form.gstin" @input="form.gstin = form.gstin.toUpperCase()" placeholder="03XXXXX1234Z5" maxlength="15"></div>
      </div>
      <div class="form-row cols-1">
        <div class="form-group"><label>Address</label><input v-model="form.address" placeholder="Full address, Punjab"></div>
      </div>
      <div class="form-row cols-2">
        <div class="form-group"><label>Phone</label><input v-model="form.phone" placeholder="9876543210"></div>
        <div class="form-group"><label>Email</label><input v-model="form.email" placeholder="you@business.com"></div>
      </div>
      <div class="form-row cols-1">
        <div class="form-group">
          <label>About your business (optional)</label>
          <textarea v-model="form.about" rows="3" placeholder="Brief description of what your business does — e.g. manufacturing of steel components for industrial use"></textarea>
        </div>
      </div>
      <div class="form-row cols-1">
        <div class="form-group">
          <label>Terms & Conditions (shown on every invoice)</label>
          <textarea v-model="form.terms_conditions" rows="4" placeholder="One condition per line, e.g.&#10;1. Interest @ 24% P.A. will be charged on delayed payments.&#10;2. All disputes are subject to Mohali Jurisdiction only."></textarea>
        </div>
      </div>
      <div class="form-row cols-3">
        <div class="form-group"><label>Bank name</label><input v-model="form.bank_name" placeholder="Punjab National Bank"></div>
        <div class="form-group"><label>Account number</label><input v-model="form.bank_account"></div>
        <div class="form-group"><label>IFSC code</label><input v-model="form.bank_ifsc"></div>
      </div>
      <div class="form-row cols-2">
        <div class="form-group">
          <label>Default GST rate</label>
          <select v-model="form.gst_rate">
            <option value="5">5%</option>
            <option value="12">12%</option>
            <option value="18">18%</option>
            <option value="28">28%</option>
          </select>
        </div>
        <div class="form-group"><label>Invoice prefix</label><input v-model="form.invoice_prefix" placeholder="INV"></div>
      </div>
      <button class="btn btn-primary" @click="save" :disabled="saving">
        <i class="ti ti-device-floppy"></i> {{ saving ? 'Saving...' : 'Save settings' }}
      </button>
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../store'

const store = useAppStore()
const saving = ref(false)
const toast = ref('')
const form = ref({
  biz_name: '', gstin: '', address: '', phone: '', email: '', about: '',
  bank_name: '', bank_account: '', bank_ifsc: '', gst_rate: '18', invoice_prefix: 'INV', terms_conditions: '',
})

onMounted(() => {
  Object.assign(form.value, store.settings)
})

function showToast(msg) { toast.value = msg; setTimeout(() => toast.value = '', 2500) }

async function save() {
  saving.value = true
  try {
    await store.saveSettings(form.value)
    showToast('Settings saved!')
  } catch (e) {
    showToast('Error saving settings')
  } finally {
    saving.value = false
  }
}
</script>
