import { defineStore } from 'pinia'
import axios from 'axios'

export const useAppStore = defineStore('app', {
  state: () => ({
    token: localStorage.getItem('billkaro_token') || null,
    user: JSON.parse(localStorage.getItem('billkaro_user') || 'null'),
    settings: {},
    customers: [],
    items: [],
    customColumns: [],
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('billkaro_token', token)
      localStorage.setItem('billkaro_user', JSON.stringify(user))
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    },

    clearAuth() {
      this.token = null
      this.user = null
      localStorage.removeItem('billkaro_token')
      localStorage.removeItem('billkaro_user')
      delete axios.defaults.headers.common['Authorization']
      // Clear cached data so it doesn't leak between accounts
      this.settings = {}
      this.customers = []
      this.items = []
      this.customColumns = []
    },

    async register(email, password) {
      const { data } = await axios.post('/auth/register', { email, password })
      this.setAuth(data.access_token, data.user)
    },

    async login(email, password) {
      const { data } = await axios.post('/auth/login', { email, password })
      this.setAuth(data.access_token, data.user)
    },

    logout() {
      this.clearAuth()
    },

    async loadSettings() {
      const { data } = await axios.get('/settings')
      this.settings = data
    },
    async saveSettings(payload) {
      await axios.put('/settings', payload)
      await this.loadSettings()
    },
    async loadCustomers() {
      const { data } = await axios.get('/customers')
      this.customers = data
    },
    async loadItems() {
      const { data } = await axios.get('/items')
      this.items = data
    },
    async loadCustomColumns() {
      const { data } = await axios.get('/custom-columns')
      this.customColumns = data
    },
    async loadAll() {
      if (!this.token) return
      await Promise.all([
        this.loadSettings(),
        this.loadCustomers(),
        this.loadItems(),
        this.loadCustomColumns(),
      ])
    },
  },
})
