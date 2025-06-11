"use client"

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { SlidersHorizontal, AlertCircle } from 'lucide-react'
import { searchProperties, PerformanceMonitor as PerfMonitorClass, APIError } from '@/lib/api'
import type { Property as APIProperty, SearchResponse } from '@/lib/api'
import { PropertyGrid } from '@/components/property-grid'
import { SearchBar } from '@/components/search-bar'
import { FilterPanel, FilterOptions } from '@/components/filter-panel'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { suggestionQueries } from '@/lib/mock-data'
import { AnimatedSearchLoader } from '@/components/animated-search-loader'

// Transform API property to frontend property format
function transformAPIProperty(apiProperty: APIProperty): Property {
  return {
    id: apiProperty.listing_number,
    title: apiProperty.title || `${apiProperty.type} in ${apiProperty.location.neighborhood}`,
    description: apiProperty.description || '',
    price: apiProperty.price || 0,
    currency: apiProperty.currency || 'ZAR',
    type: mapPropertyType(apiProperty.type),
    bedrooms: apiProperty.bedrooms || 0,
    bathrooms: apiProperty.bathrooms || 0,
    area: apiProperty.area || 0,
    areaUnit: apiProperty.areaUnit || 'm²',
    location: {
      address: apiProperty.location.address || '',
      neighborhood: apiProperty.location.neighborhood || '',
      city: apiProperty.location.city || 'Cape Town',
      postalCode: apiProperty.location.postalCode || '',
      country: apiProperty.location.country || 'South Africa'
    },
    images: apiProperty.images || [],
    features: apiProperty.features || [],
    status: mapPropertyStatus(apiProperty.status),
    listedDate: apiProperty.listedDate || new Date().toISOString(),
    searchScore: apiProperty.searchScore,
    matchExplanation: undefined // Will be generated on demand
  }
}

function mapPropertyType(apiType: string): 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse' {
  // Remove enum prefix if present
  const cleanType = apiType?.replace('PropertyType.', '').toLowerCase() || ''
  
  const typeMap: Record<string, 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse'> = {
    'house': 'house',
    'apartment': 'apartment',
    'flat': 'apartment',
    'condo': 'condo',
    'villa': 'villa',
    'townhouse': 'townhouse',
    'penthouse': 'apartment'
  }
  return typeMap[cleanType] || 'house'
}

function mapPropertyStatus(apiStatus: string): 'for_sale' | 'for_rent' {
  // Remove enum prefix if present and handle various backend status formats
  const cleanStatus = apiStatus?.replace('PropertyStatus.', '').toLowerCase() || ''
  
  if (cleanStatus.includes('rent') || cleanStatus.includes('to_rent') || cleanStatus.includes('rental')) {
    return 'for_rent'
  }
  // Default to for_sale for sale, for_sale, or any other status
  return 'for_sale'
}

// Frontend Property interface (keeping compatibility with existing components)
interface Property {
  id: string
  title: string
  description: string
  price: number
  currency: string
  type: 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse'
  bedrooms: number
  bathrooms: number
  area: number
  areaUnit: string
  location: {
    address: string
    neighborhood: string
    city: string
    postalCode: string
    country: string
  }
  images: string[]
  features: string[]
  status: 'for_sale' | 'for_rent'
  listedDate: string
  searchScore?: number
  matchExplanation?: string
}

interface SearchResult {
  properties: Property[]
  searchTerm: string
  totalResults: number
  message?: string
}

export default function SearchPage() {
  const searchParams = useSearchParams()
  const initialQuery = searchParams.get('q') || ''
  const initialFilter = (searchParams.get('filter') as 'buy' | 'rent' | null) || 'buy'
  
  const [searchResults, setSearchResults] = useState<SearchResult>({
    properties: [],
    searchTerm: '',
    totalResults: 0
  })
  
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([])
  const [activeFilters, setActiveFilters] = useState<FilterOptions | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [currentSearchQuery, setCurrentSearchQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
  
  // Session-based caching key
  const getCacheKey = (query: string, filter: string) => `search_${query.trim()}_${filter}`
  
  // Load cached search results if available
  const loadCachedResults = (query: string, filter: string) => {
    if (typeof window === 'undefined') return null
    
    try {
      const cacheKey = getCacheKey(query, filter)
      const cached = sessionStorage.getItem(cacheKey)
      if (cached) {
        const cachedData = JSON.parse(cached)
        // Check if cache is still fresh (5 minutes)
        const cacheAge = Date.now() - cachedData.timestamp
        if (cacheAge < 5 * 60 * 1000) { // 5 minutes
          console.log('Loading cached search results for:', query)
          return cachedData.results
        } else {
          sessionStorage.removeItem(cacheKey)
        }
      }
    } catch (error) {
      console.warn('Failed to load cached results:', error)
    }
    return null
  }
  
  // Save search results to cache
  const saveCachedResults = (query: string, filter: string, results: SearchResult) => {
    if (typeof window === 'undefined') return
    
    try {
      const cacheKey = getCacheKey(query, filter)
      const cacheData = {
        results,
        timestamp: Date.now()
      }
      sessionStorage.setItem(cacheKey, JSON.stringify(cacheData))
      console.log('Cached search results for:', query)
    } catch (error) {
      console.warn('Failed to cache results:', error)
    }
  }
  
  // Effect to handle URL parameter changes
  useEffect(() => {
    if (initialQuery) {
      if (initialFilter === 'rent') {
        // For rent, show empty state with message but preserve query in URL
        setSearchResults({
          properties: [],
          searchTerm: initialQuery,
          totalResults: 0,
          message: 'Rental properties are coming soon! Switch to "Buy" to see available properties for sale.'
        })
      } else {
        // Check for cached results first
        const cached = loadCachedResults(initialQuery, initialFilter)
        if (cached) {
          setSearchResults(cached)
          console.log('Used cached search results, no API call needed')
        } else {
          performSearch(initialQuery, initialFilter as 'buy' | 'rent')
        }
      }
    } else {
      // Show empty state when no query
      setSearchResults({
        properties: [],
        searchTerm: '',
        totalResults: 0
      })
    }
  }, [initialQuery, initialFilter])

  // Initialize filtered properties when search results change
  useEffect(() => {
    setFilteredProperties(searchResults.properties)
  }, [searchResults.properties])
  
  const performSearch = async (query: string, filter: 'buy' | 'rent') => {
    if (!query.trim()) {
      setSearchResults({
        properties: [],
        searchTerm: '',
        totalResults: 0
      })
      return
    }

    setIsLoading(true)
    setCurrentSearchQuery(query.trim())
    setError(null)
    
    try {
      const response = await PerfMonitorClass.measure('search', () =>
        searchProperties({
          query: query.trim(),
          page_size: 9 // Increased from 20 to 9
        })
      )

      // Transform API properties to frontend format
      const transformedProperties = response.properties.map(transformAPIProperty)

      // Detailed logging for debugging
      console.log('=== SEARCH DEBUG INFO ===')
      console.log('Raw API Response:', {
        total: response.properties.length,
        message: response.message,
        timing: response.timing,
        first_property_raw: response.properties[0]
      })
      console.log('Transformed Properties:', {
        total: transformedProperties.length,
        first_property: transformedProperties[0],
        all_statuses: transformedProperties.map(p => p.status),
        all_types: transformedProperties.map(p => p.type)
      })

      // Filter by buy/rent status - be more permissive
      const filteredByStatus = transformedProperties.filter(property => {
        if (filter === 'buy') {
          return property.status === 'for_sale'
        }
        if (filter === 'rent') {
          return property.status === 'for_rent'
        }
        return true
      })

      console.log('After Status Filter:', {
        filter,
        before_filter: transformedProperties.length,
        after_filter: filteredByStatus.length,
        filtered_properties: filteredByStatus.map(p => ({ id: p.id, status: p.status, title: p.title }))
      })

      // If no properties match the filter, show all properties with a warning
      let finalProperties = filteredByStatus
      let filterMessage = response.message

      if (filteredByStatus.length === 0 && transformedProperties.length > 0) {
        finalProperties = transformedProperties
        filterMessage = `Found ${transformedProperties.length} properties, but none match the ${filter === 'buy' ? 'for sale' : 'for rent'} filter. Showing all results.`
        console.warn('No properties matched filter, showing all:', {
          filter,
          originalCount: transformedProperties.length,
          statuses: transformedProperties.map(p => ({ id: p.id, status: p.status }))
        })
      }

      const results: SearchResult = {
        properties: finalProperties,
        searchTerm: query,
        totalResults: finalProperties.length,
        message: filterMessage
      }

      setSearchResults(results)
      
      // Save to cache for faster back navigation
      saveCachedResults(query, filter, results)
      
      console.log('Search completed:', {
        query,
        results: finalProperties.length,
        filter,
        filtered: filteredByStatus.length,
        total: transformedProperties.length
      })
      
    } catch (err) {
      console.error('Search error:', err)
      const errorMessage = err instanceof APIError 
        ? `API Error: ${err.message}` 
        : `Search failed: ${err instanceof Error ? err.message : 'Unknown error'}`
      
      setError(errorMessage)
      setSearchResults({
        properties: [],
        searchTerm: query,
        totalResults: 0
      })
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleSearch = (query: string, filter: 'buy' | 'rent') => {
    if (filter === 'rent') {
      // Don't perform search for rent, just update URL to preserve state
      const url = new URL(window.location.href)
      url.searchParams.set('q', query)
      url.searchParams.set('filter', filter)
      window.history.pushState({}, '', url)
      return
    }
    
    performSearch(query, filter)
    
    // Update URL without refreshing the page
    const url = new URL(window.location.href)
    url.searchParams.set('q', query)
    url.searchParams.set('filter', filter)
    window.history.pushState({}, '', url)
  }

  const handleFilterChange = useCallback((filtered: Property[], filters: FilterOptions) => {
    setFilteredProperties(filtered)
    setActiveFilters(filters)
  }, [])
  
  return (
    <div className="min-h-screen bg-background">
      {/* Search Header */}
      <div className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40 border-b">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-6">
          <SearchBar
            onSearch={handleSearch}
            suggestions={suggestionQueries}
            initialQuery={initialQuery}
            initialFilter={initialFilter}
            className="w-full"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {/* Error display */}
        {error && (
          <Alert className="mb-6" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {isLoading ? (
          <AnimatedSearchLoader searchQuery={currentSearchQuery} />
        ) : (
          searchResults.searchTerm || searchResults.properties.length > 0 ? (
            <div className="flex flex-col lg:flex-row gap-6">
              {/* Desktop Filter Panel - Left Side */}
              <div className="hidden lg:block lg:w-80 flex-shrink-0">
                <div className="sticky top-24 space-y-6">
                  <FilterPanel
                    properties={searchResults.properties}
                    onFilterChange={handleFilterChange}
                  />
                </div>
              </div>

              {/* Main Content - Right Side */}
              <div className="flex-1 min-w-0">
                <div className="space-y-6">
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                      <div className="flex flex-col gap-2 min-w-0 flex-1">
                        <h2 className="text-xl lg:text-2xl font-semibold">
                          {filteredProperties.length > 0 
                            ? `${filteredProperties.length} ${filteredProperties.length === 1 ? 'property' : 'properties'} found`
                            : searchResults.searchTerm
                              ? 'No properties found'
                              : 'Start your search above'
                          }
                        </h2>
                        {/* Remove technical search message, keep only user-friendly message if needed */}
                        {searchResults.message && !searchResults.message.includes('Vector+BM25+AI') && (
                          <p className="text-sm text-muted-foreground">{searchResults.message}</p>
                        )}
                        {activeFilters && (
                          <div className="text-sm text-muted-foreground">
                            {activeFilters.sortBy === 'match_score' && (
                              <span className="inline-flex items-center gap-1">
                                <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                                Sorted by AI Match Score
                              </span>
                            )}
                            {activeFilters.sortBy === 'price_low' && (
                              <span>Sorted by Price: Low to High</span>
                            )}
                            {activeFilters.sortBy === 'price_high' && (
                              <span>Sorted by Price: High to Low</span>
                            )}
                            {activeFilters.sortBy === 'area_low' && (
                              <span>Sorted by Area: Small to Large</span>
                            )}
                            {activeFilters.sortBy === 'area_high' && (
                              <span>Sorted by Area: Large to Small</span>
                            )}
                            {activeFilters.sortBy === 'newest' && (
                              <span>Sorted by Newest Listed</span>
                            )}
                            {activeFilters.sortBy === 'oldest' && (
                              <span>Sorted by Oldest Listed</span>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 flex-shrink-0">
                        {/* Mobile Filter Button */}
                        <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
                          <SheetTrigger asChild>
                            <Button variant="outline" size="sm" className="lg:hidden w-full sm:w-auto">
                              <SlidersHorizontal className="h-4 w-4 mr-2" />
                              Filters
                              {activeFilters && (
                                <span className="ml-1 bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full">
                                  {[
                                    activeFilters.priceRange[0] > 0 || activeFilters.priceRange[1] < Math.max(...searchResults.properties.map(p => p.price)),
                                    activeFilters.propertyTypes.length > 0,
                                    activeFilters.bedrooms !== 'Any',
                                    activeFilters.bathrooms !== 'Any',
                                    activeFilters.areaRange[0] > 0 || activeFilters.areaRange[1] < Math.max(...searchResults.properties.map(p => p.area)),
                                    activeFilters.neighborhoods.length > 0,
                                    activeFilters.features.length > 0
                                  ].filter(Boolean).length}
                                </span>
                              )}
                            </Button>
                          </SheetTrigger>
                          <SheetContent side="left" className="w-[90vw] sm:w-80 p-0">
                            <SheetHeader className="p-4 sm:p-6 pb-0">
                              <SheetTitle>Filters & Sort</SheetTitle>
                            </SheetHeader>
                            <div className="p-4 sm:p-6 pt-0">
                              <FilterPanel
                                properties={searchResults.properties}
                                onFilterChange={handleFilterChange}
                                className="w-full border-0 shadow-none"
                              />
                            </div>
                          </SheetContent>
                        </Sheet>
                        
                        {/* Enhanced Search Query Display */}
                        {searchResults.searchTerm && searchResults.searchTerm.trim() && (
                          <div 
                            className="bg-gradient-to-r from-muted/50 to-muted/30 dark:from-muted/20 dark:to-muted/10 border border-border rounded-lg px-3 py-2 w-full sm:max-w-xs hover:from-muted/70 hover:to-muted/50 dark:hover:from-muted/30 dark:hover:to-muted/20 transition-all duration-200"
                            title={`Search query: ${searchResults.searchTerm}`}
                          >
                            <div className="flex items-center gap-2">
                              <div className="flex-shrink-0">
                                <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                                  Search Query
                                </p>
                                <p className="text-sm font-medium text-foreground truncate">
                                  "{searchResults.searchTerm}"
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {filteredProperties.length > 0 ? (
                    <PropertyGrid
                      properties={filteredProperties}
                      searchTerm={searchResults.searchTerm}
                    />
                  ) : searchResults.properties.length > 0 ? (
                    <div className="py-12 text-center">
                      <div className="max-w-md mx-auto space-y-4 px-4">
                        <div className="text-6xl">🔍</div>
                        <h3 className="text-lg font-semibold">No matches found</h3>
                        <p className="text-muted-foreground">
                          Try adjusting your filters or search criteria to find more properties.
                        </p>
                      </div>
                    </div>
                  ) : searchResults.searchTerm ? (
                    <div className="py-12 text-center">
                      <div className="max-w-md mx-auto space-y-4 px-4">
                        {initialFilter === 'rent' ? (
                          <>
                            <div className="text-6xl">🏠</div>
                            <h3 className="text-lg font-semibold">Rental Properties Coming Soon!</h3>
                            <p className="text-muted-foreground">
                              We're working hard to bring you rental listings for "{searchResults.searchTerm}". 
                              For now, switch to the <strong>Buy</strong> tab to explore amazing properties for sale!
                            </p>
                          </>
                        ) : (
                          <>
                            <div className="text-6xl">😔</div>
                            <h3 className="text-lg font-semibold">No properties found</h3>
                            <p className="text-muted-foreground">
                              We couldn't find any properties matching "{searchResults.searchTerm}". 
                              Try adjusting your search terms or filters.
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="py-12 text-center">
                      <div className="max-w-md mx-auto space-y-4 px-4">
                        <div className="text-6xl">🏠</div>
                        <h3 className="text-lg font-semibold">Start your property search</h3>
                        <p className="text-muted-foreground">
                          Enter a search query above to find properties that match your needs using our AI-powered search.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center">
              <div className="max-w-md mx-auto space-y-4 px-4">
                <div className="text-6xl">🏠</div>
                <h3 className="text-lg font-semibold">Start your property search</h3>
                <p className="text-muted-foreground">
                  Enter a search query above to find properties that match your needs using our AI-powered search.
                </p>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}