'use client'

import { useState, useEffect } from 'react'
import ChatPanel from './ChatPanel'
import ProductPanel from './ProductPanel'
import SearchLinksPanel from './SearchLinksPanel'
import ReasoningDisplay from './ReasoningDisplay'
import { useChat } from '../hooks/useChat'
import { useProducts } from '../hooks/useProducts'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const [isMounted, setIsMounted] = useState(false)
  
  // New state for mobile-friendly toggle system
  const [activeView, setActiveView] = useState<'products' | 'chat'>('products')
  const [isChatExpanded, setIsChatExpanded] = useState(false)
  
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

  const handleSendMessage = async () => {
    if (!input.trim()) return
    
    // Clear filters when sending new message
    products.clearFilters()
    
    // Send message and handle product updates
    await chat.sendMessage(input, products.addProduct)
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
            
            {/* Desktop chat toggle */}
            <div className="hidden lg:flex items-center space-x-1">
              <button
                onClick={() => setIsChatExpanded(!isChatExpanded)}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                  isChatExpanded 
                    ? 'bg-indigo-500 text-white' 
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                }`}
              >
                Chat
              </button>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {products.uniqueProducts.length}
              </span>
            </div>

            {/* Mobile toggle */}
            <div className="flex lg:hidden">
              <div className="flex bg-slate-100 dark:bg-slate-700 rounded p-0.5">
                <button
                  onClick={() => setActiveView('chat')}
                  className={`px-2 py-1 rounded text-xs font-medium transition-all flex items-center space-x-1 ${
                    activeView === 'chat'
                      ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <span>Chat</span>
                  {chat.messages.length > 0 && (
                    <span className="bg-green-500 text-white text-xs px-1 py-0.5 rounded-full min-w-[1rem] h-4 flex items-center justify-center">
                      {chat.messages.filter(m => m.role === 'assistant').length}
                    </span>
                  )}
                </button>
                
                <button
                  onClick={() => setActiveView('products')}
                  className={`px-2 py-1 rounded text-xs font-medium transition-all flex items-center space-x-1 ${
                    activeView === 'products'
                      ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <span>Products</span>
                  {products.uniqueProducts.length > 0 && (
                    <span className="bg-indigo-500 text-white text-xs px-1 py-0.5 rounded-full min-w-[1rem] h-4 flex items-center justify-center">
                      {products.uniqueProducts.length}
                    </span>
                  )}
                </button>
              </div>
            </div>
            
          </div>
        </div>
      </div>

      {/* Main content area - Fixed height container */}
      <div className="flex-1 flex min-h-0 h-full overflow-hidden">
        
        {/* Desktop layout */}
        <div className="hidden lg:flex w-full h-full">
          {/* Chat Panel - Collapsible with independent scrolling */}
          {isChatExpanded && (
            <div className="w-[380px] flex-shrink-0 border-r border-slate-200 dark:border-slate-700 h-full">
              <ChatPanel
                messages={chat.messages}
                input={input}
                isLoading={chat.isLoading}
                searchLinksData={products.searchLinksData}
                ephemeralHistory={chat.ephemeralHistory}
                currentTurnId={chat.currentTurnId}
                onInputChange={setInput}
                onSendMessage={handleSendMessage}
              />
            </div>
          )}

          {/* Products Panel with independent scrolling */}
          <div className="flex-1 min-w-0 h-full">
            <ProductPanel
              products={products.uniqueProducts}
              selectedPriceBucket={products.selectedPriceBucket}
              selectedBrand={products.selectedBrand}
              onPriceBucketChange={products.setSelectedPriceBucket}
              onBrandChange={products.setSelectedBrand}
              onClearAll={products.clearAllProducts}
              onRemoveProduct={products.removeProduct}
              isExpanded={!isChatExpanded}
              onToggleExpand={() => setIsChatExpanded(!isChatExpanded)}
              input={input}
              isLoading={chat.isLoading}
              onInputChange={setInput}
              onSendMessage={handleSendMessage}
            />
          </div>
        </div>

        {/* Mobile layout with independent scrolling */}
        <div className="flex lg:hidden w-full h-full">
          {activeView === 'products' ? (
            <div className="w-full h-full">
              <ProductPanel
                products={products.uniqueProducts}
                selectedPriceBucket={products.selectedPriceBucket}
                selectedBrand={products.selectedBrand}
                onPriceBucketChange={products.setSelectedPriceBucket}
                onBrandChange={products.setSelectedBrand}
                onClearAll={products.clearAllProducts}
                onRemoveProduct={products.removeProduct}
                isExpanded={true}
                onToggleExpand={() => {}}
                input={input}
                isLoading={chat.isLoading}
                onInputChange={setInput}
                onSendMessage={handleSendMessage}
              />
            </div>
          ) : (
            <div className="w-full h-full">
              <ChatPanel
                messages={chat.messages}
                input={input}
                isLoading={chat.isLoading}
                searchLinksData={products.searchLinksData}
                ephemeralHistory={chat.ephemeralHistory}
                currentTurnId={chat.currentTurnId}
                onInputChange={setInput}
                onSendMessage={handleSendMessage}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 