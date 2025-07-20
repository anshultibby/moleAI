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
  const [isProductViewExpanded, setIsProductViewExpanded] = useState(false)

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

  const toggleProductView = () => {
    setIsProductViewExpanded(prev => !prev)
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

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
      const response = await fetch('http://localhost:8005/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input
        })
      })

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
                // Add reasoning as chat message immediately
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
                // Add search links as chat message immediately
                const searchMessage: Message = {
                  role: 'assistant',
                  content: `Found ${data.data.links?.length || 0} shopping sites for "${data.data.search_query}"`,
                  timestamp: new Date().toISOString(),
                  type: 'search_links'
                }
                setMessages(prev => [...prev, searchMessage])
                
                // Remove duplicates by URL
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
                // Add product immediately
                const product = {
                  ...data.data,
                  id: data.data.id || `product-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
                }
                setAllProducts(prev => [...prev, product])
              }
              
              else if (data.type === 'chat_response') {
                // Add final chat response
                const finalMessage: Message = {
                  role: 'assistant',
                  content: data.message,
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, finalMessage])
              }
              
              else if (data.type === 'error') {
                const errorMessage: Message = {
                  role: 'assistant',
                  content: `Sorry, I encountered an error: ${data.message}`,
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, errorMessage])
              }
              
              else if (data.type === 'start') {
                const startMessage: Message = {
                  role: 'assistant', 
                  content: data.message,
                  timestamp: new Date().toISOString()
                }
                setMessages(prev => [...prev, startMessage])
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
        const response = await axios.post<ChatResponse>('http://localhost:8005/api/chat', {
          message: input
        })

        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.response,
          timestamp: response.data.timestamp
        }

        setMessages(prev => [...prev, assistantMessage])
        
        // Process deals_found as before (fallback)
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
            setAllProducts(prev => [...prev, ...newProducts])
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
        const errorMessage: Message = {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Left Panel - Chat (40% width or hidden when expanded) */}
      {!isProductViewExpanded && (
        <div className="w-[40%] min-w-[380px] flex flex-col shadow-elegant-lg">
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

      {/* Right Panel - Products, Search Links, and Reasoning (60% width or full width when expanded) */}
      <div className={`${isProductViewExpanded ? "w-full" : "w-[60%] min-w-0"} flex flex-col`}>
        
          
        {/* Products Panel */}
        <div className="flex-1 min-h-0">
          <ProductPanel
            products={allProducts}
            selectedPriceBucket={selectedPriceBucket}
            selectedBrand={selectedBrand}
            onPriceBucketChange={setSelectedPriceBucket}
            onBrandChange={setSelectedBrand}
            onClearAll={clearAllProducts}
            onRemoveProduct={removeProduct}
            isExpanded={isProductViewExpanded}
            onToggleExpand={toggleProductView}
          />
        </div>
      </div>
    </div>
  )
} 