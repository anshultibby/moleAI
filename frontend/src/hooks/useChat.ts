import { useState, useEffect } from 'react'
import { Message, Product, ToolExecutionEvent } from '../types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [ephemeralHistory, setEphemeralHistory] = useState<{[turnId: string]: string[]}>({})
  const [currentTurnId, setCurrentTurnId] = useState<string | null>(null)
  const [activeToolExecutions, setActiveToolExecutions] = useState<Record<string, ToolExecutionEvent[]>>({})
  const [currentToolExecutions, setCurrentToolExecutions] = useState<Record<string, ToolExecutionEvent>>({})
  const [conversationId, setConversationId] = useState<string>('')
  const [hasStartedConversation, setHasStartedConversation] = useState(false)

  // Generate conversationId only on client side to avoid hydration mismatch
  useEffect(() => {
    setConversationId(`conv_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`)
  }, [])

  const sendMessage = async (
    input: string,
    onProductReceived: (product: Product) => void,
    onProductRemoved?: (productId: string) => void
  ) => {
    if (!input.trim() || isLoading || !conversationId) return

    // Mark conversation as started
    setHasStartedConversation(true)

    // Create a unique turn ID for this conversation turn
    const turnId = `turn_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
    setCurrentTurnId(turnId)

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
      turnId: turnId
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          conversation_id: conversationId
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
              
              switch (data.type) {
                case 'message':
                  if (data.content) {
                    const message: Message = {
                      role: 'assistant',
                      content: data.content,
                      timestamp: new Date().toISOString(),
                      turnId: turnId
                    }
                    setMessages(prev => [...prev, message])
                    setCurrentTurnId(null)
                  }
                  break
                
                case 'thinking':
                  // Handle thinking content (same as ephemeral)
                  if (data.content && data.content.trim().length > 0) {
                    setEphemeralHistory(prev => ({
                      ...prev,
                      [turnId]: [...(prev[turnId] || []), data.content]
                    }))
                  }
                  break
                
                case 'llm_call':
                  // Handle LLM call status - could show loading indicators
                  console.log('LLM Call:', data.status, data.message)
                  break
                
                case 'product_grid':
                  if (data.products) {
                    const message: Message = {
                      role: 'assistant',
                      content: data.content || '',
                      timestamp: new Date().toISOString(),
                      type: 'product_grid',
                      products: data.products,
                      productGridTitle: data.productGridTitle,
                      turnId: turnId
                    }
                    setMessages(prev => [...prev, message])
                  }
                  break
                
                case 'ephemeral':
                  if (data.content && data.content.trim().length > 0) {
                    setEphemeralHistory(prev => ({
                      ...prev,
                      [turnId]: [...(prev[turnId] || []), data.content]
                    }))
                  }
                  break
                
                case 'product':
                  if (data.product) {
                    const product: Product = {
                      ...data.product,
                      product_name: data.product.product_name,
                      store: data.product.store,
                      price: data.product.price,
                      image_url: data.product.image_url || '',
                      product_url: data.product.product_url || '',
                      description: data.product.description || '',
                      id: data.product.id || `${data.product.store}-${data.product.product_name}`.toLowerCase().replace(/[^a-z0-9]+/g, '-')
                    }
                    
                    // Add product to streaming products message or create new one
                    setMessages(prev => {
                      const lastMessage = prev[prev.length - 1]
                      
                      // If the last message is a streaming_products message from the same turn, add to it
                      if (lastMessage && 
                          lastMessage.type === 'streaming_products' && 
                          lastMessage.turnId === turnId) {
                        const updatedMessage = {
                          ...lastMessage,
                          products: [...(lastMessage.products || []), product]
                        }
                        return [...prev.slice(0, -1), updatedMessage]
                      } else {
                        // Create new streaming products message
                        const streamingMessage: Message = {
                          role: 'assistant',
                          content: '',
                          timestamp: new Date().toISOString(),
                          type: 'streaming_products',
                          products: [product],
                          productGridTitle: 'Products Found',
                          turnId: turnId
                        }
                        return [...prev, streamingMessage]
                      }
                    })
                    
                    // Also call the callback for the separate product list
                    onProductReceived(product)
                  }
                  break
                
                case 'product_removal':
                  if (data.product_id && onProductRemoved) {
                    onProductRemoved(data.product_id)
                  }
                  break
                
                case 'content_display':
                  if (data.content_type && data.data) {
                    // Handle different content types
                    if (data.content_type === 'products') {
                      // Handle product streaming with chunking
                      const products = data.data.products || []
                      const isFirstChunk = data.data.chunk_index === 0
                      const isFinalChunk = data.data.is_final_chunk
                      
                      // Add products to streaming products message or create new one
                      setMessages(prev => {
                        const lastMessage = prev[prev.length - 1]
                        
                        // If this is the first chunk or no existing streaming message, create new one
                        if (isFirstChunk || !lastMessage || 
                            lastMessage.type !== 'streaming_products' || 
                            lastMessage.turnId !== turnId) {
                          const streamingMessage: Message = {
                            role: 'assistant',
                            content: '',
                            timestamp: new Date().toISOString(),
                            type: 'streaming_products',
                            products: products,
                            productGridTitle: data.title || 'Products Found',
                            turnId: turnId
                          }
                          return [...prev, streamingMessage]
                        } else {
                          // Append to existing streaming message
                          const updatedMessage = {
                            ...lastMessage,
                            products: [...(lastMessage.products || []), ...products]
                          }
                          return [...prev.slice(0, -1), updatedMessage]
                        }
                      })
                      
                      // Also call the callback for each product
                      products.forEach((product: Product) => {
                        const processedProduct: Product = {
                          ...product,
                          product_name: product.product_name,
                          store: product.store,
                          price: product.price,
                          image_url: product.image_url || '',
                          product_url: product.product_url || '',
                          description: product.description || '',
                          id: product.id || `${(product.store || 'unknown')}-${(product.product_name || 'unknown')}`.toLowerCase().replace(/[^a-z0-9]+/g, '-')
                        }
                        onProductReceived(processedProduct)
                      })
                    } else {
                      // Handle other content types (future expansion)
                      console.log('Received content display:', data.content_type, data)
                    }
                  }
                  break
                
                case 'content_update':
                  if (data.update_type && data.target_id) {
                    // Handle content updates (future expansion)
                    console.log('Received content update:', data.update_type, data.target_id, data)
                  }
                  break
                
                case 'tool_execution':
                  if (data.tool_name && data.status) {
                    const toolEvent: ToolExecutionEvent = {
                      tool_name: data.tool_name,
                      status: data.status,
                      message: data.message,
                      progress: data.progress,
                      result: data.result,
                      error: data.error
                    }
                    
                    // Create unique key for each tool execution
                    // For search tools, include query to make each search unique
                    let toolKey = data.tool_name
                    if (data.tool_name === 'search_web_tool' && data.progress?.query) {
                      toolKey = `${data.tool_name}_${data.progress.query.replace(/\s+/g, '_').toLowerCase()}`
                    } else if (data.tool_name === 'search_web_tool') {
                      // Fallback: use timestamp if no query available
                      toolKey = `${data.tool_name}_${Date.now()}`
                    }
                    
                    // Update current tool executions (for side panel)
                    setCurrentToolExecutions(prev => ({
                      ...prev,
                      [toolKey]: toolEvent
                    }))
                    
                    // Also keep the old format for backward compatibility
                    setActiveToolExecutions(prev => {
                      const existing = prev[turnId] || []
                      const existingIndex = existing.findIndex(e => e.tool_name === data.tool_name)
                      
                      if (existingIndex >= 0) {
                        // Update existing tool execution
                        const updated = [...existing]
                        updated[existingIndex] = toolEvent
                        return {
                          ...prev,
                          [turnId]: updated
                        }
                      } else {
                        // Add new tool execution
                        return {
                          ...prev,
                          [turnId]: [...existing, toolEvent]
                        }
                      }
                    })
                  }
                  break
                
                case 'error':
                  const errorMessage: Message = {
                    role: 'assistant',
                    content: `Sorry, I encountered an error: ${data.error}`,
                    timestamp: new Date().toISOString()
                  }
                  setMessages(prev => [...prev, errorMessage])
                  break
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e)
            }
          }
        }
      }

    } catch (error) {
      console.error('Error with streaming:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const resetConversation = () => {
    setMessages([])
    setIsLoading(false)
    setEphemeralHistory({})
    setCurrentTurnId(null)
    setActiveToolExecutions({})
    setCurrentToolExecutions({})
    setHasStartedConversation(false)
    // Generate new conversation ID
    setConversationId(`conv_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`)
  }

  return {
    messages,
    isLoading,
    ephemeralHistory,
    currentTurnId,
    activeToolExecutions,
    currentToolExecutions,
    hasStartedConversation,
    sendMessage,
    resetConversation
  }
} 