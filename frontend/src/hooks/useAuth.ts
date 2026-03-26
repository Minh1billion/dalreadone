import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export function useLogin() {
  const setToken = useAuthStore((s) => s.setToken)
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function login(username: string, password: string) {
    setError('')
    setLoading(true)
    try {
      const { data } = await authApi.login(username, password)
      setToken(data.access_token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return { login, loading, error }
}

export function useRegister() {
  const setToken = useAuthStore((s) => s.setToken)
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function register(username: string, password: string) {
    setError('')
    setLoading(true)
    try {
      const { data } = await authApi.register(username, password)
      setToken(data.access_token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return { register, loading, error }
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear)
  const navigate = useNavigate()

  async function logout() {
    await authApi.logout()
    clear()
    navigate('/login')
  }

  return { logout }
}