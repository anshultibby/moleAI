import { useState, useRef, useEffect } from 'react'
import { Message, SearchLinksData, ToolExecutionEvent } from '../types'
import MessageContent from './MessageContent'
import ThinkingPanel from './ThinkingPanel'
// Removed ToolExecutionPanel - now using side panel

interface ChatPanelProps {
  messages: Message[]
  input: string
  isLoading: boolean
  searchLinksData: SearchLinksData[]
  ephemeralHistory: {[turnId: string]: string[]}
  currentTurnId: string | null
  activeToolExecutions: {[turnId: string]: ToolExecutionEvent[]}
  onInputChange: (value: string) => void
  onSendMessage: () => void
  onRemoveProduct?: (id: string) => void
}

export default function ChatPanel({
  messages,
  input,
  isLoading,
  searchLinksData,
  ephemeralHistory,
  currentTurnId,
  activeToolExecutions,
  onInputChange,
  onSendMessage,
  onRemoveProduct
}: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const scrollHeight = textareaRef.current.scrollHeight
      // Use client-side only window reference to avoid hydration mismatch
      const maxHeight = typeof window !== 'undefined' && window.innerWidth >= 640 ? 120 : 80
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + 'px'
    }
  }, [input])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
    // Allow Shift+Enter for new lines in textarea
  }

  return (
    <div className="h-full flex flex-col bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-r border-slate-200/60 dark:border-slate-600/60">
      {/* Chat Messages - Fixed spacing and layout with independent scrolling */}
      <div className="flex-1 overflow-y-auto scrollbar-thin mobile-scroll bg-gradient-to-b from-slate-50/50 to-white dark:from-slate-800/50 dark:to-slate-900 min-h-0">
        <div className="max-w-6xl mx-auto px-3 py-4">
          {messages.length === 0 && (
            <div className="text-center pt-12 pb-8">
              {/* Enhanced empty state with better visuals */}
              <div className="mb-8 relative">
                <div className="w-20 h-20 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-3xl">💬</span>
                </div>
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full animate-pulse"></div>
              </div>
              
              <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200 mb-3">
                Let&apos;s find your perfect style!
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 text-lg">
                Ask me anything about fashion and I&apos;ll find the best deals for you
              </p>
              
              <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
                <p className="text-slate-700 dark:text-slate-300 font-medium mb-4">
                  ✨ Try asking me:
                </p>
                <div className="space-y-3 text-left">
                  {[
                    "Find me elegant black dresses under $100",
                    "Show me running shoes under $100",
                    "I need a formal outfit for a wedding",
                    "What are the best deals on denim jackets?"
                  ].map((suggestion, index) => (
                    <div 
                      key={index}
                      className="flex items-center space-x-3 p-3 bg-slate-50/50 dark:bg-slate-700/50 rounded-xl hover:bg-slate-100/50 dark:hover:bg-slate-600/50 transition-colors cursor-pointer"
                      onClick={() => onInputChange(suggestion)}
                    >
                      <div className="w-2 h-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
                      <span className="text-slate-700 dark:text-slate-300 text-sm font-medium">
                        &quot;{suggestion}&quot;
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages with new design - includes thinking panels */}
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div key={index}>
                {message.role === 'user' ? (
                  <div>
                    {/* User message as bubble, right-aligned */}
                    <div className="flex justify-end mb-4">
                      <div className="max-w-xs sm:max-w-sm bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-3 rounded-2xl shadow-sm">
                        <MessageContent message={message} searchLinksData={searchLinksData} onRemoveProduct={onRemoveProduct} />
                      </div>
                    </div>
                    
                    {/* Show thinking panel for the next assistant message if it exists */}
                    {index + 1 < messages.length && messages[index + 1].role === 'assistant' && messages[index + 1].turnId && (
                      <>
                        <ThinkingPanel 
                          turnId={messages[index + 1].turnId!}
                          ephemeralMessages={ephemeralHistory[messages[index + 1].turnId!] || []}
                          isActive={false}
                        />
                        {/* Tool execution now shown in side panel */}
                      </>
                    )}
                    
                    {/* Show active thinking and tool panels if this is the last user message and we're loading */}
                    {index === messages.length - 1 && currentTurnId && (
                      <>
                        <ThinkingPanel 
                          turnId={currentTurnId}
                          ephemeralMessages={ephemeralHistory[currentTurnId] || []}
                          isActive={true}
                        />
                        {/* Tool execution now shown in side panel */}
                      </>
                    )}
                  </div>
                ) : (
                  // Assistant message as plain text on background
                  <div className="mb-6">
                    <MessageContent message={message} searchLinksData={searchLinksData} onRemoveProduct={onRemoveProduct} />
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="mb-6">
                <div className="flex items-center space-x-3 text-slate-600 dark:text-slate-400">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input - Enhanced with modern styling */}
      <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-t border-slate-200/60 dark:border-slate-600/60 p-3 sm:p-4 flex-shrink-0">
        <div className="max-w-2xl mx-auto">
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me to find clothing deals..."
              rows={1}
              className="w-full px-3 sm:px-4 py-3 sm:py-4 pr-12 sm:pr-14 pb-12 sm:pb-14 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg sm:rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:text-white text-sm sm:text-base font-medium placeholder-slate-500 dark:placeholder-slate-400 transition-all resize-none overflow-y-auto scrollbar-thin min-h-[44px] sm:min-h-[52px]"
              disabled={isLoading}
            />
            
            {/* Clear button */}
            {input && (
              <button
                onClick={() => onInputChange('')}
                className="absolute right-2 sm:right-3 top-2 sm:top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            
            {/* Send button - positioned inside textarea at bottom right */}
            <button
              onClick={onSendMessage}
              disabled={!input.trim() || isLoading}
              className="absolute bottom-2 right-2 sm:bottom-3 sm:right-3 px-3 sm:px-4 py-2 sm:py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white rounded-lg font-medium text-sm shadow-lg disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 disabled:transform-none flex items-center justify-center space-x-1"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <span className="hidden sm:inline text-xs">Send</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 