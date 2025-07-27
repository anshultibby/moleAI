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

// Helper function to make links clickable in text and handle italic formatting
function makeLinksClickable(text: string) {
  // Check if text is undefined or null
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  // First handle markdown-style links [text](url)
  let result = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-600 underline">$1</a>')
  
  // Handle italic text with asterisks *text*
  result = result.replace(/\*([^*]+)\*/g, '<em class="italic text-slate-700 dark:text-slate-300">$1</em>')
  
  // Handle bold text with double asterisks **text**
  result = result.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-slate-800 dark:text-slate-200">$1</strong>')
  
  return result
}

// Component for rendering different message types
function MessageContent({ message, searchLinksData }: { message: Message, searchLinksData: SearchLinksData[] }) {
  if (message.type === 'reasoning') {
    return (
      <div className="text-sm leading-relaxed mb-6">
        <div className="flex items-center mb-2">
          <span className="text-lg mr-2">🧠</span>
          <span className="font-medium text-blue-600 dark:text-blue-400 text-sm">AI Reasoning</span>
        </div>
        <div 
          className="text-slate-700 dark:text-slate-300 ml-6"
          dangerouslySetInnerHTML={{ __html: message.content || '' }}
        />
      </div>
    )
  }

  if (message.type === 'search_links') {
    return (
      <div className="text-sm leading-relaxed mb-6">
        <div className="flex items-center mb-2">
          <span className="text-lg mr-2">🔍</span>
          <span className="font-medium text-green-600 dark:text-green-400 text-sm">Search Results</span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 mb-3 ml-6">{message.content}</div>
        
        {/* Compact link tabs */}
        <div className="flex flex-wrap gap-2 ml-6">
          {searchLinksData.flatMap((linkData: SearchLinksData) => 
            linkData.links.slice(0, 6).map((link, linkIndex: number) => (
              <button
                key={`${linkData.id}-${linkIndex}`}
                onClick={() => {
                  try {
                    // Validate URL before opening
                    const url = new URL(link.url)
                    if (url.protocol === 'http:' || url.protocol === 'https:') {
                      window.open(link.url, '_blank', 'noopener,noreferrer')
                    } else {
                      console.warn('Invalid URL protocol:', link.url)
                    }
                  } catch (error) {
                    console.warn('Invalid URL:', link.url, error)
                    // Try fallback to homepage if available
                    if (link.domain) {
                      window.open(`https://${link.domain}`, '_blank', 'noopener,noreferrer')
                    }
                  }
                }}
                className="px-2 py-1 text-xs bg-green-50 dark:bg-slate-700 border border-green-200 dark:border-slate-600 rounded hover:bg-green-100 dark:hover:bg-slate-600 transition-colors"
                title={link.title || `Visit ${link.domain}`}
              >
                {link.domain ? link.domain.replace('.myshopify.com', '').replace('www.', '') : 'Store'}
              </button>
            ))
          )}
        </div>
      </div>
    )
  }

  if (message.type === 'progress') {
    return (
      <div className="text-sm leading-relaxed mb-6">
        <div className="flex items-center mb-2">
          <span className="text-lg mr-2">⚡</span>
          <span className="font-medium text-orange-600 dark:text-orange-400 text-sm">Progress Update</span>
        </div>
        <div 
          className="text-slate-600 dark:text-slate-400 ml-6"
          dangerouslySetInnerHTML={{ __html: makeLinksClickable(message.content || '') }}
        />
      </div>
    )
  }

  // Default assistant message content - plain text
  if (message.role === 'assistant') {
    return (
      <div className="text-sm leading-relaxed text-slate-800 dark:text-slate-200 mb-6">
        <div 
          dangerouslySetInnerHTML={{ __html: makeLinksClickable(message.content || '') }}
        />
      </div>
    )
  }

  // User message content (in bubble)
  return (
    <div 
      className="text-sm leading-relaxed text-white"
      dangerouslySetInnerHTML={{ __html: message.content || '' }}
    />
  )
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
      const maxHeight = window.innerWidth >= 640 ? 120 : 80 // Different max heights for mobile vs desktop
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
        <div className="max-w-2xl mx-auto px-4 py-6">
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
                        &quot;{suggestion}&quot;
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages with new design - no avatars, user bubbles, assistant plain text */}
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div key={index}>
                {message.role === 'user' ? (
                  // User message as bubble, right-aligned
                  <div className="flex justify-end mb-4">
                    <div className="max-w-xs sm:max-w-sm bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-3 rounded-2xl shadow-sm">
                      <MessageContent message={message} searchLinksData={searchLinksData} />
                    </div>
                  </div>
                ) : (
                  // Assistant message as plain text on background
                  <div className="mb-6">
                    <MessageContent message={message} searchLinksData={searchLinksData} />
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
                  <span className="text-sm font-medium">Finding deals...</span>
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