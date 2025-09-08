export interface Message {
  role: 'user' | 'assistant'
  content?: string  // Made optional to handle streaming edge cases
  timestamp: string
  type?: 'reasoning' | 'normal' | 'search_links' | 'progress' | 'ephemeral' | 'product_grid' | 'streaming_products'
  turnId?: string  // To associate with thinking panels
  products?: Product[]  // For product grid messages
  productGridTitle?: string  // Title for product grid
}

export interface Product {
  product_name: string
  name?: string  // Alternative name field
  price: string
  currency?: string  // Currency code (USD, EUR, GBP, etc.)
  store: string
  store_name?: string  // Alternative store field
  image_url?: string
  product_url?: string
  description?: string
  category?: string  // Product category
  type?: string
  id?: string
}

export interface SearchLink {
  title: string
  url: string
  description: string
  domain: string
  score: number
  highlights: string[]
}

export interface SearchLinksData {
  type: 'search_links'
  search_query: string
  total_results: number
  links: SearchLink[]
  timestamp: string
  id?: string
}

export interface ChatResponse {
  response: string
  timestamp: string
  deals_found?: (Product | SearchLinksData)[]
}

export interface StreamMessage {
  type: 'start' | 'message' | 'product' | 'complete' | 'error'
  content?: string
  product?: Product
  error?: string
}

// Price bucket helper function
export function getPriceBucket(priceStr: string): string {
  // Handle undefined, null, or empty strings
  if (!priceStr || typeof priceStr !== 'string') {
    return 'Unknown'
  }
  
  const price = parseFloat(priceStr.replace(/[^0-9.]/g, ''))
  if (isNaN(price)) return 'Unknown'
  if (price < 20) return 'Under $20'
  if (price < 50) return '$20-$50'
  if (price < 100) return '$50-$100'
  if (price < 200) return '$100-$200'
  return 'Over $200'
}

// Price bucket sorting helper function
export function sortPriceBuckets(buckets: string[]): string[] {
  const bucketOrder = ['Under $20', '$20-$50', '$50-$100', '$100-$200', 'Over $200', 'Unknown']
  
  return buckets.sort((a, b) => {
    const indexA = bucketOrder.indexOf(a)
    const indexB = bucketOrder.indexOf(b)
    
    // If bucket not found in order, put it at the end
    const orderA = indexA === -1 ? bucketOrder.length : indexA
    const orderB = indexB === -1 ? bucketOrder.length : indexB
    
    return orderA - orderB
  })
} 