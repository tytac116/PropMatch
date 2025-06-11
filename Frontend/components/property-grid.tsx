"use client"

import { Property } from '@/lib/mock-data'
import { PropertyCard } from '@/components/property-card'

interface PropertyGridProps {
  properties: Property[]
  searchTerm?: string
  className?: string
}

export function PropertyGrid({ properties, searchTerm, className }: PropertyGridProps) {
  if (properties.length === 0) {
    return (
      <div className="min-h-[300px] flex flex-col items-center justify-center text-center p-8">
        <h3 className="text-2xl font-bold mb-2">No properties found</h3>
        <p className="text-muted-foreground">
          {searchTerm
            ? `No properties match your search for "${searchTerm}". Try different keywords or filters.`
            : 'No properties are currently available. Please check back later.'}
        </p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {properties.map((property) => (
          <PropertyCard 
            key={property.id} 
            property={property} 
            searchTerm={searchTerm}
          />
        ))}
      </div>
    </div>
  )
}