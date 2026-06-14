<template>
  <!-- Auth pages: no sidebar -->
  <RouterView v-if="isAuthPage" />

  <!-- App shell -->
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="sb-brand">
        <div>
          <span class="sb-logo">BillKaro</span>
          <span class="sb-sub">{{ store.user?.email || 'GST Billing' }}</span>
        </div>
        <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
          <i :class="isDark ? 'ti ti-sun' : 'ti ti-moon'"></i>
        </button>
      </div>
      <nav>
        <RouterLink to="/"            class="nav-item"><i class="ti ti-layout-dashboard"></i> Dashboard</RouterLink>
        <RouterLink to="/invoice/new" class="nav-item"><i class="ti ti-file-invoice"></i> New Invoice</RouterLink>
        <RouterLink to="/invoices"    class="nav-item"><i class="ti ti-list"></i> All Invoices</RouterLink>
        <RouterLink to="/customers"   class="nav-item"><i class="ti ti-users"></i> Customers</RouterLink>
        <RouterLink to="/items"       class="nav-item"><i class="ti ti-box"></i> Items</RouterLink>
        <RouterLink to="/settings"    class="nav-item"><i class="ti ti-settings"></i> Settings</RouterLink>
      </nav>
      <div class="sb-footer">
        <button class="nav-item logout-btn" @click="logout"><i class="ti ti-logout"></i> Log out</button>
      </div>
    </aside>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from './store'

const store = useAppStore()
const route = useRoute()
const router = useRouter()
const isDark = ref(false)

const isAuthPage = computed(() => route.meta.guest === true)

function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  localStorage.setItem('billkaro-theme', dark ? 'dark' : 'light')
  isDark.value = dark
}

function toggleTheme() {
  applyTheme(!isDark.value)
}

function logout() {
  store.logout()
  router.push('/login')
}

onMounted(() => {
  if (store.isAuthenticated) {
    store.loadAll()
  }

  const saved = localStorage.getItem('billkaro-theme')
  if (saved) {
    applyTheme(saved === 'dark')
  } else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme(prefersDark)
  }
})
</script>

<style>
.sb-footer {
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding: 0.5rem;
}
.logout-btn {
  width: 100%;
  border: none;
  background: none;
  cursor: pointer;
  font-family: inherit;
  border-radius: 7px;
}
.logout-btn:hover { background: var(--danger-bg); color: var(--danger); }
.sidebar { display: flex; flex-direction: column; }
nav { flex: 1; }
</style>
