import { useState } from 'react'
import { Product, getPriceBucket, sortPriceBuckets } from '../types'

interface FilterPanelProps {
  products: Product[]
  selectedPriceBucket: string
  selectedBrand: string
  onPriceBucketChange: (bucket: string) => void
  onBrandChange: (brand: string) => void
  onClearAll: () => void
}

export default function FilterPanel({ 
  products, 
  selectedPriceBucket, 
  selectedBrand, 
  onPriceBucketChange, 
  onBrandChange,
  onClearAll 
}: FilterPanelProps) {
  const [showFilters, setShowFilters] = useState(false)
  
  // Get unique price buckets and brands from products
  const priceBuckets = Array.from(new Set(products.map(p => getPriceBucket(p))))
  const brands = Array.from(new Set(products.map(p => p.store).filter(Boolean)))

  const hasActiveFilters = selectedPriceBucket || selectedBrand
  const activeFilterCount = (selectedPriceBucket ? 1 : 0) + (selectedBrand ? 1 : 0)

  return (
    <div className="space-y-4">
      {/* Enhanced header with modern styling */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Product count with enhanced styling */}
          <div className="flex items-center space-x-3">
            <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200">
              Products
            </h3>
            <span className="px-3 py-1 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-bold rounded-full shadow-elegant">
              {products.length}
            </span>
          </div>
          
          {/* Enhanced filter toggle button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`group flex items-center space-x-2 px-4 py-2 rounded-xl font-medium text-sm transition-all transform hover:scale-105 shadow-elegant ${
              hasActiveFilters || showFilters
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-elegant-lg'
                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-600'
            }`}
          >
            <svg className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-45' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
            <span>Filters</span>
            {activeFilterCount > 0 && (
              <span className="bg-white/20 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center font-bold">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
        
        {/* Enhanced clear all button */}
        {hasActiveFilters && (
          <button
            onClick={onClearAll}
            className="flex items-center space-x-2 px-4 py-2 bg-red-500/10 dark:bg-red-500/20 text-red-600 dark:text-red-400 hover:bg-red-500/20 dark:hover:bg-red-500/30 rounded-xl font-medium text-sm transition-all transform hover:scale-105 border border-red-200 dark:border-red-800"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>Clear All</span>
          </button>
        )}
      </div>

      {/* Enhanced collapsible filters section */}
      <div className={`transition-all duration-300 overflow-hidden ${
        showFilters ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl border border-slate-200/60 dark:border-slate-600/60 p-6 space-y-6 shadow-elegant">
          
          {/* Enhanced Price Range Filter */}
          {priceBuckets.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"></div>
                <h4 className="font-bold text-slate-800 dark:text-slate-200">Price Range</h4>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {sortPriceBuckets(priceBuckets).map(bucket => (
                  <button
                    key={bucket}
                    onClick={() => onPriceBucketChange(selectedPriceBucket === bucket ? '' : bucket)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all transform hover:scale-105 border ${
                      selectedPriceBucket === bucket
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-transparent shadow-elegant-lg'
                        : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 border-slate-200 dark:border-slate-600'
                    }`}
                  >
                    {bucket}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Enhanced Brand Filter */}
          {brands.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full"></div>
                <h4 className="font-bold text-slate-800 dark:text-slate-200">Brands</h4>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {brands.sort().map(brand => (
                  <button
                    key={brand}
                    onClick={() => onBrandChange(selectedBrand === brand ? '' : brand)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all transform hover:scale-105 border ${
                      selectedBrand === brand
                        ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white border-transparent shadow-elegant-lg'
                        : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 border-slate-200 dark:border-slate-600'
                    }`}
                  >
                    {brand}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* No filters available message */}
          {priceBuckets.length === 0 && brands.length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto bg-gradient-to-br from-slate-400 to-slate-500 rounded-2xl flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <p className="text-slate-600 dark:text-slate-400 font-medium">
                Add some products to enable filtering
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Active filters summary */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Active filters:</span>
          
          {selectedPriceBucket && (
            <span className="inline-flex items-center space-x-1 px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full text-sm font-medium">
              <span>{selectedPriceBucket}</span>
              <button
                onClick={() => onPriceBucketChange('')}
                className="w-4 h-4 rounded-full bg-indigo-200 dark:bg-indigo-700 hover:bg-indigo-300 dark:hover:bg-indigo-600 flex items-center justify-center transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
          
          {selectedBrand && (
            <span className="inline-flex items-center space-x-1 px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full text-sm font-medium">
              <span>{selectedBrand}</span>
              <button
                onClick={() => onBrandChange('')}
                className="w-4 h-4 rounded-full bg-purple-200 dark:bg-purple-700 hover:bg-purple-300 dark:hover:bg-purple-600 flex items-center justify-center transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  )
} 