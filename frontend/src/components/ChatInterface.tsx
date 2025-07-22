'use client'

import { useState } from 'react'
import axios from 'axios'
import ChatPanel from './ChatPanel'
import ProductPanel from './ProductPanel'
import SearchLinksPanel from './SearchLinksPanel'
import ReasoningDisplay from './ReasoningDisplay'
import { Message, Product, ChatResponse, SearchLinksData } from '../types'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [allProducts, setAllProducts] = useState<Product[]>([])
  const [searchLinksData, setSearchLinksData] = useState<SearchLinksData[]>([])
  const [reasoningData, setReasoningData] = useState<any[]>([])
  const [selectedPriceBucket, setSelectedPriceBucket] = useState('')
  const [selectedBrand, setSelectedBrand] = useState('')
  
  // New state for mobile-friendly toggle system
  const [activeView, setActiveView] = useState<'products' | 'chat'>('products')
  const [isChatExpanded, setIsChatExpanded] = useState(false)

  const removeProduct = (productId: string) => {
    setAllProducts(prev => prev.filter(p => p.id !== productId))
  }

  const removeSearchLinks = (searchLinksId: string) => {
    setSearchLinksData(prev => prev.filter(s => s.id !== searchLinksId))
  }

  const clearAllProducts = () => {
    setAllProducts([])
    setSearchLinksData([])
    setReasoningData([])
    setSelectedPriceBucket('')
    setSelectedBrand('')
  }

  const handleLogout = () => {
    sessionStorage.removeItem('shopmole_authenticated')
    window.location.reload()
  }

  // Filter out duplicate products based on name and store
  const getUniqueProducts = (products: Product[]): Product[] => {
    const seen = new Set<string>()
    return products.filter(product => {
      const key = `${product.product_name || product.name}-${product.store}-${product.price}`
      if (seen.has(key)) {
        console.log(`Duplicate product filtered out: ${key}`)
        return false
      }
      seen.add(key)
      return true
    })
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Clear previous results before starting new query
    setAllProducts([])
    setSearchLinksData([])
    setReasoningData([])
    setSelectedPriceBucket('')
    setSelectedBrand('')

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Use streaming endpoint for real-time updates
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      console.log('Attempting to connect to backend at:', apiUrl)
      
    const response = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              console.log('Streaming update:', data)
              
              // Handle different types of streaming updates
              if (data.type === 'reasoning') {
                const reasoningMessage: Message = {
                  role: 'assistant',
                  content: data.data.formatted_text || data.data.title,
                  timestamp: new Date().toISOString(),
                  type: 'reasoning'
                }
                setMessages(prev => [...prev, reasoningMessage])
                setReasoningData(prev => [...prev, data.data])
              }
              
              else if (data.type === 'search_links') {
                const searchMessage: Message = {
                  role: 'assistant',
                  content: `Found ${data.data.links?.length || 0} shopping sites for "${data.data.search_query}"`,
                  timestamp: new Date().toISOString(),
                  type: 'search_links'
                }
                setMessages(prev => [...prev, searchMessage])
                
                const uniqueLinks = {
                  ...data.data,
                  links: data.data.links?.filter((link: any, index: number, self: any[]) => 
                    index === self.findIndex((l: any) => l.url === link.url)
                  ) || []
                }
                
                setSearchLinksData(prev => [...prev, {
                  ...uniqueLinks,
                  id: `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
                }])
              }
              
              else if (data.type === 'product') {
                const product = {
                  ...data.data,
                  id: data.data.id || `product-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
                }
                
                // Debug logging
                console.log('Received product:', {
                  name: product.product_name,
                  store: product.store,
                  store_name: product.store_name,
                  price: product.price
                })
                
                // Filter duplicates when adding
                setAllProducts(prev => {
                  const combined = [...prev, product]
                  const unique = getUniqueProducts(combined)
                  console.log(`Products after dedup: ${prev.length} + 1 → ${unique.length}`)
                  return unique
                })
                // Switch to products tab on mobile when we get the first product
                setActiveView('products')
              }
              
              else if (data.type === 'chat_response') {
                const finalMessage: Message = {
                  role: 'assistant',
                  content: data.message || 'Search completed.',
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, finalMessage])
                // Switch to products tab when search is complete if we have products
                setAllProducts(prev => {
                  if (prev.length > 0) {
                    setActiveView('products')
                  }
                  return prev
                })
              }
              
              else if (data.type === 'error') {
                const errorMessage: Message = {
                  role: 'assistant',
                  content: `Sorry, I encountered an error: ${data.message || 'Unknown error'}`,
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, errorMessage])
              }
              
              else if (data.type === 'start') {
                const startMessage: Message = {
                  role: 'assistant', 
                  content: data.message || 'Starting search...',
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, startMessage])
              }
              
              else if (data.type === 'progress') {
                const progressMessage: Message = {
                  role: 'assistant',
                  content: data.message || 'Processing...',
                  timestamp: new Date().toISOString(),
                  type: 'progress'
                }
                setMessages(prev => [...prev, progressMessage])
              }
              
            } catch (e) {
              console.error('Error parsing streaming data:', e)
            }
          }
        }
      }

    } catch (error) {
      console.error('Error with streaming:', error)
      
      // Fallback to regular endpoint
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        console.log('Falling back to regular endpoint at:', apiUrl)
        
      const response = await axios.post<ChatResponse>(`${apiUrl}/api/chat`, {
          message: input
        })

        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.response,
          timestamp: response.data.timestamp
        }

        setMessages(prev => [...prev, assistantMessage])
        
        if (response.data.deals_found && response.data.deals_found.length > 0) {
          const newProducts: Product[] = []
          const newSearchLinks: SearchLinksData[] = []
          const newReasoning: any[] = []
          
          response.data.deals_found.forEach(item => {
            console.log('Processing item:', item.type, item)
            
            if (item.type === 'search_links') {
              const searchLinksItem = item as SearchLinksData
              newSearchLinks.push({
                ...searchLinksItem,
                id: searchLinksItem.id || `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
              })
            } else if (item.type === 'reasoning') {
              newReasoning.push({
                ...item,
                id: item.id || `reasoning-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
              })
            } else {
              const productItem = item as Product
              newProducts.push({
                ...productItem,
                id: productItem.id || `product-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
              })
            }
          })
          
          if (newProducts.length > 0) {
            setAllProducts(prev => getUniqueProducts([...prev, ...newProducts]))
            // Switch to products tab when we get products
            setActiveView('products')
          }
          
          if (newSearchLinks.length > 0) {
            const uniqueLinks = newSearchLinks.map(linkData => ({
              ...linkData,
              links: linkData.links.filter((link, index, self) => 
                index === self.findIndex(l => l.url === link.url)
              )
            }))
            setSearchLinksData(prev => [...prev, ...uniqueLinks])
          }
          
          if (newReasoning.length > 0) {
            setReasoningData(prev => [...prev, ...newReasoning])
            newReasoning.forEach(reasoning => {
              const reasoningMessage: Message = {
                role: 'assistant',
                content: reasoning.formatted_text || reasoning.title,
                timestamp: new Date().toISOString(),
                type: 'reasoning'
              }
              setMessages(prev => [...prev, reasoningMessage])
            })
          }
        }
      } catch (fallbackError) {
        console.error('Error with fallback request:', fallbackError)
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const errorMessage: Message = {
          role: 'assistant',
          content: `Sorry, I couldn't connect to the backend at ${apiUrl}. Please check if the backend is running and the URL is correct. Error: ${fallbackError instanceof Error ? fallbackError.message : 'Unknown error'}`,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } finally {
      setIsLoading(false)
    }
  }

  const uniqueProducts = getUniqueProducts(allProducts)

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex flex-col">
      
      {/* Compact top toggle bar */}
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 shadow-sm px-3 py-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          
          {/* Minimal branding */}
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded flex items-center justify-center">
              <span className="text-white text-xs font-bold">M</span>
            </div>
            <span className="text-sm font-semibold text-slate-800 dark:text-white">MoleAI</span>
          </div>

          {/* Compact toggles */}
          <div className="flex items-center space-x-2">
            
            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="px-2 py-1 text-xs bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 rounded transition-colors flex items-center space-x-1"
              title="Logout"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">Logout</span>
            </button>
            
            {/* Desktop chat toggle */}
            <div className="hidden lg:flex items-center space-x-1">
              <button
                onClick={() => setIsChatExpanded(!isChatExpanded)}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                  isChatExpanded 
                    ? 'bg-indigo-500 text-white' 
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                }`}
              >
                Chat
              </button>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {uniqueProducts.length}
              </span>
            </div>

            {/* Mobile toggle */}
            <div className="flex lg:hidden">
              <div className="flex bg-slate-100 dark:bg-slate-700 rounded p-0.5">
                <button
                  onClick={() => setActiveView('chat')}
                  className={`px-2 py-1 rounded text-xs font-medium transition-all flex items-center space-x-1 ${
                    activeView === 'chat'
                      ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <span>Chat</span>
                  {messages.length > 0 && (
                    <span className="bg-green-500 text-white text-xs px-1 py-0.5 rounded-full min-w-[1rem] h-4 flex items-center justify-center">
                      {messages.filter(m => m.role === 'assistant').length}
                    </span>
                  )}
                </button>
                
                <button
                  onClick={() => setActiveView('products')}
                  className={`px-2 py-1 rounded text-xs font-medium transition-all flex items-center space-x-1 ${
                    activeView === 'products'
                      ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  <span>Products</span>
                  {uniqueProducts.length > 0 && (
                    <span className="bg-indigo-500 text-white text-xs px-1 py-0.5 rounded-full min-w-[1rem] h-4 flex items-center justify-center">
                      {uniqueProducts.length}
                    </span>
                  )}
                </button>
              </div>
            </div>
            
          </div>
        </div>
      </div>

      {/* Main content area - Fixed height container */}
      <div className="flex-1 flex min-h-0 h-full overflow-hidden">
        
        {/* Desktop layout */}
        <div className="hidden lg:flex w-full h-full">
          {/* Chat Panel - Collapsible with independent scrolling */}
          {isChatExpanded && (
            <div className="w-[380px] flex-shrink-0 border-r border-slate-200 dark:border-slate-700 h-full">
              <ChatPanel
                messages={messages}
                input={input}
                isLoading={isLoading}
                searchLinksData={searchLinksData}
                onInputChange={setInput}
                onSendMessage={sendMessage}
              />
            </div>
          )}

          {/* Products Panel with independent scrolling */}
          <div className="flex-1 min-w-0 h-full">
            <ProductPanel
              products={uniqueProducts}
              selectedPriceBucket={selectedPriceBucket}
              selectedBrand={selectedBrand}
              onPriceBucketChange={setSelectedPriceBucket}
              onBrandChange={setSelectedBrand}
              onClearAll={clearAllProducts}
              onRemoveProduct={removeProduct}
              isExpanded={!isChatExpanded}
              onToggleExpand={() => setIsChatExpanded(!isChatExpanded)}
              input={input}
              isLoading={isLoading}
              onInputChange={setInput}
              onSendMessage={sendMessage}
            />
          </div>
        </div>

        {/* Mobile layout with independent scrolling */}
        <div className="flex lg:hidden w-full h-full">
          {activeView === 'products' ? (
            <div className="w-full h-full">
              <ProductPanel
                products={uniqueProducts}
                selectedPriceBucket={selectedPriceBucket}
                selectedBrand={selectedBrand}
                onPriceBucketChange={setSelectedPriceBucket}
                onBrandChange={setSelectedBrand}
                onClearAll={clearAllProducts}
                onRemoveProduct={removeProduct}
                isExpanded={true}
                onToggleExpand={() => {}}
                input={input}
                isLoading={isLoading}
                onInputChange={setInput}
                onSendMessage={sendMessage}
              />
            </div>
          ) : (
            <div className="w-full h-full">
              <ChatPanel
                messages={messages}
                input={input}
                isLoading={isLoading}
                searchLinksData={searchLinksData}
                onInputChange={setInput}
                onSendMessage={sendMessage}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 