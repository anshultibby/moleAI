'use client'

import { useState, useRef, useCallback } from 'react'
import { ToolExecutionEvent } from '../types'

interface ToolExecutionSidePanelProps {
  toolExecutions: Record<string, ToolExecutionEvent>
  isActive: boolean
}

// Tool metadata for better display
const TOOL_METADATA: Record<string, { icon: string; displayName: string; category: string }> = {
  search_web_tool: { icon: '🔍', displayName: 'Web Search', category: 'Search' },
  scrape_website: { icon: '🌐', displayName: 'Scrape Website', category: 'Extraction' },
  extract_products: { icon: '🛍️', displayName: 'Extract Products', category: 'Extraction' },
  get_resource: { icon: '📦', displayName: 'Get Resource', category: 'Data' },
  create_checklist: { icon: '✅', displayName: 'Create Checklist', category: 'Planning' },
  update_checklist_item: { icon: '📝', displayName: 'Update Checklist', category: 'Planning' },
  // Add more tools as needed
}

function getToolMetadata(toolName: string) {
  return TOOL_METADATA[toolName] || { 
    icon: '🔧', 
    displayName: toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    category: 'Tool'
  }
}

function ToolCard({ execution }: { execution: ToolExecutionEvent }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const metadata = getToolMetadata(execution.tool_name)
  
  // Extract arguments
  const args = execution.progress?.arguments || {}
  const hasArgs = Object.keys(args).length > 0
  
  // Extract result
  const result = execution.result
  const hasResult = result && result.length > 0
  
  // Parse result if it's JSON
  let parsedResult: any = null
  let resultType: 'json' | 'text' | 'search_results' | 'scraped_sites' = 'text'
  if (typeof result === 'string' && (result.trim().startsWith('{') || result.trim().startsWith('['))) {
    try {
      parsedResult = JSON.parse(result)
      resultType = 'json'
      
      // Detect special result types
      if (parsedResult && typeof parsedResult === 'object') {
        // Search results format: {query: "...", results: [{title, url, description}]}
        if (parsedResult.query && Array.isArray(parsedResult.results)) {
          resultType = 'search_results'
        }
        // Scraped sites format: {scraped_sites: [{name, url, success}]}
        else if (Array.isArray(parsedResult.scraped_sites)) {
          resultType = 'scraped_sites'
        }
      }
    } catch (e) {
      // Not valid JSON, treat as text
      parsedResult = result
    }
  } else {
    parsedResult = result
  }
  
  // Determine status color and icon
  const statusConfig = {
    started: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', icon: '⏳', label: 'Running' },
    progress: { color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400', icon: '⚙️', label: 'In Progress' },
    completed: { color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: '✅', label: 'Completed' },
    error: { color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', icon: '❌', label: 'Error' }
  }
  
  const status = statusConfig[execution.status] || statusConfig.started
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* Header - Always visible */}
      <div 
        className="p-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start space-x-3">
          {/* Tool icon */}
          <span className="text-2xl flex-shrink-0">{metadata.icon}</span>
          
          {/* Tool info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate">
                {metadata.displayName}
              </h3>
              <span className={`text-xs px-2 py-0.5 rounded-full ${status.color} font-medium`}>
                {status.icon} {status.label}
              </span>
            </div>
            
            {/* Quick preview of arguments or results */}
            {!isExpanded && (
              <div className="text-xs text-slate-600 dark:text-slate-400 truncate">
                {/* Show search query for search results */}
                {resultType === 'search_results' && parsedResult?.query ? (
                  <span>
                    <span className="font-medium">query:</span> {parsedResult.query}
                    {parsedResult.results && (
                      <span className="ml-2 text-slate-500">• {parsedResult.results.length} results</span>
                    )}
                  </span>
                ) : hasArgs ? (
                  // Show first 2 arguments
                  Object.entries(args).slice(0, 2).map(([key, value]) => (
                    <span key={key} className="mr-2">
                      <span className="font-medium">{key}:</span> {String(value).substring(0, 30)}
                    </span>
                  ))
                ) : null}
              </div>
            )}
            
            {/* Show error message if present */}
            {execution.error && !isExpanded && (
              <div className="text-xs text-red-600 dark:text-red-400 truncate mt-1">
                {execution.error}
              </div>
            )}
          </div>
          
          {/* Expand/collapse icon */}
          <svg
            className={`w-5 h-5 text-slate-400 dark:text-slate-500 transition-transform duration-200 flex-shrink-0 ${
              isExpanded ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {/* Collapsible details */}
      {isExpanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
          {/* Arguments section */}
          {hasArgs && (
            <div className="p-3 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                  Input Arguments
                </span>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded p-2 space-y-1">
                {Object.entries(args).map(([key, value]) => (
                  <div key={key} className="text-xs">
                    <span className="font-medium text-slate-700 dark:text-slate-300">{key}:</span>{' '}
                    <span className="text-slate-600 dark:text-slate-400">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Result section */}
          {hasResult && execution.status === 'completed' && (
            <div className="p-3">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                  Result
                </span>
                {resultType === 'search_results' && parsedResult?.results && (
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {parsedResult.results.length} results
                  </span>
                )}
              </div>
              <div className="bg-white dark:bg-slate-800 rounded max-h-96 overflow-y-auto">
                {resultType === 'search_results' && parsedResult?.results ? (
                  // Special formatting for search results
                  <div className="divide-y divide-slate-200 dark:divide-slate-700">
                    {parsedResult.results.map((item: any, idx: number) => (
                      <a
                        key={idx}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
                      >
                        <div className="text-sm font-medium text-indigo-600 dark:text-indigo-400 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 mb-1 line-clamp-2">
                          {item.title}
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400 mb-1 line-clamp-2">
                          {item.description}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-500 truncate">
                          {item.url}
                        </div>
                      </a>
                    ))}
                  </div>
                ) : resultType === 'scraped_sites' && parsedResult?.scraped_sites ? (
                  // Special formatting for scraped sites
                  <div className="divide-y divide-slate-200 dark:divide-slate-700">
                    {parsedResult.scraped_sites.map((site: any, idx: number) => (
                      <a
                        key={idx}
                        href={site.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">{site.success !== false ? '✅' : '❌'}</span>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 truncate">
                              {site.name}
                            </div>
                            <div className="text-xs text-slate-500 dark:text-slate-500 truncate">
                              {site.url}
                            </div>
                          </div>
                        </div>
                      </a>
                    ))}
                  </div>
                ) : resultType === 'json' ? (
                  // Default JSON formatting
                  <pre className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap font-mono p-2">
                    {JSON.stringify(parsedResult, null, 2)}
                  </pre>
                ) : (
                  // Plain text
                  <div className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap p-2">
                    {String(parsedResult)}
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Error section */}
          {execution.error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wide">
                  Error
                </span>
              </div>
              <div className="text-xs text-red-600 dark:text-red-400">
                {execution.error}
              </div>
            </div>
          )}
          
          {/* Timestamp */}
          {execution.timestamp && (
            <div className="px-3 py-2 border-t border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-500">
                {new Date(execution.timestamp).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ToolExecutionSidePanel({ 
  toolExecutions, 
  isActive 
}: ToolExecutionSidePanelProps) {
  const [panelWidth, setPanelWidth] = useState(420) // Default 420px
  const [isResizing, setIsResizing] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    
    const startX = e.clientX
    const startWidth = panelWidth
    
    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startX - e.clientX // Negative because we're resizing from the left
      const newWidth = Math.max(320, Math.min(800, startWidth + deltaX)) // Min 320px, max 800px
      setPanelWidth(newWidth)
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }, [panelWidth])

  const allTools = Object.values(toolExecutions)
  
  if (allTools.length === 0) {
    return null
  }

  // Count by status
  const statusCounts = allTools.reduce((acc, tool) => {
    acc[tool.status] = (acc[tool.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div 
      ref={panelRef}
      className="bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col relative"
      style={{ width: `${panelWidth}px` }}
    >
      {/* Resize handle */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-indigo-500 transition-colors z-10 ${
          isResizing ? 'bg-indigo-500' : 'bg-transparent hover:bg-indigo-300'
        }`}
        onMouseDown={handleMouseDown}
        title="Drag to resize panel"
      />
      
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm">🔧</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                Tool Execution Trace
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {allTools.length} tool call{allTools.length !== 1 ? 's' : ''}
                {statusCounts.completed > 0 && ` · ${statusCounts.completed} completed`}
                {statusCounts.started > 0 && ` · ${statusCounts.started} running`}
                {statusCounts.error > 0 && ` · ${statusCounts.error} failed`}
              </p>
            </div>
          </div>
          
          {/* Active indicator */}
          {isActive && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-slate-600 dark:text-slate-400">Active</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Tool cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {allTools.map((execution, index) => (
          <ToolCard
            key={execution.tool_call_id || `${execution.tool_name}-${index}`}
            execution={execution}
          />
        ))}
      </div>
    </div>
  )
}