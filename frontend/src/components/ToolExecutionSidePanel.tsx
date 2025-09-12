'use client'

import { useState, useRef, useCallback } from 'react'
import { ToolExecutionEvent } from '../types'

interface ToolExecutionSidePanelProps {
  toolExecutions: Record<string, ToolExecutionEvent>
  isActive: boolean
}


function getSimpleMessage(execution: ToolExecutionEvent): string {
  if (execution.tool_name === 'search_web_tool') {
    console.log('=== DEBUGGING SEARCH EXECUTION ===')
    console.log('Full execution object:', execution)
    console.log('Progress:', execution.progress)
    console.log('Result type:', typeof execution.result)
    console.log('Result content:', execution.result)
    console.log('Message:', execution.message)
    
    // Try to extract query from multiple places
    let query = 'products'
    
    // First try progress
    console.log('Step 1: Checking progress...')
    if (execution.progress?.query) {
      console.log('Found query in progress:', execution.progress.query)
      query = execution.progress.query
    }
    // Then try to extract from result if it has query field
    else if (execution.result && typeof execution.result === 'string') {
      console.log('Step 2: Parsing JSON result...')
      try {
        const parsed = JSON.parse(execution.result)
        console.log('Parsed JSON result:', parsed)
        if (parsed && parsed.query) {
          console.log('Found query in result:', parsed.query)
          query = parsed.query
        } else {
          console.log('No query found in parsed result')
        }
      } catch (e) {
        console.log('JSON parse error:', e)
      }
    }
    // Finally try message
    else if (execution.message && execution.message.includes('for:')) {
      console.log('Step 3: Checking message...')
      const match = execution.message.match(/for:\s*(.+)/)
      if (match) {
        console.log('Found query in message:', match[1])
        query = match[1]
      }
    }
    
    console.log('FINAL EXTRACTED QUERY:', query)
    console.log('=== END DEBUG ===')
    
    if (execution.status === 'completed') {
      return `Searched "${query}"`
    }
    return `Searching "${query}"...`
  }
  
  if (execution.tool_name === 'scrape_website') {
    return execution.status === 'completed' ? 'Checked websites' : 'Browsing websites...'
  }
  
  return 'Working...'
}

function getSimpleLinks(execution: ToolExecutionEvent): Array<{title: string, url: string}> {
  if (execution.tool_name !== 'search_web_tool' || !execution.result) return []
  
  try {
    // New simple format: result is directly an array of {title, url}
    if (Array.isArray(execution.result)) {
      return execution.result.filter((result: any) => result.url)
    }
    
    // Handle string format - parse JSON
    if (typeof execution.result === 'string') {
      // Check if string is empty or just whitespace
      const resultStr = execution.result.trim()
      if (!resultStr) {
        console.log('Empty result string, skipping JSON parse')
        return []
      }
      
      // Check if string starts with valid JSON characters
      if (!resultStr.startsWith('{') && !resultStr.startsWith('[')) {
        console.log('Result string does not appear to be JSON:', resultStr.substring(0, 100))
        return []
      }
      
      try {
        const parsed = JSON.parse(resultStr)
        
        // Handle format: {query: "...", results: [...]}
        if (parsed && typeof parsed === 'object' && parsed.results && Array.isArray(parsed.results)) {
          return parsed.results.map((result: any) => ({
            title: result.title || 'Store',
            url: result.url
          })).filter((result: any) => result.url)
        }
        
        // Handle direct array in string
        if (Array.isArray(parsed)) {
          return parsed.filter((result: any) => result.url)
        }
        
        console.log('Parsed JSON but no valid results array found:', parsed)
      } catch (e) {
        console.log('JSON parse error in links:', e)
        console.log('Failed to parse result string:', resultStr.substring(0, 200))
      }
    }
  } catch (e) {
    console.log('Unexpected error in getSimpleLinks:', e)
  }
  
  return []
}

function getScrapedSites(executions: ToolExecutionEvent[]): Array<{name: string, url: string, success?: boolean}> {
  const scrapedSites: Array<{name: string, url: string, success?: boolean}> = []
  
  executions
    .filter(exec => exec.tool_name === 'scrape_website' && exec.status === 'completed')
    .forEach(exec => {
      if (!exec.result) return
      
      try {
        // Try to parse the new JSON format first
        if (typeof exec.result === 'string' && (exec.result.startsWith('{') || exec.result.startsWith('['))) {
          const parsed = JSON.parse(exec.result)
          
          if (parsed.scraped_sites && Array.isArray(parsed.scraped_sites)) {
            // New detailed format: {"scraped_sites": [{"name": "Zara", "url": "https://...", "success": true}], ...}
            parsed.scraped_sites.forEach((site: any) => {
              if (typeof site === 'object' && site.name && site.url) {
                scrapedSites.push({
                  name: site.name,
                  url: site.url,
                  success: site.success
                })
              } else if (typeof site === 'string') {
                // Fallback for old format: just site names
                scrapedSites.push({
                  name: site,
                  url: `https://${site.toLowerCase().replace(/\s+/g, '')}.com`,
                  success: true
                })
              }
            })
            return
          }
        }
        
        // Fallback to old format parsing
        if (exec.result.includes('_content')) {
          const match = exec.result.match(/(\w+)_content/)
          if (match) {
            const siteName = match[1].charAt(0).toUpperCase() + match[1].slice(1)
            scrapedSites.push({
              name: siteName,
              url: `https://${match[1].toLowerCase()}.com`,
              success: true
            })
          }
        }
      } catch (e) {
        console.log('Error parsing scraped sites result:', e)
        // Fallback to generic website
        scrapedSites.push({
          name: 'Website',
          url: '#',
          success: false
        })
      }
    })
  
  // Only return successfully scraped sites for display
  return scrapedSites.filter(site => site.success !== false)
}

function SimpleCard({ execution, allExecutions }: { execution: ToolExecutionEvent, allExecutions: ToolExecutionEvent[] }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const message = getSimpleMessage(execution)
  const links = getSimpleLinks(execution)
  const scrapedSites = execution.tool_name === 'scrape_website' ? getScrapedSites(allExecutions) : []
  const icon = execution.tool_name === 'search_web_tool' ? '🔍' : '🌐'
  
  const hasExpandableContent = links.length > 0 || scrapedSites.length > 0
  
  return (
    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Header - clickable if has expandable content */}
      <div 
        className={`p-4 ${hasExpandableContent ? 'cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700' : ''}`}
        onClick={() => hasExpandableContent && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">{icon}</span>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex-1">
            {message}
          </h3>
          {/* Expand arrow if has expandable content */}
          {hasExpandableContent && (
            <svg
              className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform duration-200 ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </div>
      </div>
      
      {/* Collapsible content */}
      {isExpanded && hasExpandableContent && (
        <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3 space-y-2">
          {/* Search results */}
          {links.map((link, index) => (
            <a
              key={index}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
            >
              <div className="text-sm font-medium text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 leading-tight">
                {link.title}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {new URL(link.url).hostname}
              </div>
            </a>
          ))}
          
          {/* Scraped sites */}
          {scrapedSites.map((site, index) => (
            <a
              key={index}
              href={site.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
            >
              <div className="text-sm font-medium text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 leading-tight">
                {site.name}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {site.url}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ToolExecutionSidePanel({ 
  toolExecutions, 
  isActive 
}: ToolExecutionSidePanelProps) {
  const [panelWidth, setPanelWidth] = useState(384) // Default 384px (w-96)
  const [isResizing, setIsResizing] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    
    const startX = e.clientX
    const startWidth = panelWidth
    
    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = startX - e.clientX // Negative because we're resizing from the left
      const newWidth = Math.max(280, Math.min(800, startWidth + deltaX)) // Min 280px, max 800px
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
  // Filter to only show search and scraping activities
  const allTasks = Object.values(toolExecutions).filter(execution => 
    execution.tool_name === 'search_web_tool' || execution.tool_name === 'scrape_website'
  )
  
  if (allTasks.length === 0) {
    return null
  }

  // Group tasks: show each search as separate card, but group all scraping into one card
  const searchTasks = allTasks.filter(task => task.tool_name === 'search_web_tool')
  const scrapingTasks = allTasks.filter(task => task.tool_name === 'scrape_website')
  const hasScrapingTasks = scrapingTasks.length > 0
  
  const displayTasks = []
  // Add each search task as a separate card
  displayTasks.push(...searchTasks)
  // Add one representative scraping card if any scraping exists
  if (hasScrapingTasks) displayTasks.push(scrapingTasks[0]) // Use first scraping task as representative

  return (
    <div className="w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-700 flex flex-col">
      {/* Header */}
      <div className="px-4 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
        <div className="flex items-center space-x-3">
          <span className="text-lg">🤖</span>
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Tasks
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {displayTasks.length} task{displayTasks.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>
      
      {/* Tasks */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {displayTasks.map((execution, index) => (
          <SimpleCard
            key={`${execution.tool_name}-${index}`}
            execution={execution}
            allExecutions={allTasks}
          />
        ))}
      </div>
    </div>
  )
}
