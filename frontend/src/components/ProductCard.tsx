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
      className="group bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-200 cursor-pointer w-full flex flex-col relative active:scale-95 sm:active:scale-100 product-card"
      onClick={handleCardClick}
    >
      {/* Image section - Fixed height */}
      <div className="relative bg-gray-50 dark:bg-slate-700 product-card-image flex-shrink-0 h-[200px] sm:h-[250px]">
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

      {/* Content section - Fixed height with flex layout */}
      <div className="p-3 sm:p-3.5 flex flex-col justify-between product-card-content min-h-[100px]">
        {/* Store name */}
        <div className="flex-shrink-0">
          <p className="text-xs text-slate-500 dark:text-slate-400 truncate font-medium">
            {storeName}
          </p>
        </div>
        
        {/* Product name - Takes up available space with consistent height */}
        <div className="flex-1 flex items-start py-1 min-h-[36px] sm:min-h-[40px]">
          <h3 className="font-semibold text-slate-900 dark:text-white text-sm line-clamp-2 leading-tight">
            {displayName}
          </h3>
        </div>
        
        {/* Price - Fixed at bottom */}
        <div className="flex-shrink-0">
          <p className="text-sm font-bold text-indigo-600 dark:text-indigo-400 truncate">
            {product.price || 'Price on request'}
          </p>
        </div>
      </div>
    </div>
  )
} 