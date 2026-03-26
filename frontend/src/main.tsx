import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api/axios.ts'
import './index.css'
import App from './App.tsx'
import { useAuthStore } from './store/authStore'

// 1. Read access_token from URL after OAuth redirect
const params = new URLSearchParams(window.location.search)
const oauthToken = params.get('access_token')
if (oauthToken) {
  useAuthStore.getState().setToken(oauthToken)
  window.history.replaceState({}, '', '/')
}

// 2. Silent refresh
if (!oauthToken) {
  try {
    const { data } = await api.post('/auth/refresh')
    useAuthStore.getState().setToken(data.access_token)
  } catch {
    // pass
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)