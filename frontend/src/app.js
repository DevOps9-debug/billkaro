import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import './css/app.css'

axios.defaults.baseURL = '/api/v1'

// Restore auth header from storage on full page load
const savedToken = localStorage.getItem('billkaro_token')
if (savedToken) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
}

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// Global 401 handler -> force logout & redirect to login
axios.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('billkaro_token')
      localStorage.removeItem('billkaro_user')
      delete axios.defaults.headers.common['Authorization']
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    }
    return Promise.reject(err)
  }
)

app.mount('#app')
