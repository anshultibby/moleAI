'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'
import PasswordGate from '@/components/PasswordGate'

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const handleAuthenticated = () => {
    setIsAuthenticated(true)
  }

  return (
    <main>
      {isAuthenticated ? (
        <ChatInterface />
      ) : (
        <PasswordGate onAuthenticated={handleAuthenticated} />
      )}
    </main>
  )
} 