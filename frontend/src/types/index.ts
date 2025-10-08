export interface Message {
  role: 'user' | 'assistant'
  content?: string  // Made optional to handle streaming edge cases
  timestamp: string
  type?: 'reasoning' | 'normal' | 'search_links' | 'progress' | 'ephemeral' | 'product_grid' | 'streaming_products' | 'tool_execution'
  turnId?: string  // To associate with thinking panels
  products?: Product[]  // For product grid messages
  productGridTitle?: string  // Title for product grid
  toolExecutions?: ToolExecutionEvent[]  // For tool execution tracking
}

export interface Product {
  // Essential fields (required)
  product_name: string
  store: string
  price: string
  price_value: number
  product_url: string
  image_url: string
  
  // Optional fields
  currency?: string
  sku?: string
  product_id?: string
  color?: string
  size?: string
  description?: string
  
  // Legacy fields for backward compatibility
  variant_id?: string
  type?: string
  id?: string
}

export interface ProductCollection {
  source_name: string  // Meaningful name for the source (e.g., 'zara_dresses')
  source_url: string  // Original URL that was scraped
  pages_scraped: number[]  // List of page numbers scraped
  products: Product[]  // List of extracted products
  
  // Extraction metadata
  extraction_method?: string  // Method used for extraction (e.g., 'shopify_analytics')
  
  // Source metadata
  site_name?: string  // Human-readable site name (e.g., 'Zara')
  category?: string  // Product category if known
  
  // Computed field
  total_products: number  // Total product count
}

export interface ResourceMetadata {
  content_type: 'product_collection'
  product_count: number
  source_url: string
  extraction_method?: string
  site_name?: string
  extra?: Record<string, any>
}

export interface Resource {
  id: string
  product_collection: ProductCollection
  metadata: ResourceMetadata
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

export interface ToolExecutionEvent {
  tool_name: string
  status: 'started' | 'progress' | 'completed' | 'error'
  message?: string
  progress?: {
    current?: number
    total?: number
    url?: string
    query?: string
    num_results?: number
    results_found?: number
    status?: string
    arguments?: Record<string, any>  // Tool call arguments
    [key: string]: any
  }
  result?: string | any[]
  error?: string
  tool_call_id?: string  // Unique ID for this tool call
  timestamp?: string
}

export interface ContentDisplayEvent {
  type: 'content_display'
  content_type: string
  data: any
  title?: string
  metadata?: any
  timestamp: string
}

export interface ContentUpdateEvent {
  type: 'content_update'
  update_type: string
  target_id: string
  data: any
  metadata?: any
  timestamp: string
}

export interface StreamMessage {
  type: 'start' | 'message' | 'product' | 'complete' | 'error' | 'tool_execution' | 'thinking' | 'llm_call' | 'content_display' | 'content_update'
  content?: string
  product?: Product
  error?: string
  tool_name?: string
  status?: 'started' | 'progress' | 'completed' | 'error' | 'continuing'
  message?: string
  progress?: any
  result?: string
  tool_call_id?: string
  final?: boolean
  
  // New content streaming fields
  content_type?: string
  data?: any
  title?: string
  metadata?: any
  update_type?: string
  target_id?: string
}

// Price bucket helper function
export function getPriceBucket(product: Product): string {
  // Use price_value if available (more reliable), otherwise parse price string
  let numericPrice: number
  
  if (product.price_value !== undefined && product.price_value !== null) {
    numericPrice = product.price_value
  } else if (product.price) {
    numericPrice = parseFloat(product.price.replace(/[^0-9.]/g, ''))
  } else {
    return 'Unknown'
  }
  
  if (isNaN(numericPrice)) return 'Unknown'
  if (numericPrice < 20) return 'Under $20'
  if (numericPrice < 50) return '$20-$50'
  if (numericPrice < 100) return '$50-$100'
  if (numericPrice < 200) return '$100-$200'
  return 'Over $200'
}

// Legacy price bucket function for backward compatibility
export function getPriceBucketFromValue(price: string | number | undefined | null): string {
  // Handle undefined, null, or empty values
  if (price === undefined || price === null || price === '') {
    return 'Unknown'
  }
  
  let numericPrice: number
  
  if (typeof price === 'number') {
    numericPrice = price
  } else if (typeof price === 'string') {
    numericPrice = parseFloat(price.replace(/[^0-9.]/g, ''))
  } else {
    return 'Unknown'
  }
  
  if (isNaN(numericPrice)) return 'Unknown'
  if (numericPrice < 20) return 'Under $20'
  if (numericPrice < 50) return '$20-$50'
  if (numericPrice < 100) return '$50-$100'
  if (numericPrice < 200) return '$100-$200'
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