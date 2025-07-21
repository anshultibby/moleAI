import FilterPanel from './FilterPanel'
import ProductCard from './ProductCard'
import { Product, getPriceBucket, sortPriceBuckets } from '../types'

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
  onToggleExpand
}: ProductPanelProps) {
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
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const priceA = getPriceValue(a.price)
    const priceB = getPriceValue(b.price)
    return priceA - priceB
  })

  return (
    <div className="flex-1 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm flex flex-col">


      {/* Enhanced Products Display */}
      <div className="flex-1 overflow-y-auto scrollbar-thin bg-gradient-to-b from-slate-50/30 to-white dark:from-slate-800/30 dark:to-slate-900">
        {products.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
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
                No products yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-lg leading-relaxed px-4">
                Start chatting and I'll find amazing deals that match your style preferences
              </p>
              
              <div className="mt-6 sm:mt-8 p-4 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl border border-slate-200/60 dark:border-slate-600/60">
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 font-medium">
                  💡 Products will appear here automatically as you chat
                </p>
              </div>
            </div>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-8">
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
            {/* Simple product grid/carousel - no buckets */}
            <div className="relative">
              {/* Mobile: Horizontal scroll */}
              <div className="sm:hidden">
                <div className="flex space-x-3 overflow-x-auto pb-4 px-1 snap-x snap-mandatory mobile-scroll-hidden">
                  {sortedProducts.map(product => (
                    <div key={product.id} className="flex-shrink-0 snap-start">
                      <ProductCard
                        product={product}
                        onRemove={onRemoveProduct}
                      />
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Desktop: Responsive grid */}
              <div className="hidden sm:grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
                {sortedProducts.map(product => (
                  <div key={product.id} className="transform transition-all duration-300 hover:scale-105">
                    <ProductCard
                      product={product}
                      onRemove={onRemoveProduct}
                    />
                  </div>
                ))}
              </div>
              
              {/* Scroll hint for mobile large collections */}
              {sortedProducts.length > 2 && (
                <div className="sm:hidden absolute right-0 top-1/2 transform -translate-y-1/2 bg-gradient-to-l from-slate-50/90 to-transparent dark:from-slate-800/90 w-8 h-full flex items-center justify-end pr-2 pointer-events-none">
                  <svg className="w-3 h-3 text-slate-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 