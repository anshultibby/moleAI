'use client'

import { useState, useEffect } from 'react'
import ChatPanel from './ChatPanel'
import WelcomePage from './WelcomePage'
import ToolExecutionSidePanel from './ToolExecutionSidePanel'
import { useChat } from '../hooks/useChat'
import { useProducts } from '../hooks/useProducts'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const [isMounted, setIsMounted] = useState(false)
  
  // Use custom hooks for state management
  const chat = useChat()
  const products = useProducts()

  // Ensure component is mounted on client side to prevent hydration issues
  useEffect(() => {
    setIsMounted(true)
  }, [])

  const handleLogout = () => {
    sessionStorage.removeItem('shopmole_authenticated')
    window.location.reload()
  }

  const handleStartConversation = async (query: string) => {
    // Clear filters when starting new conversation
    products.clearFilters()
    
    // Send message and handle product updates
    await chat.sendMessage(query, products.addProduct, products.removeProductById)
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return
    
    // Clear filters when sending new message
    products.clearFilters()
    
    // Send message and handle product updates
    await chat.sendMessage(input, products.addProduct, products.removeProductById)
    setInput('')
  }

  const handleNewSearch = () => {
    // Reset everything for a new search
    chat.resetConversation()
    products.clearAllProducts()
    setInput('')
  }

  // Don't render until mounted to prevent hydration issues
  if (!isMounted) {
    return (
      <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-slate-600 dark:text-slate-400">Loading...</div>
      </div>
    )
  }

  // Show welcome page if no conversation has started
  if (!chat.hasStartedConversation) {
    return <WelcomePage onStartConversation={handleStartConversation} />
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex flex-col">
      
      {/* Compact top toggle bar */}
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 shadow-sm px-3 py-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          
          {/* Minimal branding */}
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded flex items-center justify-center">
              <span className="text-white text-xs font-bold">M</span>
            </div>
            <span className="text-sm font-semibold text-slate-800 dark:text-white">MoleAI</span>
          </div>

          {/* Compact toggles */}
          <div className="flex items-center space-x-2">
            
            {/* New Search Button */}
            <button
              onClick={handleNewSearch}
              className="px-2 py-1 text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 rounded transition-colors flex items-center space-x-1"
              title="New Search"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="hidden sm:inline">New</span>
            </button>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="px-2 py-1 text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 rounded transition-colors flex items-center space-x-1"
              title="Logout"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">Logout</span>
            </button>
            
            {/* Chat indicator */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Full Chat View
              </span>
              {products.uniqueProducts.length > 0 && (
                <span className="bg-indigo-500 text-white text-xs px-2 py-1 rounded-full">
                  {products.uniqueProducts.length} products
                </span>
              )}
            </div>
            
          </div>
        </div>
      </div>

      {/* Main content area - Chat with side panel */}
      <div className="flex-1 flex min-h-0 h-full overflow-hidden">
        <div className="flex-1 h-full">
          <ChatPanel
            messages={chat.messages}
            input={input}
            isLoading={chat.isLoading}
            searchLinksData={products.searchLinksData}
            ephemeralHistory={chat.ephemeralHistory}
            currentTurnId={chat.currentTurnId}
            activeToolExecutions={chat.activeToolExecutions}
            onInputChange={setInput}
            onSendMessage={handleSendMessage}
            onRemoveProduct={products.removeProduct}
          />
        </div>
        
        {/* AI Shopping Activity Panel */}
        {Object.keys(chat.currentToolExecutions).length > 0 && (
          <ToolExecutionSidePanel
            toolExecutions={chat.currentToolExecutions}
            isActive={chat.isLoading}
          />
        )}
      </div>
    </div>
  )
} 