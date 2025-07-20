import { useState, useRef, useEffect } from 'react'
import { Message, SearchLinksData } from '../types'

interface ChatPanelProps {
  messages: Message[]
  input: string
  isLoading: boolean
  searchLinksData: SearchLinksData[]
  onInputChange: (value: string) => void
  onSendMessage: () => void
}

// Helper function to make links clickable in text
function makeLinksClickable(text: string) {
  const urlRegex = /\[([^\]]+)\]\(([^)]+)\)/g
  return text.replace(urlRegex, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-600 underline">$1</a>')
}

export default function ChatPanel({
  messages,
  input,
  isLoading,
  searchLinksData,
  onInputChange,
  onSendMessage
}: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-r border-slate-200/60 dark:border-slate-600/60">
      {/* Chat Header - Enhanced with gradient and better typography */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-700 dark:to-purple-700 shadow-elegant-lg">
        <div className="px-6 py-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <span className="text-2xl">🛒</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">
                Shopping Assistant
              </h1>
              <p className="text-indigo-100 text-sm font-medium">
                Discover amazing fashion deals with AI
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages - Enhanced spacing and design */}
      <div className="flex-1 overflow-y-auto scrollbar-thin bg-gradient-to-b from-slate-50/50 to-white dark:from-slate-800/50 dark:to-slate-900">
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="text-center pt-12 pb-8">
              {/* Enhanced empty state with better visuals */}
              <div className="mb-8 relative">
                <div className="w-20 h-20 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-elegant-lg">
                  <span className="text-3xl">💬</span>
                </div>
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full animate-pulse-glow"></div>
              </div>
              
              <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200 mb-3 gradient-text">
                Let's find your perfect style!
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 text-lg">
                Ask me anything about fashion and I'll find the best deals for you
              </p>
              
              <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl p-6 shadow-elegant">
                <p className="text-slate-700 dark:text-slate-300 font-medium mb-4">
                  ✨ Try asking me:
                </p>
                <div className="space-y-3 text-left">
                  {[
                    "Find me elegant black dresses under $100",
                    "Show me trendy winter coats",
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
                        "{suggestion}"
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className="group">
              <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  {/* Message bubble with enhanced styling - different styles for different types */}
                  <div
                    className={`px-5 py-3 rounded-2xl shadow-elegant ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white ml-4'
                        : message.type === 'reasoning'
                        ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-700 dark:to-slate-600 border border-blue-200 dark:border-slate-500 mr-4'
                        : message.type === 'search_links'
                        ? 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-slate-700 dark:to-slate-600 border border-green-200 dark:border-slate-500 mr-4'
                        : 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-600 mr-4'
                    }`}
                  >
                    {message.type === 'reasoning' ? (
                      <div className="text-sm leading-relaxed">
                        <div className="flex items-center mb-2">
                          <span className="text-lg mr-2">🧠</span>
                          <span className="font-semibold text-blue-700 dark:text-blue-300">AI Reasoning</span>
                        </div>
                        <div 
                          className="reasoning-display"
                          dangerouslySetInnerHTML={{ __html: message.content }}
                        />
                        <style jsx>{`
                          .reasoning-display .reasoning-step {
                            margin: 8px 0;
                            padding-left: 16px;
                            border-left: 2px solid #3b82f6;
                          }
                          .reasoning-display .reasoning-conclusion {
                            margin: 12px 0;
                            padding: 8px;
                            background: rgba(59, 130, 246, 0.1);
                            border-radius: 6px;
                          }
                          .reasoning-display .reasoning-confidence {
                            margin: 8px 0;
                            font-size: 12px;
                            opacity: 0.8;
                          }
                        `}</style>
                      </div>
                    ) : message.type === 'search_links' ? (
                      <div className="text-sm leading-relaxed">
                        <div className="flex items-center mb-2">
                          <span className="text-lg mr-2">🔍</span>
                          <span className="font-semibold text-green-700 dark:text-green-300">Search Results</span>
                        </div>
                        <div>{message.content}</div>
                                                 {/* Add compact link tabs */}
                         <div className="mt-2 flex flex-wrap gap-1">
                           {searchLinksData.flatMap((linkData: SearchLinksData) => 
                             linkData.links.slice(0, 6).map((link, linkIndex: number) => (
                               <button
                                 key={`${linkData.id}-${linkIndex}`}
                                 onClick={() => window.open(link.url, '_blank')}
                                 className="px-2 py-1 text-xs bg-white dark:bg-slate-600 border border-green-300 dark:border-slate-400 rounded-md hover:bg-green-100 dark:hover:bg-slate-500 transition-colors"
                                 title={link.title}
                               >
                                 {link.domain || new URL(link.url).hostname.replace('www.', '')}
                               </button>
                             ))
                           )}
                         </div>
                      </div>
                    ) : (
                      <div 
                        className="text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{ 
                          __html: message.role === 'assistant' ? makeLinksClickable(message.content) : message.content 
                        }}
                      />
                    )}
                  </div>
                  
                  {/* Timestamp */}
                  <p className={`text-xs mt-2 px-1 ${
                    message.role === 'user' 
                      ? 'text-slate-500 dark:text-slate-400 text-right mr-4' 
                      : 'text-slate-500 dark:text-slate-400 ml-4'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
                
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  message.role === 'user' 
                    ? 'order-1 bg-slate-300 dark:bg-slate-600 ml-3' 
                    : 'order-2 bg-gradient-to-br from-indigo-500 to-purple-600 mr-3'
                }`}>
                  <span className="text-sm">
                    {message.role === 'user' ? '👤' : '🤖'}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start group">
              <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 mr-3">
                <span className="text-sm">🤖</span>
              </div>
              <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 max-w-xs px-5 py-3 rounded-2xl shadow-elegant">
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-slate-600 dark:text-slate-400 font-medium">Finding amazing deals...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input - Enhanced with modern styling */}
      <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-t border-slate-200/60 dark:border-slate-600/60 p-4">
        <div className="max-w-2xl mx-auto">
          <div className="flex space-x-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me to find clothing deals..."
                className="w-full px-4 py-3 pr-12 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:text-white text-sm font-medium placeholder-slate-500 dark:placeholder-slate-400 transition-all"
                disabled={isLoading}
              />
              {input && (
                <button
                  onClick={() => onInputChange('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <button
              onClick={onSendMessage}
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white rounded-xl font-medium text-sm shadow-elegant disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 disabled:transform-none flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Sending</span>
                </>
              ) : (
                <>
                  <span>Send</span>
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