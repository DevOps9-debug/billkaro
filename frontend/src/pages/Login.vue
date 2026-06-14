<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-brand">BillKaro</div>
      <div class="auth-sub">Sign in to your account</div>

      <div class="form-group" style="margin-bottom:12px;">
        <label>Email</label>
        <input v-model="email" type="email" placeholder="you@business.com" @keyup.enter="submit">
      </div>
      <div class="form-group" style="margin-bottom:16px;">
        <label>Password</label>
        <input v-model="password" type="password" placeholder="••••••••" @keyup.enter="submit">
      </div>

      <div v-if="error" class="auth-error">{{ error }}</div>

      <button class="btn btn-primary" style="width:100%;justify-content:center;" @click="submit" :disabled="loading">
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>

      <div class="auth-footer">
        Don't have an account? <RouterLink to="/register">Create one</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../store'

const router = useRouter()
const store = useAppStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value || !password.value) {
    error.value = 'Enter email and password'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await store.login(email.value, password.value)
    await store.loadAll()
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-page);
}
.auth-card {
  width: 100%;
  max-width: 360px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
}
.auth-brand { font-size: 22px; font-weight: 700; color: var(--text-primary); text-align: center; }
.auth-sub { font-size: 13px; color: var(--text-muted); text-align: center; margin-bottom: 1.5rem; margin-top: 4px; }
.auth-error {
  background: var(--danger-bg); color: var(--danger);
  border: 1px solid var(--danger-border);
  border-radius: 7px; padding: 8px 12px;
  font-size: 12px; margin-bottom: 12px;
}
.auth-footer { text-align: center; font-size: 13px; color: var(--text-secondary); margin-top: 1.25rem; }
.auth-footer a { color: var(--accent); text-decoration: none; font-weight: 500; }
</style>
