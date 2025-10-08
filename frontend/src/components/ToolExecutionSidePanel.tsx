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
  
  // Try to parse the result field as JSON
  if (typeof result === 'string' && result.length > 0) {
    const trimmed = result.trim()
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        parsedResult = JSON.parse(result)
        
        // Detect special result types
        if (parsedResult && typeof parsedResult === 'object') {
          // Search results format: {query: "...", results: [{title, url}]}
          if (parsedResult.query && Array.isArray(parsedResult.results) && parsedResult.results.length > 0) {
            resultType = 'search_results'
            // Limit to first 5 results for readability
            parsedResult.results = parsedResult.results.slice(0, 5)
            console.log('✅ Detected search_results with', parsedResult.results.length, 'results for query:', parsedResult.query)
          }
          // Scraped sites format: {scraped_sites: [{name, url, success}]}
          else if (Array.isArray(parsedResult.scraped_sites)) {
            resultType = 'scraped_sites'
          }
          else {
            // Generic JSON
            resultType = 'json'
          }
        }
      } catch (e) {
        // Not valid JSON, treat as text
        console.warn('Failed to parse tool result as JSON:', e)
        parsedResult = result
        resultType = 'text'
      }
    } else {
      // Plain text result
      parsedResult = result
      resultType = 'text'
    }
  } else {
    parsedResult = result
    resultType = 'text'
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
    <div className="bg-white dark:bg-slate-800/95 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shadow-md overflow-hidden hover:shadow-xl hover:border-indigo-400/60 dark:hover:border-indigo-500/60 transition-all duration-300 ease-out backdrop-blur-sm">
      {/* Header - Always visible */}
      <div 
        className="p-4 cursor-pointer hover:bg-gradient-to-r hover:from-indigo-50/50 hover:to-transparent dark:hover:from-indigo-900/20 dark:hover:to-transparent transition-all duration-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start space-x-3">
          {/* Tool icon with background */}
          <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-100 via-purple-100 to-pink-100 dark:from-indigo-900/50 dark:via-purple-900/50 dark:to-pink-900/50 flex items-center justify-center shadow-sm ring-1 ring-slate-200/50 dark:ring-slate-700/50">
            <span className="text-xl">{metadata.icon}</span>
          </div>
          
          {/* Tool info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 truncate">
                {metadata.displayName}
              </h3>
              <span className={`text-xs px-2.5 py-1 rounded-lg ${status.color} font-semibold flex items-center space-x-1.5 shadow-sm`}>
                <span className="text-sm">{status.icon}</span>
                <span>{status.label}</span>
              </span>
            </div>
            
            {/* Quick preview of arguments or results */}
            {!isExpanded && (
              <div className="text-sm text-slate-600 dark:text-slate-400">
                {/* Show search query for search results */}
                {resultType === 'search_results' && parsedResult?.query ? (
                  <div className="flex items-center space-x-2">
                    <span className="text-indigo-600 dark:text-indigo-400 font-medium truncate">
                      {parsedResult.query}
                    </span>
                    {parsedResult.results && (
                      <span className="flex-shrink-0 text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full">
                        {parsedResult.results.length} results
                      </span>
                    )}
                  </div>
                ) : hasArgs ? (
                  // Show first argument only
                  <div className="truncate">
                    {Object.entries(args).slice(0, 1).map(([key, value]) => (
                      <span key={key} className="mr-2">
                        <span className="font-medium">{key}:</span> {String(value).substring(0, 40)}
                      </span>
                    ))}
                  </div>
                ) : execution.status === 'completed' && hasResult ? (
                  <span className="text-xs text-green-600 dark:text-green-400">✓ Click to view result</span>
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
          <div className={`flex-shrink-0 w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-all duration-200 shadow-sm ring-1 ring-slate-200/50 dark:ring-slate-700/50`}>
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
        <div className="border-t border-slate-200/80 dark:border-slate-700/80 bg-gradient-to-b from-slate-50 to-slate-100/50 dark:from-slate-900/50 dark:to-slate-900/30">
          {/* Arguments section */}
          {hasArgs && (
            <div className="p-4 border-b border-slate-200/80 dark:border-slate-700/80">
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider bg-slate-200 dark:bg-slate-700 px-2 py-1 rounded-md">
                  Input
                </span>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-lg p-3.5 space-y-2.5 shadow-sm ring-1 ring-slate-200/50 dark:ring-slate-700/50">
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
            <div className="p-4">
              <div className="flex items-center space-x-2 mb-3">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider bg-slate-200 dark:bg-slate-700 px-2 py-1 rounded-md">
                  {resultType === 'search_results' ? 'Found Results' : 'Result'}
                </span>
                {resultType === 'search_results' && parsedResult?.results && (
                  <span className="text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-1 rounded-md font-semibold">
                    {parsedResult.results.length} results
                  </span>
                )}
              </div>
              
              {/* Show query for search results */}
              {resultType === 'search_results' && parsedResult?.query && (
                <div className="mb-4 p-4 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/30 dark:via-purple-900/30 dark:to-pink-900/30 rounded-xl border border-indigo-200/60 dark:border-indigo-800/40 shadow-sm ring-1 ring-indigo-100/50 dark:ring-indigo-800/20">
                  <div className="flex items-center space-x-2 mb-2.5">
                    <span className="text-xl">🔍</span>
                    <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider bg-white/60 dark:bg-slate-800/60 px-2 py-1 rounded-md">Search Query</span>
                  </div>
                  <div className="text-base text-slate-900 dark:text-slate-100 font-semibold leading-relaxed">
                    "{parsedResult.query}"
                  </div>
                </div>
              )}
              
              <div className="bg-white dark:bg-slate-800 rounded-xl max-h-96 overflow-y-auto shadow-sm ring-1 ring-slate-200/50 dark:ring-slate-700/50">
                {resultType === 'search_results' && parsedResult?.results ? (
                  // Special formatting for search results - Clean and readable
                  <div className="divide-y divide-slate-200/60 dark:divide-slate-700/60">
                    {parsedResult.results.map((item: any, idx: number) => (
                      <a
                        key={idx}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start space-x-3 p-4 hover:bg-gradient-to-r hover:from-indigo-50/80 hover:to-transparent dark:hover:from-indigo-900/30 dark:hover:to-transparent transition-all duration-200 group border-l-3 border-transparent hover:border-indigo-500 dark:hover:border-indigo-400"
                      >
                        {/* Result number badge */}
                        <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center group-hover:from-indigo-100 group-hover:to-indigo-200 dark:group-hover:from-indigo-900/50 dark:group-hover:to-indigo-800/50 transition-all duration-200 shadow-sm">
                          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 group-hover:text-indigo-700 dark:group-hover:text-indigo-300">
                            {idx + 1}
                          </span>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          {/* Clickable Title */}
                          <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 mb-2 line-clamp-2 leading-snug flex items-start">
                            {item.title}
                            <svg className="w-3.5 h-3.5 ml-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </div>
                          {/* Domain/URL - with icon */}
                          <div className="flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                            </svg>
                            <span className="truncate font-medium">{new URL(item.url).hostname}</span>
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
                  // JSON formatting - More readable structured display
                  <div className="p-4 space-y-2">
                    {(() => {
                      // Render JSON in a more human-readable way
                      const renderValue = (value: any, depth: number = 0): JSX.Element => {
                        const indent = depth * 16;
                        
                        if (value === null || value === undefined) {
                          return <span className="text-slate-400 italic">null</span>
                        }
                        
                        if (typeof value === 'boolean') {
                          return <span className="text-purple-600 dark:text-purple-400 font-medium">{value ? 'true' : 'false'}</span>
                        }
                        
                        if (typeof value === 'number') {
                          return <span className="text-blue-600 dark:text-blue-400 font-medium">{value}</span>
                        }
                        
                        if (typeof value === 'string') {
                          // Check if it's a URL
                          if (value.startsWith('http://') || value.startsWith('https://')) {
                            return (
                              <a href={value} target="_blank" rel="noopener noreferrer" className="text-indigo-600 dark:text-indigo-400 hover:underline">
                                {value}
                              </a>
                            )
                          }
                          return <span className="text-green-700 dark:text-green-400">{value}</span>
                        }
                        
                        if (Array.isArray(value)) {
                          if (value.length === 0) {
                            return <span className="text-slate-400 italic">empty array</span>
                          }
                          return (
                            <div className="space-y-1.5">
                              {value.slice(0, 10).map((item, idx) => (
                                <div key={idx} style={{ paddingLeft: `${indent + 16}px` }} className="flex items-start space-x-2">
                                  <span className="text-slate-500 dark:text-slate-400 font-medium text-xs mt-0.5">{idx + 1}.</span>
                                  {renderValue(item, depth + 1)}
                                </div>
                              ))}
                              {value.length > 10 && (
                                <div style={{ paddingLeft: `${indent + 16}px` }} className="text-slate-400 text-xs italic">
                                  ... and {value.length - 10} more items
                                </div>
                              )}
                            </div>
                          )
                        }
                        
                        if (typeof value === 'object') {
                          const entries = Object.entries(value).slice(0, 20);
                          if (entries.length === 0) {
                            return <span className="text-slate-400 italic">empty object</span>
                          }
                          return (
                            <div className="space-y-2">
                              {entries.map(([key, val]) => (
                                <div key={key} style={{ paddingLeft: `${indent + 16}px` }} className="flex items-start space-x-2">
                                  <span className="text-slate-700 dark:text-slate-300 font-semibold text-sm min-w-fit">{key}:</span>
                                  <div className="flex-1">{renderValue(val, depth + 1)}</div>
                                </div>
                              ))}
                              {Object.entries(value).length > 20 && (
                                <div style={{ paddingLeft: `${indent + 16}px` }} className="text-slate-400 text-xs italic">
                                  ... and {Object.entries(value).length - 20} more fields
                                </div>
                              )}
                            </div>
                          )
                        }
                        
                        return <span className="text-slate-600 dark:text-slate-400">{String(value)}</span>
                      }
                      
                      return renderValue(parsedResult)
                    })()}
                  </div>
                ) : (
                  // Plain text - better formatting
                  <div className="p-4">
                    <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {String(parsedResult).substring(0, 1000)}
                      {String(parsedResult).length > 1000 && (
                        <span className="block mt-2 text-xs text-slate-400 italic">... (showing first 1000 characters)</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Error section */}
          {execution.error && (
            <div className="p-4 bg-gradient-to-br from-red-50 to-red-100/50 dark:from-red-900/30 dark:to-red-900/20 border-t border-red-200/60 dark:border-red-800/40">
              <div className="flex items-center space-x-2 mb-2.5">
                <span className="text-xs font-bold text-red-700 dark:text-red-400 uppercase tracking-wider bg-white/60 dark:bg-slate-800/60 px-2 py-1 rounded-md">
                  Error
                </span>
              </div>
              <div className="text-sm text-red-700 dark:text-red-300 leading-relaxed font-medium">
                {execution.error}
              </div>
            </div>
          )}
          
          {/* Timestamp */}
          {execution.timestamp && (
            <div className="px-4 py-2.5 border-t border-slate-200/80 dark:border-slate-700/80 bg-slate-50/50 dark:bg-slate-900/30">
              <div className="flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">{new Date(execution.timestamp).toLocaleTimeString()}</span>
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