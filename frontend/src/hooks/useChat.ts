import { useState, useEffect } from 'react'
import { Message, Product } from '../types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [ephemeralHistory, setEphemeralHistory] = useState<{[turnId: string]: string[]}>({})
  const [currentTurnId, setCurrentTurnId] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string>('')
  const [hasStartedConversation, setHasStartedConversation] = useState(false)

  // Generate conversationId only on client side to avoid hydration mismatch
  useEffect(() => {
    setConversationId(`conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
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
    const turnId = `turn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
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
                      product_name: data.product.product_name || data.product.name || data.product.title || 'Unknown Product',
                      store: data.product.store || data.product.store_name || 'Unknown Store',
                      price: data.product.price || 'Price not available',
                      image_url: data.product.image_url || '',
                      product_url: data.product.product_url || '',
                      description: data.product.description || '',
                      id: data.product.id || `${(data.product.store || data.product.store_name || 'unknown')}-${(data.product.product_name || data.product.name || data.product.title || 'unknown')}`.toLowerCase().replace(/[^a-z0-9]+/g, '-')
                    }
                    onProductReceived(product)
                  }
                  break
                
                case 'product_removal':
                  if (data.product_id && onProductRemoved) {
                    onProductRemoved(data.product_id)
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
    setEphemeralHistory({})
    setCurrentTurnId(null)
    setHasStartedConversation(false)
    // Generate new conversation ID
    setConversationId(`conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  }

  return {
    messages,
    isLoading,
    ephemeralHistory,
    currentTurnId,
    hasStartedConversation,
    sendMessage,
    resetConversation
  }
} 