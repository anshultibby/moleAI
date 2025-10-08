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
    console.warn('Image failed to load:', {
      src: e.currentTarget.src,
      product_name: product.product_name,
      original_url: product.image_url
    })
  }

  // Extract store name from URL
  const getStoreName = () => {
    // Try different possible store field names
    const store = product.store || ''
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
    
    // Ensure HTTPS for all URLs to avoid mixed content issues
    if (url.startsWith('http:')) {
      url = url.replace('http:', 'https:')
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
    const name = product.product_name || 'Fashion Item'
    
    // Clean up common issues with product names
    const cleanName = name
      .replace(/^\s*-\s*/, '') // Remove leading dashes
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
    
    // If the name is too generic, try to make it more descriptive
    if (cleanName.toLowerCase() === 'unknown product' || cleanName.length < 3) {
      const category = product.description || ''
      if (category) {
        return category.charAt(0).toUpperCase() + category.slice(1)
      }
      return 'Fashion Item'
    }
    
    return cleanName
  }

  const getProductCategory = () => {
    const description = product.description || ''
    const name = product.product_name || ''
    
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
      className="group bg-white dark:bg-slate-800/95 rounded-2xl shadow-md hover:shadow-2xl border border-slate-200/60 dark:border-slate-700/60 overflow-hidden transition-all duration-300 ease-out cursor-pointer w-full flex flex-col h-[320px] relative hover:scale-[1.03] hover:-translate-y-2 active:scale-[0.98] hover:border-indigo-400/50 dark:hover:border-indigo-500/50 backdrop-blur-sm"
      onClick={handleCardClick}
      style={{
        transformOrigin: 'center center'
      }}
    >
      {/* Image section - Optimized height */}
      <div className="relative bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-700 dark:to-slate-800 flex-shrink-0 h-[200px] overflow-hidden">
        {imageUrl ? (
          <>
            <Image
              src={imageUrl}
              alt={displayName}
              fill
              className={`product-image transition-all duration-500 ease-out ${
                imageLoading ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
              } ${
                imageFitMode === 'contain' 
                  ? 'object-contain p-2' 
                  : 'object-cover'
              } group-hover:scale-105`}
              onError={handleImageError}
              onLoad={handleImageLoad}
              onDoubleClick={handleImageDoubleClick}
              unoptimized={true}
              priority={false}
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
            {imageLoading && !imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-700 dark:to-slate-600">
                <div className="text-center">
                  <div className="w-10 h-10 border-3 border-slate-200 border-t-indigo-500 dark:border-slate-600 dark:border-t-indigo-400 rounded-full animate-spin mb-2"></div>
                  <span className="text-slate-400 dark:text-slate-500 text-xs font-medium">Loading...</span>
                </div>
              </div>
            )}
            {imageError && (
              <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-700 dark:to-slate-600">
                <div className="text-center p-4">
                  <span className="text-4xl block mb-2 opacity-40">👗</span>
                  <span className="text-slate-400 dark:text-slate-500 text-xs font-medium">Image unavailable</span>
                </div>
              </div>
            )}

          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-700 dark:to-slate-600">
            <div className="text-center p-4">
              <span className="text-4xl block mb-2 opacity-40">👗</span>
              <span className="text-slate-400 dark:text-slate-500 text-xs font-medium">No image</span>
            </div>
          </div>
        )}
      </div>

      {/* Content section - Enhanced layout */}
      <div className="p-4 flex flex-col h-[120px] bg-gradient-to-b from-white to-slate-50/50 dark:from-slate-800/95 dark:to-slate-800">
        {/* Product name - Enhanced */}
        <div className="mb-2.5 h-[40px] flex items-start">
          <h3 className="font-semibold text-slate-900 dark:text-white text-base leading-snug line-clamp-2 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors duration-200">
            {displayName}
          </h3>
        </div>
        
        {/* Price section - More prominent */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent">
            {(() => {
              // If price already includes currency symbol, use it as is
              if (product.price && (product.price.includes('$') || product.price.includes('€') || product.price.includes('£') || product.price.includes('¥') || product.price.includes('₹'))) {
                return product.price;
              }
              
              // Otherwise, add currency symbol
              const currency = product.currency || 'USD';
              const currencySymbols: Record<string, string> = {
                'USD': '$',
                'EUR': '€',
                'GBP': '£',
                'JPY': '¥',
                'INR': '₹',
                'CAD': '$',
                'AUD': '$'
              };
              
              const symbol = currencySymbols[currency] || currency;
              return `${symbol}${product.price}`;
            })()}
          </p>
        </div>
        
        {/* Store name - Enhanced bottom section */}
        <div className="mt-auto pt-2 border-t border-slate-200/50 dark:border-slate-700/50">
          <div className="flex items-center space-x-1.5">
            <svg className="w-3 h-3 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            <p className="text-xs text-slate-600 dark:text-slate-400 font-medium tracking-wide truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors duration-200">
              {storeName}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 