import { Product } from '../types'
import ProductCard from './ProductCard'

interface ProductGridProps {
  products: Product[]
  title?: string
  onRemoveProduct?: (id: string) => void
}

export default function ProductGrid({ products, title, onRemoveProduct }: ProductGridProps) {
  if (!products || products.length === 0) {
    return null
  }

  return (
    <div className="my-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
      {title && (
        <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4 flex items-center">
          <span className="mr-2">🛍️</span>
          {title}
        </h3>
      )}
      
      {/* Responsive grid that works well in chat */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {products.map((product, index) => (
          <div 
            key={product.id || index} 
            className="transform transition-all duration-300 hover:scale-105 hover:shadow-xl hover:-translate-y-2 animate-fadeInUp"
            style={{
              animationDelay: `${index * 150}ms`,
              animationFillMode: 'both'
            }}
          >
            <ProductCard
              product={product}
              onRemove={onRemoveProduct || (() => {})}
            />
          </div>
        ))}
      </div>
      
      {products.length > 4 && (
        <div className="mt-3 text-center">
          <span className="text-sm text-slate-600 dark:text-slate-400">
            Showing {products.length} products
          </span>
        </div>
      )}
    </div>
  )
}
