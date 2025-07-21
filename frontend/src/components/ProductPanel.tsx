import FilterPanel from './FilterPanel'
import ProductCard from './ProductCard'
import { Product, getPriceBucket, sortPriceBuckets } from '../types'
import { useRef, useEffect } from 'react'

interface ProductPanelProps {
  products: Product[]
  selectedPriceBucket: string
  selectedBrand: string
  onPriceBucketChange: (bucket: string) => void
  onBrandChange: (brand: string) => void
  onClearAll: () => void
  onRemoveProduct: (id: string) => void
  isExpanded: boolean
  onToggleExpand: () => void
  // New props for text input functionality
  input?: string
  isLoading?: boolean
  onInputChange?: (value: string) => void
  onSendMessage?: () => void
}

export default function ProductPanel({
  products,
  selectedPriceBucket,
  selectedBrand,
  onPriceBucketChange,
  onBrandChange,
  onClearAll,
  onRemoveProduct,
  isExpanded,
  onToggleExpand,
  input = '',
  isLoading = false,
  onInputChange,
  onSendMessage
}: ProductPanelProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Filter products based on selected filters
  const filteredProducts = products.filter(product => {
    if (selectedPriceBucket && getPriceBucket(product.price) !== selectedPriceBucket) {
      return false
    }
    if (selectedBrand && product.store !== selectedBrand) {
      return false
    }
    return true
  })

  // Limit products per store to maximum 6 items
  const limitProductsPerStore = (products: Product[], maxPerStore: number = 6): Product[] => {
    const storeGroups: { [store: string]: Product[] } = {}
    
    // Group products by store
    products.forEach(product => {
      const storeName = product.store || 'Unknown Store'
      if (!storeGroups[storeName]) {
        storeGroups[storeName] = []
      }
      storeGroups[storeName].push(product)
    })
    
    // Limit each store to maxPerStore products and flatten
    const limitedProducts: Product[] = []
    Object.values(storeGroups).forEach(storeProducts => {
      limitedProducts.push(...storeProducts.slice(0, maxPerStore))
    })
    
    return limitedProducts
  }

  // Apply store limit to filtered products
  const storeLimitedProducts = limitProductsPerStore(filteredProducts, 6)

  // Helper function to extract numeric price value
  const getPriceValue = (priceStr: string): number => {
    if (!priceStr || typeof priceStr !== 'string') {
      return 0
    }
    // Extract numbers from price string (handles formats like "$29.99", "€25,95", "Price not available")
    const match = priceStr.match(/[\d.,]+/)
    if (match) {
      // Replace comma with dot for parsing (handles European formats)
      const numStr = match[0].replace(',', '.')
      const num = parseFloat(numStr)
      return isNaN(num) ? 0 : num
    }
    return 0
  }

  // Sort all products by price (lowest to highest)
  const sortedProducts = [...storeLimitedProducts].sort((a, b) => {
    const priceA = getPriceValue(a.price)
    const priceB = getPriceValue(b.price)
    return priceA - priceB
  })

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const scrollHeight = textareaRef.current.scrollHeight
      const maxHeight = window.innerWidth >= 640 ? 120 : 80 // Different max heights for mobile vs desktop
      textareaRef.current.style.height = Math.min(scrollHeight, maxHeight) + 'px'
    }
  }, [input])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (onSendMessage) {
        onSendMessage()
      }
    }
    // Allow Shift+Enter for new lines in textarea
  }

  return (
    <div className="h-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm flex flex-col">

      {/* Enhanced Products Display with independent scrolling */}
      <div className="flex-1 overflow-y-auto scrollbar-thin mobile-scroll bg-gradient-to-b from-slate-50/30 to-white dark:from-slate-800/30 dark:to-slate-900 min-h-0">
        {products.length === 0 ? (
          <div className="h-full flex items-center justify-center p-8">
            <div className="text-center max-w-md w-full">
              {/* Enhanced empty state */}
              <div className="mb-8 relative">
                <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-lg">
                  <span className="text-3xl sm:text-4xl">🛍️</span>
                </div>
                <div className="absolute -top-2 -right-2 w-6 h-6 sm:w-8 sm:h-8 bg-yellow-400 rounded-full animate-pulse flex items-center justify-center">
                  <span className="text-xs sm:text-sm">✨</span>
                </div>
              </div>
              
              <h3 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-slate-200 mb-3">
                Welcome to MoleAI
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-lg leading-relaxed px-4 mb-6">
                Ask me to find amazing deals that match your style preferences
              </p>
              
              {/* Text input box */}
              {onInputChange && onSendMessage ? (
                <div className="w-full mb-6">
                  <div className="relative">
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={(e) => onInputChange(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask me to find clothing deals..."
                      rows={1}
                      className="w-full px-3 sm:px-4 py-3 sm:py-4 pr-12 sm:pr-14 pb-12 sm:pb-14 bg-white dark:bg-slate-700 border-2 border-slate-200 dark:border-slate-600 rounded-lg sm:rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:text-white text-sm sm:text-base font-medium placeholder-slate-500 dark:placeholder-slate-400 transition-all resize-none overflow-y-auto scrollbar-thin min-h-[44px] sm:min-h-[52px] shadow-lg"
                      disabled={isLoading}
                    />
                    
                    {/* Clear button */}
                    {input && (
                      <button
                        onClick={() => onInputChange('')}
                        className="absolute right-2 sm:right-3 top-2 sm:top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                      >
                        <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                    
                    {/* Send button - positioned inside textarea at bottom right */}
                    <button
                      onClick={onSendMessage}
                      disabled={!input.trim() || isLoading}
                      className="absolute bottom-2 right-2 sm:bottom-3 sm:right-3 px-3 sm:px-4 py-2 sm:py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white rounded-lg font-medium text-sm shadow-lg disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 disabled:transform-none flex items-center justify-center space-x-1"
                    >
                      {isLoading ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      ) : (
                        <>
                          <span className="hidden sm:inline text-xs">Send</span>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                          </svg>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : null}
              
              <div className="p-4 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl border border-slate-200/60 dark:border-slate-600/60">
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 font-medium mb-3">
                  ✨ Try asking me:
                </p>
                <div className="space-y-2 text-left">
                  {[
                    "Find me elegant black dresses under $100",
                    "Show me trendy winter coats",
                    "I need a formal outfit for a wedding"
                  ].map((suggestion, index) => (
                    <div 
                      key={index}
                      className="flex items-center space-x-2 p-2 bg-slate-50/50 dark:bg-slate-700/50 rounded-lg hover:bg-slate-100/50 dark:hover:bg-slate-600/50 transition-colors cursor-pointer"
                      onClick={() => onInputChange && onInputChange(suggestion)}
                    >
                      <div className="w-1.5 h-1.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
                      <span className="text-slate-700 dark:text-slate-300 text-xs font-medium">
                        &quot;{suggestion}&quot;
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : storeLimitedProducts.length === 0 ? (
          <div className="h-full flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              {/* Enhanced no results state */}
              <div className="mb-6">
                <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-2xl sm:text-3xl">🔍</span>
                </div>
              </div>
              
              <h3 className="text-lg sm:text-xl font-bold text-slate-800 dark:text-slate-200 mb-3">
                No matches found
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6 text-sm sm:text-base px-4">
                Try adjusting your filters to see more products
              </p>
              
              <button
                onClick={onClearAll}
                className="px-4 sm:px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl font-medium text-sm shadow-lg transition-all transform hover:scale-105"
              >
                Clear All Filters
              </button>
            </div>
          </div>
        ) : (
          <div className="p-4 sm:p-6">
            {/* Responsive product grid - vertical scrolling on all devices */}
            <div className="relative">
              {/* Unified responsive grid for all screen sizes */}
              <div className={`grid gap-4 sm:gap-6 ${
                isExpanded 
                  ? 'grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6'
                  : 'grid-cols-2 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5'
              }`}>
                {sortedProducts.map(product => (
                  <div key={product.id} className="transform transition-all duration-300 hover:scale-105">
                    <ProductCard
                      product={product}
                      onRemove={onRemoveProduct}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 