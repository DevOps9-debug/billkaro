import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from './store'

const routes = [
  { path: '/login',     component: () => import('./pages/Login.vue'),    meta: { title: 'Sign In', guest: true } },
  { path: '/register',  component: () => import('./pages/Register.vue'), meta: { title: 'Create Account', guest: true } },

  { path: '/',           component: () => import('./pages/Dashboard.vue'),  meta: { title: 'Dashboard' } },
  { path: '/invoice/new',component: () => import('./pages/InvoiceNew.vue'), meta: { title: 'New Invoice' } },
  { path: '/invoices',   component: () => import('./pages/Invoices.vue'),   meta: { title: 'All Invoices' } },
  { path: '/invoices/:id/edit', component: () => import('./pages/InvoiceNew.vue'), meta: { title: 'Edit Invoice' } },
  { path: '/invoices/:id',component: () => import('./pages/InvoiceView.vue'),meta: { title: 'Invoice' } },
  { path: '/customers',  component: () => import('./pages/Customers.vue'),  meta: { title: 'Customers' } },
  { path: '/items',      component: () => import('./pages/Items.vue'),       meta: { title: 'Items' } },
  { path: '/settings',   component: () => import('./pages/Settings.vue'),   meta: { title: 'Settings' } },
  
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const store = useAppStore()
  const isGuestPage = to.meta.guest === true

  if (!store.isAuthenticated && !isGuestPage) {
    return '/login'
  }
  if (store.isAuthenticated && isGuestPage) {
    return '/'
  }
  return true
})

router.afterEach((to) => {
  document.title = (to.meta.title ? to.meta.title + ' — ' : '') + 'BillKaro'
})

export default router
