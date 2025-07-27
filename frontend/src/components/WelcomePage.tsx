'use client'

import { useState, useRef, useEffect } from 'react'

interface WelcomePageProps {
  onStartConversation: (query: string) => void
}

export default function WelcomePage({ onStartConversation }: WelcomePageProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const scrollHeight = textareaRef.current.scrollHeight
      const maxHeight = 100
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + 'px'
    }
  }, [input])

  const handleSend = () => {
    if (!input.trim()) return
    onStartConversation(input.trim())
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const suggestions = [
    "Find me elegant black dresses under $100",
    "Show me trendy winter coats for women",
    "I need a formal outfit for a wedding",
    "Looking for comfortable running shoes",
    "Find sustainable fashion brands",
    "Show me cozy sweaters for fall"
  ]

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex flex-col">
      
      {/* Header with minimal branding in corner */}
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 shadow-sm px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-start">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded flex items-center justify-center">
              <span className="text-white text-xs font-bold">M</span>
            </div>
            <span className="text-sm font-semibold text-slate-800 dark:text-white">MoleAI</span>
          </div>
        </div>
      </div>

      {/* Main content - centered search experience */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-3xl text-center">
          
          {/* Hero section */}
          <div className="mb-6">
            <div className="mb-4 relative">
              <div className="w-16 h-16 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                <span className="text-2xl">🛍️</span>
              </div>
              <div className="absolute -top-1 -right-6 w-6 h-6 bg-yellow-400 rounded-full animate-pulse flex items-center justify-center">
                <span className="text-xs">✨</span>
              </div>
            </div>
            
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-800 dark:text-slate-200 mb-3">
              Find Amazing Deals with AI
            </h2>
            <p className="text-base text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl mx-auto">
              Describe what you're looking for and I'll search across multiple stores to find the best deals that match your style and budget.
            </p>
          </div>

          {/* Search input */}
          <div className="mb-6">
            <div className="relative max-w-2xl mx-auto">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me to find clothing deals... (e.g., 'Find me trendy winter coats under $150')"
                rows={1}
                className="w-full px-4 py-3 pr-14 pb-12 bg-white dark:bg-slate-700 border-2 border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:text-white text-base font-medium placeholder-slate-500 dark:placeholder-slate-400 transition-all resize-none overflow-y-auto scrollbar-thin min-h-[48px] shadow-lg"
              />
              
              {/* Clear button */}
              {input && (
                <button
                  onClick={() => setInput('')}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
              
              {/* Send button */}
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="absolute bottom-2 right-2 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white rounded-lg font-medium text-sm shadow-lg disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 disabled:transform-none flex items-center space-x-1"
              >
                <span>Search</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>

          {/* Sample suggestions */}
          <div className="max-w-5xl mx-auto">
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-3">
              ✨ Try these popular searches:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {suggestions.map((suggestion, index) => (
                <div 
                  key={index}
                  className="flex items-center space-x-2 p-3 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-lg border border-slate-200/60 dark:border-slate-600/60 hover:bg-white/90 dark:hover:bg-slate-700/90 transition-all cursor-pointer group shadow-sm hover:shadow-md transform hover:scale-102"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <div className="w-1.5 h-1.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full group-hover:scale-125 transition-transform"></div>
                  <span className="text-slate-700 dark:text-slate-300 text-xs font-medium text-left flex-1">
                    "{suggestion}"
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Footer note */}
          <div className="mt-8 pt-6 border-t border-slate-200/50 dark:border-slate-700/50">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              I'll search across multiple stores and show you the best deals in real-time
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 