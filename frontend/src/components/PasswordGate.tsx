'use client'

import { useState, useEffect } from 'react'

interface PasswordGateProps {
  onAuthenticated: () => void
}

export default function PasswordGate({ onAuthenticated }: PasswordGateProps) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Check if user is already authenticated
  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('shopmole_authenticated')
    if (isAuthenticated === 'true') {
      onAuthenticated()
    }
  }, [onAuthenticated])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Simple password check
    if (password === 'shopmole') {
      sessionStorage.setItem('shopmole_authenticated', 'true')
      onAuthenticated()
    } else {
      setError('Incorrect password. Please try again.')
      setPassword('')
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-xl border border-slate-200/60 dark:border-slate-600/60 p-8">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">
              Shopmole AI
            </h1>
            <p className="text-slate-600 dark:text-slate-300 text-sm">
              Enter password to access the shopping assistant
            </p>
          </div>

          {/* Password Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:text-white placeholder-slate-500 dark:placeholder-slate-400"
                placeholder="Enter password"
                required
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !password.trim()}
              className="w-full px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white rounded-lg font-medium shadow-lg disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 disabled:transform-none flex items-center justify-center"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                'Access Shopmole AI'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-600">
            <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
              Protected access to prevent unauthorized usage
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-6 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            AI-powered shopping assistant • Find the best deals
          </p>
        </div>
      </div>
    </div>
  )
} 