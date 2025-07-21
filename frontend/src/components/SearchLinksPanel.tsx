import React from 'react'
import { SearchLinksData } from '../types'

interface SearchLinksPanelProps {
  searchLinksData: SearchLinksData
  onRemove?: (id: string) => void
}

export default function SearchLinksPanel({ searchLinksData, onRemove }: SearchLinksPanelProps) {
  const handleLinkClick = (url: string, title: string) => {
    // Track click for analytics if needed
    console.log(`User clicked link: ${title} - ${url}`)
    // Open in new tab
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const getDomainColor = (domain: string) => {
    // Map common domains to brand colors
    const domainColors: { [key: string]: string } = {
      'amazon.com': 'bg-orange-100 text-orange-800 border-orange-200',
      'target.com': 'bg-red-100 text-red-800 border-red-200',
      'walmart.com': 'bg-blue-100 text-blue-800 border-blue-200',
      'bestbuy.com': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'costco.com': 'bg-red-100 text-red-800 border-red-200',
      'ebay.com': 'bg-purple-100 text-purple-800 border-purple-200',
      'zara.com': 'bg-gray-100 text-gray-800 border-gray-200',
      'hm.com': 'bg-red-100 text-red-800 border-red-200',
      'uniqlo.com': 'bg-red-100 text-red-800 border-red-200',
    }
    
    // Check for partial matches
    for (const [domainKey, colorClass] of Object.entries(domainColors)) {
      if (domain.includes(domainKey.replace('.com', ''))) {
        return colorClass
      }
    }
    
    // Default color
    return 'bg-slate-100 text-slate-800 border-slate-200'
  }

  const formatScore = (score: number) => {
    return Math.round(score * 100)
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-elegant border border-slate-200 dark:border-slate-600 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-lg">Search Results</h3>
              <p className="text-blue-100 text-sm">
                Found {searchLinksData.total_results} results for &quot;{searchLinksData.search_query}&quot;
              </p>
            </div>
          </div>
          
          {onRemove && searchLinksData.id && (
            <button
              onClick={() => onRemove(searchLinksData.id!)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="Dismiss search links"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Links Grid */}
      <div className="p-6">
        <div className="grid gap-4">
          {searchLinksData.links.map((link, index) => (
            <div
              key={index}
              onClick={() => handleLinkClick(link.url, link.title)}
              className="group p-4 border border-slate-200 dark:border-slate-600 rounded-lg hover:border-blue-300 dark:hover:border-blue-500 hover:shadow-md transition-all cursor-pointer bg-slate-50 dark:bg-slate-700 hover:bg-blue-50 dark:hover:bg-slate-600"
            >
              <div className="flex items-start space-x-4">
                {/* Link Icon */}
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-blue-200 dark:group-hover:bg-blue-800 transition-colors">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </div>

                {/* Link Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-slate-900 dark:text-slate-100 line-clamp-2 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">
                      {link.title}
                    </h4>
                    
                    {/* Domain Badge */}
                    <span className={`ml-3 px-2 py-1 text-xs font-medium rounded-full border flex-shrink-0 ${getDomainColor(link.domain)}`}>
                      {link.domain}
                    </span>
                  </div>

                  {/* Description */}
                  {link.description && (
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3 line-clamp-2">
                      {link.description}
                    </p>
                  )}

                  {/* Highlights */}
                  {link.highlights && link.highlights.length > 0 && (
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-2">
                        {link.highlights.slice(0, 2).map((highlight, highlightIndex) => (
                          <span
                            key={highlightIndex}
                            className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-300 px-2 py-1 rounded-full border border-yellow-200 dark:border-yellow-700"
                          >
                            &quot;{highlight.length > 50 ? highlight.substring(0, 50) + '...' : highlight}&quot;
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
                      <span>Click to visit</span>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </div>
                    
                    {/* Relevance Score */}
                    {link.score > 0 && (
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-slate-500 dark:text-slate-400">Relevance:</span>
                        <div className="flex items-center space-x-1">
                          <div className="w-16 h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${Math.min(100, formatScore(link.score))}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                            {formatScore(link.score)}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer with total count */}
        {searchLinksData.total_results > searchLinksData.links.length && (
          <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
            <p className="text-sm text-slate-600 dark:text-slate-400 text-center">
              Showing {searchLinksData.links.length} of {searchLinksData.total_results} total results
            </p>
          </div>
        )}
      </div>
    </div>
  )
} 