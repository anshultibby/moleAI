import { useState } from 'react'

// Helper function to make links clickable
function makeLinksClickable(text: string) {
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

interface ThinkingPanelProps {
  turnId: string
  ephemeralMessages: string[]
  isActive: boolean
}

export default function ThinkingPanel({ 
  turnId, 
  ephemeralMessages, 
  isActive 
}: ThinkingPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Filter out empty or whitespace-only messages
  const validMessages = ephemeralMessages.filter(msg => msg && msg.trim().length > 0)
  
  if (validMessages.length === 0 && !isActive) return null
  
  // Split messages into previous and current
  const previousMessages = isActive && validMessages.length > 1 ? validMessages.slice(0, -1) : []
  const currentMessage = isActive && validMessages.length > 0 ? validMessages[validMessages.length - 1] : null
  const allMessages = isActive ? validMessages : validMessages // For completed turns, show all
  
  // Show summary for collapsed state
  const displaySummary = previousMessages.length > 0 
    ? `${previousMessages.length} previous step${previousMessages.length > 1 ? 's' : ''}`
    : null
  
  return (
    <div className="my-3">
      {/* Collapsible panel for previous messages (only shown if there are previous messages) */}
      {(previousMessages.length > 0 || (!isActive && validMessages.length > 1)) && (
        <div className="mb-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors w-full text-left"
          >
            <span className="text-lg">💭</span>
            <span className="flex-1 italic">
              {isActive 
                ? displaySummary || 'Previous steps'
                : `Performed ${validMessages.length} step${validMessages.length > 1 ? 's' : ''}`
              }
            </span>
            <span className="text-xs bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-full">
              {isActive ? previousMessages.length : validMessages.length}
            </span>
            <svg 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {/* Expanded previous messages */}
          {isExpanded && (
            <div className="mt-2 ml-6 space-y-2 text-sm">
              {(isActive ? previousMessages : validMessages).map((msg, index) => (
                <div 
                  key={index}
                  className="text-slate-400 dark:text-slate-500 italic border-l-2 border-slate-200 dark:border-slate-600 pl-3 py-1"
                  dangerouslySetInnerHTML={{ __html: makeLinksClickable(msg) }}
                />
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Current active message (shown separately below the collapsible panel) */}
      {isActive && currentMessage && (
        <div className="flex items-start space-x-2 text-sm text-slate-600 dark:text-slate-400">
          <span className="text-lg">💭</span>
          <div 
            className="flex-1 italic"
            dangerouslySetInnerHTML={{ __html: makeLinksClickable(currentMessage) }}
          />
        </div>
      )}
    </div>
  )
} 