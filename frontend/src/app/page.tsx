'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/ChatInterface'
import PasswordGate from '@/components/PasswordGate'

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  // Handle mounting and check authentication status
  useEffect(() => {
    // Check if user was previously authenticated (only in browser)
    const wasAuthenticated = typeof window !== 'undefined' 
      ? sessionStorage.getItem('shopmole_authenticated') === 'true'
      : false
    setIsAuthenticated(wasAuthenticated)
    setIsMounted(true)
  }, [])

  const handleAuthenticated = () => {
    setIsAuthenticated(true)
  }

  // Don't render until mounted to prevent hydration issues
  if (!isMounted) {
    return (
      <main className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-slate-600 dark:text-slate-400">Loading...</div>
      </main>
    )
  }

  return (
    <main>
      {/* Temporarily disabled for site verification */}
      {/* {isAuthenticated ? (
        <ChatInterface />
      ) : (
        <PasswordGate onAuthenticated={handleAuthenticated} />
      )} */}
      <ChatInterface />
    </main>
  )
} 