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
  const [imageFitMode, setImageFitMode] = useState<'cover' | 'contain'>('contain')

  const handleImageLoad = () => {
    setImageLoading(false)
  }

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setImageLoading(false)
    setImageError(true)
  }

  // Extract store name from URL
  const getStoreName = () => {
    // Try different possible store field names
    const store = product.store || product.store_name || ''
    if (store && store !== 'Unknown Store' && store !== 'unknown' && store.trim()) {
      return store
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
        return url + separator + 'w=400&h=500&f=auto&q=80'
      }
    }
    
    // Handle H&M images
    if (url.includes('hm.com') || url.includes('h&m')) {
      if (!url.includes('$')) {
        const separator = url.includes('?') ? '&' : '?'
        return url + separator + '$quality$=80&wid=400&hei=500'
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
    
    // Validate URL format
    try {
      new URL(url)
      return url
    } catch (e) {
      console.warn('Invalid image URL:', url)
      return null
    }
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



  // Handle image fit mode toggle on double-click
  const handleImageDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setImageFitMode(prev => prev === 'contain' ? 'cover' : 'contain')
  }

  const imageUrl = getImageUrl(product.image_url)
  const displayName = getProductDisplayName()
  const storeName = getStoreName()

  return (
    <div 
      className="group bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-200 cursor-pointer w-full flex flex-col h-[330px] relative hover:scale-[1.02] active:scale-95"
      onClick={handleCardClick}
    >
      {/* Image section - Fixed height */}
      <div className="relative bg-gray-50 dark:bg-slate-700 flex-shrink-0 h-[180px]">
        {imageUrl ? (
          <>
            <Image
              src={imageUrl}
              alt={displayName}
              fill
              className={`product-image transition-all duration-300 ${
                imageLoading ? 'opacity-0' : 'opacity-100'
              } ${
                imageFitMode === 'contain' 
                  ? 'object-contain' 
                  : 'object-cover'
              }`}
              onError={handleImageError}
              onLoad={handleImageLoad}
              onDoubleClick={handleImageDoubleClick}
              unoptimized={true}
              priority={false}
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
            {imageLoading && !imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-gray-300 border-t-indigo-500 rounded-full animate-spin mb-2"></div>
                  <span className="text-gray-400 text-xs">Loading...</span>
                </div>
              </div>
            )}
            {imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
                <div className="text-center">
                  <span className="text-gray-400 text-xl sm:text-2xl block">👗</span>
                  <span className="text-gray-400 text-xs mt-1">Image unavailable</span>
                </div>
              </div>
            )}

          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-slate-600">
            <div className="text-center">
              <span className="text-gray-400 text-xl sm:text-2xl block">👗</span>
              <span className="text-gray-400 text-xs mt-1">No image</span>
            </div>
          </div>
        )}
      </div>

      {/* Content section - Clean layout */}
      <div className="p-4 flex flex-col h-[150px] bg-white dark:bg-slate-800">
        {/* Product name - Most important, at top */}
        <div className="mb-3 h-[44px] flex items-start">
          <h3 className="font-semibold text-slate-900 dark:text-white text-sm leading-tight line-clamp-2">
            {displayName}
          </h3>
        </div>
        
        {/* Price - Second priority */}
        <div className="mb-3">
          <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
            {product.price.startsWith('$') ? product.price : `$${product.price}`}
          </p>
        </div>
        
        {/* Store name - Can get cut off, least priority */}
        <div className="mt-auto">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wide truncate">
            {storeName}
          </p>
        </div>
      </div>
    </div>
  )
} 