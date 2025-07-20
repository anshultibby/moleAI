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

  // Group products by price bucket
  const groupedProducts = filteredProducts.reduce((groups, product) => {
    const bucket = getPriceBucket(product.price)
    if (!groups[bucket]) groups[bucket] = []
    groups[bucket].push(product)
    return groups
  }, {} as Record<string, Product[]>)

  return (
    <div className="flex-1 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm flex flex-col">
      {/* Enhanced Header with gradient and better toggle */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 border-b border-slate-200 dark:border-slate-600 shadow-elegant">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex-1">
            <FilterPanel
              products={products}
              selectedPriceBucket={selectedPriceBucket}
              selectedBrand={selectedBrand}
              onPriceBucketChange={onPriceBucketChange}
              onBrandChange={onBrandChange}
              onClearAll={onClearAll}
            />
          </div>
          
          {/* Enhanced Toggle Button */}
          <div className="ml-4">
            <button
              onClick={onToggleExpand}
              className="group p-3 rounded-xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-elegant transition-all hover:shadow-elegant-lg transform hover:scale-105"
              title={isExpanded ? "Show chat panel" : "Expand product view"}
            >
              <svg 
                className={`w-5 h-5 text-slate-600 dark:text-slate-400 transition-transform duration-200 ${
                  isExpanded ? 'rotate-180' : ''
                }`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d={isExpanded ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} 
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Products Display */}
      <div className="flex-1 overflow-y-auto scrollbar-thin bg-gradient-to-b from-slate-50/30 to-white dark:from-slate-800/30 dark:to-slate-900">
        {products.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              {/* Enhanced empty state */}
              <div className="mb-8 relative">
                <div className="w-24 h-24 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-elegant-lg">
                  <span className="text-4xl">🛍️</span>
                </div>
                <div className="absolute -top-3 -right-3 w-8 h-8 bg-yellow-400 rounded-full animate-pulse-glow flex items-center justify-center">
                  <span className="text-sm">✨</span>
                </div>
              </div>
              
              <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-200 mb-3 gradient-text">
                No products yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 text-lg leading-relaxed">
                Start chatting and I'll find amazing deals that match your style preferences
              </p>
              
              <div className="mt-8 p-4 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl border border-slate-200/60 dark:border-slate-600/60">
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
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
                <div className="w-20 h-20 mx-auto bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-elegant">
                  <span className="text-3xl">🔍</span>
                </div>
              </div>
              
              <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-3">
                No matches found
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Try adjusting your filters to see more products
              </p>
              
              <button
                onClick={onClearAll}
                className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl font-medium text-sm shadow-elegant transition-all transform hover:scale-105"
              >
                Clear All Filters
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-8">
            {Object.entries(groupedProducts)
              .sort(([a], [b]) => {
                const sortedBuckets = sortPriceBuckets([a, b])
                return sortedBuckets.indexOf(a) - sortedBuckets.indexOf(b)
              })
              .map(([bucket, products]) => (
                <div key={bucket} className="space-y-4">
                  {/* Enhanced category header */}
                  <div className="flex items-center space-x-4">
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                    <div className="px-4 py-2 bg-white dark:bg-slate-800 rounded-full border border-slate-200 dark:border-slate-600 shadow-elegant">
                      <span className="text-sm font-bold text-slate-700 dark:text-slate-300 tracking-wide">
                        {bucket}
                      </span>
                      <span className="ml-2 text-xs bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 px-2 py-1 rounded-full font-medium">
                        {products.length} {products.length === 1 ? 'item' : 'items'}
                      </span>
                    </div>
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-600 to-transparent"></div>
                  </div>
                  
                  {/* Horizontal scrolling product carousel */}
                  <div className="relative">
                    <div className="flex space-x-4 overflow-x-auto horizontal-scroll pb-4 px-1">
                      {products.map(product => (
                        <div key={product.id} className="product-card-hover transition-all duration-300">
                          <ProductCard
                            product={product}
                            onRemove={onRemoveProduct}
                          />
                        </div>
                      ))}
                    </div>
                    
                    {/* Scroll hint for large collections */}
                    {products.length > 3 && (
                      <div className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-gradient-to-l from-slate-50/90 to-transparent dark:from-slate-800/90 w-8 h-full flex items-center justify-end pr-2 pointer-events-none">
                        <svg className="w-4 h-4 text-slate-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  )
} 