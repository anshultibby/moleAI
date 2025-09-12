'use client'

import { useState } from 'react'
import { ToolExecutionEvent } from '../types'

interface ToolExecutionSidePanelProps {
  toolExecutions: Record<string, ToolExecutionEvent>
  isActive: boolean
}

function parseSearchResults(resultString: string): any {
  try {
    const parsed = JSON.parse(resultString.trim())
    return parsed
  } catch {
    return { raw: resultString }
  }
}

function getActivityMessage(toolName: string, execution: ToolExecutionEvent): string {
  switch (toolName) {
    case 'search_web_tool':
      if (execution.status === 'started') return 'Searching the web...'
      if (execution.status === 'progress') return 'Finding the best stores...'
      if (execution.status === 'completed') return 'Found great options!'
      return 'Searching...'
    case 'scrape_website':
      if (execution.status === 'started') return 'Visiting website...'
      if (execution.status === 'progress') return 'Browsing products...'
      if (execution.status === 'completed') return 'Checked website!'
      return 'Browsing...'
    default:
      return 'Working...'
  }
}

function getActivityIcon(toolName: string, status: string): string {
  if (status === 'started' || status === 'progress') {
    return toolName === 'search_web_tool' ? '🔍' : '🌐'
  }
  return toolName === 'search_web_tool' ? '✅' : '🛍️'
}

function extractSearchResults(execution: ToolExecutionEvent): Array<{title: string, url: string}> {
  if (!execution.result || execution.tool_name !== 'search_web_tool') return []
  
  const parsed = parseSearchResults(execution.result)
  
  if (parsed.results && Array.isArray(parsed.results)) {
    return parsed.results.map((result: any) => ({
      title: result.title || 'Untitled',
      url: result.url
    })).filter((result: any) => result.url).slice(0, 8) // Limit to 8 results
  }
  
  return []
}

function extractWebsiteInfo(execution: ToolExecutionEvent): {domain: string, url: string} | null {
  if (execution.tool_name !== 'scrape_website') return null
  
  if (execution.progress?.url) {
    try {
      const url = new URL(execution.progress.url)
      const domain = url.hostname.replace('www.', '').split('.')[0]
      return {
        domain: domain.charAt(0).toUpperCase() + domain.slice(1),
        url: execution.progress.url
      }
    } catch {
      return null
    }
  }
  
  return null
}

interface ActivityCardProps {
  execution: ToolExecutionEvent
  isActive: boolean
}

function ActivityCard({ execution, isActive }: ActivityCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const message = getActivityMessage(execution.tool_name, execution)
  const icon = getActivityIcon(execution.tool_name, execution.status)
  
  if (execution.tool_name === 'search_web_tool') {
    const results = extractSearchResults(execution)
    const query = execution.progress?.query || 'products'
    
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800 overflow-hidden">
        <div className="p-4">
          <div className="flex items-center space-x-3">
            <div className={`text-lg ${isActive ? 'animate-pulse' : ''}`}>{icon}</div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-200">
                {message}
              </h3>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                Looking for: {query}
              </p>
            </div>
            {results.length > 0 && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
              >
                <svg
                  className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>
          
          {results.length > 0 && !isExpanded && (
            <div className="mt-3 text-xs text-blue-600 dark:text-blue-400">
              Found {results.length} stores to check
            </div>
          )}
        </div>
        
        {isExpanded && results.length > 0 && (
          <div className="border-t border-blue-200 dark:border-blue-700 bg-white/50 dark:bg-slate-800/50 p-3 space-y-2">
            {results.map((result, index) => (
              <a
                key={index}
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-2 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors group"
              >
                <div className="text-sm font-medium text-slate-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 leading-tight">
                  {result.title}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
                  {new URL(result.url).hostname}
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    )
  }
  
  if (execution.tool_name === 'scrape_website') {
    const websiteInfo = extractWebsiteInfo(execution)
    
    return (
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800 p-4">
        <div className="flex items-center space-x-3">
          <div className={`text-lg ${isActive ? 'animate-pulse' : ''}`}>{icon}</div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-green-800 dark:text-green-200">
              {message}
            </h3>
            {websiteInfo && (
              <div className="mt-1">
                <a
                  href={websiteInfo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 hover:underline"
                >
                  {websiteInfo.domain}
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }
  
  return null
}

export default function ToolExecutionSidePanel({ 
  toolExecutions, 
  isActive 
}: ToolExecutionSidePanelProps) {
  // Filter to only show search and scraping activities
  const relevantExecutions = Object.values(toolExecutions).filter(execution => 
    execution.tool_name === 'search_web_tool' || execution.tool_name === 'scrape_website'
  )
  
  if (relevantExecutions.length === 0) {
    return null
  }
  
  // Sort by most recent activity first
  const sortedExecutions = relevantExecutions.sort((a, b) => {
    // Active tools first
    if ((a.status === 'started' || a.status === 'progress') && b.status === 'completed') return -1
    if (a.status === 'completed' && (b.status === 'started' || b.status === 'progress')) return 1
    return 0
  })
  
  const activeCount = relevantExecutions.filter(e => e.status === 'started' || e.status === 'progress').length
  const completedCount = relevantExecutions.filter(e => e.status === 'completed').length

  return (
    <div className="w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-700 flex flex-col">
      {/* Header */}
      <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
            <span className="text-white text-sm">🤖</span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              AI Shopping Assistant
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {activeCount > 0 ? `Working on ${activeCount} task${activeCount !== 1 ? 's' : ''}` : 
               `Completed ${completedCount} task${completedCount !== 1 ? 's' : ''}`}
            </p>
          </div>
        </div>
      </div>
      
      {/* Activity Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sortedExecutions.map((execution, index) => (
          <ActivityCard
            key={`${execution.tool_name}-${index}`}
            execution={execution}
            isActive={execution.status === 'started' || execution.status === 'progress'}
          />
        ))}
        
        {completedCount > 0 && activeCount === 0 && (
          <div className="text-center py-4">
            <div className="text-2xl mb-2">🎉</div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              All done! Check out the products I found for you.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
