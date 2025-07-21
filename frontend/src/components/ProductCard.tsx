import { Product } from '../types'
import { useState } from 'react'
import Image from 'next/image'

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

  // Extract store name from URL
  const getStoreName = () => {
    if (product.store && product.store !== 'Unknown Store' && product.store !== 'unknown') {
      return product.store
    }
    
    // Extract from product URL
    if (product.product_url) {
      try {
        const url = new URL(product.product_url)
        const hostname = url.hostname.toLowerCase()
        
        // Remove common prefixes and suffixes
        let storeName = hostname
          .replace(/^(www\.|shop\.|store\.)/, '')
          .replace(/\.(com|net|org|co\.uk|myshopify\.com)$/, '')
          .replace(/\.myshopify$/, '')
        
        // Capitalize first letter
        storeName = storeName.charAt(0).toUpperCase() + storeName.slice(1)
        
        // Handle special cases
        if (hostname.includes('myshopify.com')) {
          const shopName = hostname.split('.myshopify.com')[0]
          return shopName.charAt(0).toUpperCase() + shopName.slice(1)
        }
        
        return storeName
      } catch (e) {
        return 'Online Store'
      }
    }
    
    return 'Store'
  }

  const getImageUrl = (url?: string) => {
    if (!url || url.includes('example.com')) {
      return null
    }
    
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
      if (!url.includes('$')) {
        const separator = url.includes('?') ? '&' : '?'
        return url + separator + '$quality$=80&wid=300&hei=400'
      }
    }
    
    // Handle relative URLs
    if (url.startsWith('//')) {
      return 'https:' + url
    }
    
    if (url.startsWith('/')) {
      // Try to infer the store from the product's URL
      if (product.product_url) {
        try {
          const baseUrl = new URL(product.product_url).origin
          return baseUrl + url
        } catch (e) {
          return null
        }
      }
      return null
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
    // Always link to the actual product, never to example.com
    if (product.product_url && !product.product_url.includes('example.com')) {
      window.open(product.product_url, '_blank', 'noopener,noreferrer')
    }
  }

  const handleRemoveClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onRemove(product.id || '')
  }

  const imageUrl = getImageUrl(product.image_url)
  const displayName = getProductDisplayName()
  const storeName = getStoreName()

  return (
    <div 
      className="group bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-200 cursor-pointer w-full flex flex-col relative active:scale-95 sm:active:scale-100"
      onClick={handleCardClick}
    >
      {/* Image section */}
      <div className="relative bg-gray-50 dark:bg-slate-700 h-32 sm:h-40 flex-shrink-0">
        {imageUrl ? (
          <>
            <Image
              src={imageUrl}
              alt={displayName}
              fill
              className={`object-cover transition-opacity duration-300 ${imageLoading ? 'opacity-0' : 'opacity-100'}`}
              onError={handleImageError}
              onLoad={handleImageLoad}
            />
            {imageLoading && !imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
                <div className="text-center">
                  <span className="text-gray-400 text-xl sm:text-2xl block">👗</span>
                </div>
              </div>
            )}
            {imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
                <div className="text-center">
                  <span className="text-gray-400 text-xl sm:text-2xl block">👗</span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
            <div className="text-center">
              <span className="text-gray-400 text-xl sm:text-2xl block">👗</span>
            </div>
          </div>
        )}
      </div>

      {/* Content section with guaranteed space */}
      <div className="p-3 sm:p-4 flex flex-col justify-between min-h-[80px] sm:min-h-[90px]">
        {/* Store name */}
        <div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 truncate font-medium">
            {storeName}
          </p>
        </div>
        
        {/* Product name */}
        <div className="flex-1 min-h-0 py-1">
          <h3 className="font-semibold text-slate-900 dark:text-white text-sm sm:text-base line-clamp-2 leading-tight">
            {displayName}
          </h3>
        </div>
        
        {/* Price */}
        <div className="mt-1">
          <p className="text-sm sm:text-base font-bold text-indigo-600 dark:text-indigo-400 truncate">
            {product.price || 'Price on request'}
          </p>
        </div>
      </div>
    </div>
  )
} 