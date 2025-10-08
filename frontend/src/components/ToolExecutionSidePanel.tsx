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
  list_resources: { icon: '📋', displayName: 'List Resources', category: 'Data' },
  display_items: { icon: '✨', displayName: 'Display Products', category: 'Display' },
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
          // Limit to first 5 results for readability
          parsedResult.results = parsedResult.results.slice(0, 5)
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
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden hover:shadow-lg hover:border-indigo-300 dark:hover:border-indigo-700 transition-all duration-200">
      {/* Header - Always visible */}
      <div 
        className="p-4 cursor-pointer hover:bg-gradient-to-r hover:from-slate-50 hover:to-transparent dark:hover:from-slate-700/30 dark:hover:to-transparent transition-all duration-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start space-x-3">
          {/* Tool icon with background */}
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/40 dark:to-purple-900/40 flex items-center justify-center">
            <span className="text-xl">{metadata.icon}</span>
          </div>
          
          {/* Tool info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1.5">
              <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200 truncate">
                {metadata.displayName}
              </h3>
              <span className={`text-sm px-2.5 py-0.5 rounded-full ${status.color} font-medium flex items-center space-x-1`}>
                <span>{status.icon}</span>
                <span>{status.label}</span>
              </span>
            </div>
            
            {/* Quick preview of arguments or results */}
            {!isExpanded && (
              <div className="text-sm text-slate-600 dark:text-slate-400 truncate">
                {/* Show search query for search results */}
                {resultType === 'search_results' && parsedResult?.query ? (
                  <span>
                    <span className="font-medium">query:</span> {parsedResult.query}
                    {parsedResult.results && (
                      <span className="ml-2 text-slate-500">• {parsedResult.results.length} results</span>
                    )}
                  </span>
                ) : hasArgs ? (
                  // Show first argument only
                  Object.entries(args).slice(0, 1).map(([key, value]) => (
                    <span key={key} className="mr-2">
                      <span className="font-medium">{key}:</span> {String(value).substring(0, 40)}
                    </span>
                  ))
                ) : null}
              </div>
            )}
            
            {/* Show error message if present */}
            {execution.error && !isExpanded && (
              <div className="text-sm text-red-600 dark:text-red-400 truncate mt-1">
                {execution.error}
              </div>
            )}
          </div>
          
          {/* Expand/collapse icon */}
          <div className={`flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-colors`}>
            <svg
              className={`w-4 h-4 text-slate-600 dark:text-slate-400 transition-transform duration-300 ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>
      
      {/* Collapsible details */}
      {isExpanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
          {/* Arguments section */}
          {hasArgs && (
            <div className="p-3 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                  Input
                </span>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded p-3 space-y-2">
                {Object.entries(args).map(([key, value]) => {
                  // Format value for display
                  let displayValue = String(value)
                  if (typeof value === 'object') {
                    // If it's an array, show count
                    if (Array.isArray(value)) {
                      displayValue = `[${value.length} items]`
                    } else {
                      displayValue = JSON.stringify(value, null, 2)
                    }
                  }
                  // Truncate long strings
                  if (displayValue.length > 100) {
                    displayValue = displayValue.substring(0, 100) + '...'
                  }
                  
                  return (
                    <div key={key} className="text-sm">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{key}:</span>{' '}
                      <span className="text-slate-600 dark:text-slate-400">
                        {displayValue}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
          
          {/* Result section */}
          {hasResult && execution.status === 'completed' && (
            <div className="p-3">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                  {resultType === 'search_results' ? 'Found Results' : 'Result'}
                </span>
                {resultType === 'search_results' && parsedResult?.results && (
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    ({parsedResult.results.length})
                  </span>
                )}
              </div>
              
              {/* Show query for search results */}
              {resultType === 'search_results' && parsedResult?.query && (
                <div className="mb-3 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg border border-indigo-100 dark:border-indigo-800/30">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-lg">🔍</span>
                    <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-400 uppercase tracking-wide">Search Query</span>
                  </div>
                  <div className="text-base text-slate-800 dark:text-slate-200 font-medium">
                    "{parsedResult.query}"
                  </div>
                </div>
              )}
              
              <div className="bg-white dark:bg-slate-800 rounded max-h-96 overflow-y-auto shadow-sm">
                {resultType === 'search_results' && parsedResult?.results ? (
                  // Special formatting for search results - Clean and readable
                  <div className="divide-y divide-slate-200 dark:divide-slate-700">
                    {parsedResult.results.map((item: any, idx: number) => (
                      <a
                        key={idx}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start space-x-3 p-4 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-transparent dark:hover:from-indigo-900/20 dark:hover:to-transparent transition-all duration-200 group border-l-2 border-transparent hover:border-indigo-500"
                      >
                        {/* Result number badge */}
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/40 transition-colors">
                          <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                            {idx + 1}
                          </span>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          {/* Clickable Title */}
                          <div className="text-base font-semibold text-indigo-600 dark:text-indigo-400 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 mb-2 line-clamp-2 leading-snug flex items-start">
                            {item.title}
                            <svg className="w-4 h-4 ml-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </div>
                          {/* Domain/URL - with icon */}
                          <div className="flex items-center space-x-1 text-xs text-slate-500 dark:text-slate-500">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                            </svg>
                            <span className="truncate">{new URL(item.url).hostname}</span>
                          </div>
                        </div>
                      </a>
                    ))}
                  </div>
                ) : resultType === 'scraped_sites' && parsedResult?.scraped_sites ? (
                  // Special formatting for scraped sites
                  <div className="divide-y divide-slate-200 dark:divide-slate-700">
                    {parsedResult.scraped_sites.map((site: any, idx: number) => {
                      const isSuccess = site.success !== false
                      return (
                        <a
                          key={idx}
                          href={site.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`flex items-center space-x-3 p-4 transition-all duration-200 group border-l-2 ${
                            isSuccess 
                              ? 'hover:bg-gradient-to-r hover:from-green-50 hover:to-transparent dark:hover:from-green-900/20 border-transparent hover:border-green-500'
                              : 'hover:bg-gradient-to-r hover:from-red-50 hover:to-transparent dark:hover:from-red-900/20 border-transparent hover:border-red-500'
                          }`}
                        >
                          {/* Status icon */}
                          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                            isSuccess 
                              ? 'bg-green-100 dark:bg-green-900/40 group-hover:bg-green-200 dark:group-hover:bg-green-900/60'
                              : 'bg-red-100 dark:bg-red-900/40 group-hover:bg-red-200 dark:group-hover:bg-red-900/60'
                          } transition-colors`}>
                            <span className="text-lg">{isSuccess ? '✅' : '❌'}</span>
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="text-base font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 truncate flex items-center">
                              {site.name}
                              <svg className="w-4 h-4 ml-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </div>
                            <div className="flex items-center space-x-1 text-xs text-slate-500 dark:text-slate-500 mt-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                              </svg>
                              <span className="truncate">{new URL(site.url).hostname}</span>
                            </div>
                          </div>
                        </a>
                      )
                    })}
                  </div>
                ) : resultType === 'json' ? (
                  // Default JSON formatting - truncated for readability
                  <pre className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap font-mono p-3 max-h-64 overflow-y-auto">
                    {JSON.stringify(parsedResult, null, 2).substring(0, 500)}
                    {JSON.stringify(parsedResult, null, 2).length > 500 && '\n... (truncated)'}
                  </pre>
                ) : (
                  // Plain text - truncated for readability
                  <div className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap p-3 max-h-64 overflow-y-auto">
                    {String(parsedResult).substring(0, 500)}
                    {String(parsedResult).length > 500 && '\n... (truncated)'}
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Error section */}
          {execution.error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-semibold text-red-700 dark:text-red-400 uppercase tracking-wide">
                  Error
                </span>
              </div>
              <div className="text-sm text-red-600 dark:text-red-400 leading-relaxed">
                {execution.error}
              </div>
            </div>
          )}
          
          {/* Timestamp */}
          {execution.timestamp && (
            <div className="px-3 py-2 border-t border-slate-200 dark:border-slate-700">
              <div className="text-sm text-slate-500 dark:text-slate-500">
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
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-lg">🔧</span>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
                Tool Execution Trace
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
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
              <span className="text-sm text-slate-600 dark:text-slate-400">Active</span>
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