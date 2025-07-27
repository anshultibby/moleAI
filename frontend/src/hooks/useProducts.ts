import { useState } from 'react'
import { Product, SearchLinksData } from '../types'

export function useProducts() {
  const [allProducts, setAllProducts] = useState<Product[]>([])
  const [searchLinksData, setSearchLinksData] = useState<SearchLinksData[]>([])
  const [reasoningData, setReasoningData] = useState<any[]>([])
  const [selectedPriceBucket, setSelectedPriceBucket] = useState('')
  const [selectedBrand, setSelectedBrand] = useState('')

  // Filter out duplicate products based on name and store
  const getUniqueProducts = (products: Product[]): Product[] => {
    const seen = new Set<string>()
    return products.filter(product => {
      const key = `${product.product_name || product.name}-${product.store}-${product.price}`
      if (seen.has(key)) {
        console.log(`Duplicate product filtered out: ${key}`)
        return false
      }
      seen.add(key)
      return true
    })
  }

  const addProduct = (product: Product) => {
    setAllProducts(prev => [...prev, product])
  }

  const removeProduct = (productId: string) => {
    setAllProducts(prev => prev.filter(p => p.id !== productId))
  }

  const removeProductById = (productId: string) => {
    console.log(`Removing product by ID: ${productId}`)
    setAllProducts(prev => prev.filter(p => p.id !== productId))
  }

  const removeSearchLinks = (searchLinksId: string) => {
    setSearchLinksData(prev => prev.filter(s => s.id !== searchLinksId))
  }

  const clearAllProducts = () => {
    setAllProducts([])
    setSearchLinksData([])
    setReasoningData([])
    setSelectedPriceBucket('')
    setSelectedBrand('')
  }

  const clearFilters = () => {
    setSearchLinksData([])
    setReasoningData([])
    setSelectedPriceBucket('')
    setSelectedBrand('')
  }

  const uniqueProducts = getUniqueProducts(allProducts)

  return {
    allProducts,
    uniqueProducts,
    searchLinksData,
    reasoningData,
    selectedPriceBucket,
    selectedBrand,
    addProduct,
    removeProduct,
    removeProductById,
    removeSearchLinks,
    clearAllProducts,
    clearFilters,
    setSelectedPriceBucket,
    setSelectedBrand
  }
} 