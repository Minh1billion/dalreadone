import { useState } from 'react'
import { useLogin, useRegister } from '../hooks/useAuth'

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const { login, loading: loginLoading, error: loginError } = useLogin()
  const { register, loading: registerLoading, error: registerError } = useRegister()

  const loading = isLogin ? loginLoading : registerLoading
  const error = isLogin ? loginError : registerError

  function switchForm() {
    setIsLogin(!isLogin)
    setUsername('')
    setPassword('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (isLogin) await login(username, password)
    else await register(username, password)
  }

  function handleOAuth(provider: 'google' | 'github') {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/${provider}`
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center mb-3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <polyline points="10 17 15 12 10 7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">DALreaDone</h1>
          <p className="text-sm text-gray-500 mt-1">Data analytics, simplified.</p>
        </div>

        {/* Title */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            {isLogin ? 'Welcome back' : 'Create an account'}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {isLogin ? 'Sign in to your account to continue.' : 'Start analyzing your data today.'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-shadow"
            />
          </div>

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50"
          >
            {loading ? 'Please wait...' : isLogin ? 'Sign in' : 'Create account'}
          </button>
        </form>

        {/* Switch form */}
        <p className="text-center text-sm text-gray-500 mt-4">
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={switchForm}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            {isLogin ? 'Register' : 'Sign in'}
          </button>
        </p>

        {/* Divider */}
        <div className="flex items-center gap-3 my-5">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">Or continue with</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* OAuth */}
        <div className="space-y-2">
          <button
            onClick={() => handleOAuth('google')}
            className="w-full flex items-center justify-center gap-3 py-2.5 border border-gray-200 rounded-md text-sm font-medium text-gray-700 hover:bg-amber-50 hover:border-primary-200 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>
          <button
            onClick={() => handleOAuth('github')}
            className="w-full flex items-center justify-center gap-3 py-2.5 border border-gray-200 rounded-md text-sm font-medium text-gray-700 hover:bg-amber-50 hover:border-primary-200 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
            </svg>
            Continue with GitHub
          </button>
        </div>

      </div>
    </div>
  )
}