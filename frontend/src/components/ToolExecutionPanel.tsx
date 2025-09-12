'use client'

import { ToolExecutionEvent } from '../types'

interface ToolExecutionPanelProps {
  turnId: string
  toolExecutions: ToolExecutionEvent[]
  isActive: boolean
}

function getToolIcon(toolName: string): string {
  switch (toolName) {
    case 'search_web_tool':
      return '🔍'
    case 'scrape_website':
      return '🌐'
    case 'display_items':
      return '📦'
    case 'grep_resource':
      return '🔎'
    case 'css_select_resource':
      return '🎯'
    default:
      return '⚙️'
  }
}

function getToolDisplayName(toolName: string): string {
  switch (toolName) {
    case 'search_web_tool':
      return 'Web Search'
    case 'scrape_website':
      return 'Website Scraping'
    case 'display_items':
      return 'Product Display'
    case 'grep_resource':
      return 'Content Search'
    case 'css_select_resource':
      return 'Element Selection'
    default:
      return toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'started':
      return 'text-blue-600 dark:text-blue-400'
    case 'progress':
      return 'text-orange-600 dark:text-orange-400'
    case 'completed':
      return 'text-green-600 dark:text-green-400'
    case 'error':
      return 'text-red-600 dark:text-red-400'
    default:
      return 'text-slate-600 dark:text-slate-400'
  }
}

function ProgressBar({ current, total }: { current?: number; total?: number }) {
  if (!current || !total) return null
  
  const percentage = Math.min((current / total) * 100, 100)
  
  return (
    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mt-2">
      <div 
        className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}

function ToolExecutionItem({ execution }: { execution: ToolExecutionEvent }) {
  const icon = getToolIcon(execution.tool_name)
  const displayName = getToolDisplayName(execution.tool_name)
  const statusColor = getStatusColor(execution.status)
  
  return (
    <div className="flex items-start space-x-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
      <div className="text-lg flex-shrink-0 mt-0.5">{icon}</div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-slate-800 dark:text-slate-200">
            {displayName}
          </h4>
          <span className={`text-xs font-medium ${statusColor} capitalize`}>
            {execution.status}
          </span>
        </div>
        
        {execution.message && (
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            {execution.message}
          </p>
        )}
        
        {execution.progress && (
          <div className="mt-2">
            {execution.progress.query && (
              <p className="text-xs text-slate-500 dark:text-slate-500">
                Query: {execution.progress.query}
              </p>
            )}
            
            {execution.progress.url && (
              <p className="text-xs text-slate-500 dark:text-slate-500 truncate">
                URL: {execution.progress.url}
              </p>
            )}
            
            {execution.progress.current && execution.progress.total && (
              <div className="mt-1">
                <div className="flex justify-between text-xs text-slate-500 dark:text-slate-500">
                  <span>{execution.progress.current} of {execution.progress.total}</span>
                  <span>{Math.round((execution.progress.current / execution.progress.total) * 100)}%</span>
                </div>
                <ProgressBar 
                  current={execution.progress.current} 
                  total={execution.progress.total} 
                />
              </div>
            )}
            
            {execution.progress.results_found && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                Found {execution.progress.results_found} results
              </p>
            )}
          </div>
        )}
        
        {execution.error && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-2 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {execution.error}
          </p>
        )}
        
        {execution.status === 'completed' && execution.result && (
          <details className="mt-2">
            <summary className="text-xs text-slate-500 dark:text-slate-500 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300">
              View result
            </summary>
            <pre className="text-xs text-slate-600 dark:text-slate-400 mt-1 bg-slate-100 dark:bg-slate-700 p-2 rounded overflow-x-auto max-h-32">
              {execution.result.length > 500 ? execution.result.substring(0, 500) + '...' : execution.result}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
}

export default function ToolExecutionPanel({ 
  turnId, 
  toolExecutions, 
  isActive 
}: ToolExecutionPanelProps) {
  if (!toolExecutions || toolExecutions.length === 0) {
    return null
  }

  return (
    <div className="mb-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm">
        <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-blue-500 animate-pulse' : 'bg-slate-400'}`} />
            <h3 className="text-sm font-medium text-slate-800 dark:text-slate-200">
              Tool Execution {isActive ? '(Active)' : '(Completed)'}
            </h3>
            <span className="text-xs text-slate-500 dark:text-slate-500">
              {toolExecutions.length} tool{toolExecutions.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
        
        <div className="p-4 space-y-3">
          {toolExecutions.map((execution, index) => (
            <ToolExecutionItem key={`${execution.tool_name}-${index}`} execution={execution} />
          ))}
        </div>
      </div>
    </div>
  )
}
