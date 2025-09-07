import { Message, SearchLinksData } from '../types'

// Helper function to make links clickable in text and handle formatting including line breaks
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
  
  // Convert line breaks to HTML <br/> tags
  result = result.replace(/\n/g, '<br/>')
  
  return result
}

interface MessageContentProps {
  message: Message
  searchLinksData: SearchLinksData[]
}

export default function MessageContent({ message, searchLinksData }: MessageContentProps) {
  if (message.type === 'reasoning') {
    return (
      <div className="text-sm leading-relaxed mb-6">
        <div className="flex items-center mb-2">
          <span className="text-lg mr-2">🧠</span>
          <span className="font-medium text-blue-600 dark:text-blue-400 text-sm">AI Reasoning</span>
        </div>
        <div 
          className="text-slate-700 dark:text-slate-300 ml-6"
          dangerouslySetInnerHTML={{ __html: makeLinksClickable(message.content || '') }}
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
      dangerouslySetInnerHTML={{ __html: makeLinksClickable(message.content || '') }}
    />
  )
} 