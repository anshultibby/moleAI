import { Product } from '../types'
import { useState } from 'react'

interface ProductCardProps {
  product: Product
  onRemove: (id: string) => void
}

export default function ProductCard({ product, onRemove }: ProductCardProps) {
  const [imageLoading, setImageLoading] = useState(true)
  const [imageError, setImageError] = useState(false)

  const handleImageLoad = () => {
    setImageLoading(false)
  }

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setImageLoading(false)
    setImageError(true)
  }

  const getImageUrl = (url?: string) => {
    if (!url) return null
    
    // Handle different store image URL formats
    if (url.includes('zara')) {
      // Ensure proper dimensions for Zara images
      if (!url.includes('w=') && !url.includes('width=')) {
        const separator = url.includes('?') ? '&' : '?'
        return url + separator + 'w=300&h=400&f=auto&q=80'
      }
    }
    
    // Handle H&M images
    if (url.includes('hm.com') || url.includes('h&m')) {
      // H&M images usually work as-is, but we can add quality params if needed
      if (!url.includes('$')) {
        const separator = url.includes('?') ? '&' : '?'
        return url + separator + '$quality$=80&wid=300&hei=400'
      }
    }
    
    // Handle Uniqlo images
    if (url.includes('uniqlo')) {
      // Uniqlo images usually work well as-is
      return url
    }
    
    // Handle ASOS images
    if (url.includes('asos')) {
      // ASOS images usually work well as-is
      return url
    }
    
    // Handle Forever 21 images
    if (url.includes('forever21')) {
      // Forever 21 images usually work well as-is
      return url
    }
    
    // Handle relative URLs
    if (url.startsWith('//')) {
      return 'https:' + url
    }
    
    if (url.startsWith('/')) {
      // Try to infer the store from the product's store field
      const storeName = product.store?.toLowerCase() || ''
      if (storeName.includes('zara')) {
        return 'https://www.zara.com' + url
      } else if (storeName.includes('h&m') || storeName.includes('hm')) {
        return 'https://www2.hm.com' + url
      } else if (storeName.includes('uniqlo')) {
        return 'https://www.uniqlo.com' + url
      } else if (storeName.includes('forever')) {
        return 'https://www.forever21.com' + url
      } else if (storeName.includes('asos')) {
        return 'https://www.asos.com' + url
      } else {
        // Fallback to a generic domain
        return 'https://example.com' + url
      }
    }
    
    return url
  }

  const getProductDisplayName = () => {
    const name = product.product_name || product.name || 'Fashion Item'
    
    // Clean up common issues with product names
    const cleanName = name
      .replace(/^\s*-\s*/, '') // Remove leading dashes
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
    
    // If the name is too generic, try to make it more descriptive
    if (cleanName.toLowerCase() === 'unknown product' || cleanName.length < 3) {
      const category = product.description || product.category || ''
      if (category) {
        return category.charAt(0).toUpperCase() + category.slice(1)
      }
      return 'Fashion Item'
    }
    
    return cleanName
  }

  const getProductCategory = () => {
    const description = product.description || ''
    const name = product.product_name || product.name || ''
    
    // Extract category information from description or name
    const categories = ['dress', 'shirt', 'top', 'blouse', 'jacket', 'coat', 'pants', 'jeans', 'skirt', 'sweater', 'cardigan', 'blazer', 'shoes', 'bag', 'accessory']
    
    const text = (description + ' ' + name).toLowerCase()
    const foundCategory = categories.find(cat => text.includes(cat))
    
    if (foundCategory) {
      return foundCategory.charAt(0).toUpperCase() + foundCategory.slice(1)
    }
    
    return null
  }

  const handleCardClick = () => {
    if (product.product_url) {
      window.open(product.product_url, '_blank', 'noopener,noreferrer')
    }
  }

  const handleRemoveClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onRemove(product.id || '')
  }

  const imageUrl = getImageUrl(product.image_url)
  const displayName = getProductDisplayName()
  const category = getProductCategory()

  return (
    <div 
      className="group bg-white dark:bg-slate-800 rounded-lg shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-200 cursor-pointer min-w-[250px] max-w-[250px] flex-shrink-0 h-[360px] flex flex-col"
      onClick={handleCardClick}
    >
      {/* Remove button */}
      <button
        onClick={handleRemoveClick}
        className="absolute top-2 right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-xs transition-all z-10 opacity-0 group-hover:opacity-100"
        title="Remove"
      >
        ×
      </button>

      {/* Image section - Fixed height */}
      <div className="relative bg-gray-50 dark:bg-slate-700 h-48 flex-shrink-0">
        {imageUrl ? (
          <>
            <img
              src={imageUrl}
              alt={displayName}
              className={`w-full h-full object-cover transition-opacity duration-300 ${imageLoading ? 'opacity-0' : 'opacity-100'}`}
              onError={handleImageError}
              onLoad={handleImageLoad}
              loading="lazy"
            />
            {imageLoading && !imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600 image-loading">
                <div className="text-center">
                  <span className="text-gray-400 text-3xl block mb-2">👗</span>
                  <span className="text-gray-500 text-sm">Loading...</span>
                </div>
              </div>
            )}
            {imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
                <div className="text-center">
                  <span className="text-gray-400 text-3xl block mb-2">👗</span>
                  <span className="text-gray-500 text-sm">Image not available</span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="image-placeholder w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
            <div className="text-center">
              <span className="text-gray-400 text-3xl block mb-2">👗</span>
              <span className="text-gray-500 text-sm">Image not available</span>
            </div>
          </div>
        )}

        {/* Store badge */}
        <div className="absolute top-2 left-2">
          <span className="px-2 py-1 bg-white/90 dark:bg-slate-800/90 text-xs font-medium rounded text-slate-700 dark:text-slate-300">
            {product.store || 'Zara'}
          </span>
        </div>

        {/* Category badge */}
        {category && (
          <div className="absolute bottom-2 left-2">
            <span className="px-2 py-1 bg-indigo-500/90 text-white text-xs font-medium rounded">
              {category}
            </span>
          </div>
        )}
      </div>

      {/* Content section - Flexible height with consistent structure */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div className="flex-1 space-y-2">
          {/* Product name - Fixed height area */}
          <h3 className="font-semibold text-slate-900 dark:text-white text-sm line-clamp-2 leading-tight h-10 flex items-start">
            {displayName}
          </h3>
          
          {/* Description area - Fixed height whether content exists or not */}
          <div className="h-8">
            {product.description && product.description !== displayName && (
              <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                {product.description}
              </p>
            )}
          </div>
        </div>
        
        {/* Price section - Always at bottom */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
            {product.price || 'Price on request'}
          </p>
          
          {/* External link indicator */}
          {product.product_url && (
            <div className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 