"use client"

import { Property } from '@/lib/mock-data'
import { PropertyCard } from '@/components/property-card'
import { cn } from '@/lib/utils'

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
    <div className={cn("grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr", className)}>
      {properties.map((property) => (
        <PropertyCard 
          key={property.id} 
          property={property} 
          searchTerm={searchTerm}
          className="h-full"
        />
      ))}
    </div>
  )
}