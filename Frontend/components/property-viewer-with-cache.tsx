"use client"

import { useEffect, useState } from 'react'
import { Property } from '@/lib/mock-data'
import { PropertyViewer } from '@/components/property-viewer'

interface PropertyViewerWithCacheProps {
  property: Property
  searchTerm?: string
  enableStreaming?: boolean
}

export function PropertyViewerWithCache({ 
  property, 
  searchTerm, 
  enableStreaming 
}: PropertyViewerWithCacheProps) {
  const [propertyWithScore, setPropertyWithScore] = useState(property)

  useEffect(() => {
    // Try to get search score from cache if we have a search term
    if (searchTerm && searchTerm.trim()) {
      try {
        // Look for cached search results that contain this property
        const cacheKeys = Object.keys(sessionStorage).filter(key => 
          key.startsWith('search_') && key.toLowerCase().includes(searchTerm.toLowerCase().trim())
        )
        
        for (const cacheKey of cacheKeys) {
          const cached = sessionStorage.getItem(cacheKey)
          if (cached) {
            const cachedData = JSON.parse(cached)
            const cachedProperty = cachedData.results?.properties?.find(
              (p: any) => p.id === property.id
            )
            if (cachedProperty?.searchScore) {
              console.log('Found cached search score:', cachedProperty.searchScore, 'for property:', property.id)
              setPropertyWithScore({
                ...property,
                searchScore: cachedProperty.searchScore
              })
              break
            }
          }
        }
      } catch (error) {
        console.warn('Failed to load cached search score:', error)
      }
    }
  }, [property, searchTerm])

  return (
    <PropertyViewer 
      property={propertyWithScore} 
      searchTerm={searchTerm}
      enableStreaming={enableStreaming}
    />
  )
} 