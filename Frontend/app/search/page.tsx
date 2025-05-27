"use client"

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { SlidersHorizontal, X } from 'lucide-react'
import { searchProperties } from '@/lib/mock-data'
import { PropertyGrid } from '@/components/property-grid'
import { SearchBar } from '@/components/search-bar'
import { FilterPanel, FilterOptions } from '@/components/filter-panel'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { suggestionQueries } from '@/lib/mock-data'
import { Property } from '@/lib/mock-data'

export default function SearchPage() {
  const searchParams = useSearchParams()
  const initialQuery = searchParams.get('q') || ''
  const initialFilter = (searchParams.get('filter') as 'buy' | 'rent' | null) || 'buy'
  
  const [searchResults, setSearchResults] = useState(() => 
    initialQuery ? searchProperties(initialQuery, initialFilter) : { properties: [], searchTerm: '', totalResults: 0 }
  )
  
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([])
  const [activeFilters, setActiveFilters] = useState<FilterOptions | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
  
  // Effect to handle URL parameter changes
  useEffect(() => {
    if (initialQuery) {
      performSearch(initialQuery, initialFilter as 'buy' | 'rent')
    } else {
      // If no query, show all properties with default scores
      const results = searchProperties('', initialFilter as 'buy' | 'rent')
      setSearchResults(results)
    }
  }, [initialQuery, initialFilter])

  // Initialize filtered properties when search results change
  useEffect(() => {
    setFilteredProperties(searchResults.properties)
  }, [searchResults.properties])
  
  const performSearch = (query: string, filter: 'buy' | 'rent') => {
    setIsLoading(true)
    
    // Simulate API call delay
    setTimeout(() => {
      const results = searchProperties(query, filter)
      setSearchResults(results)
      setIsLoading(false)
    }, 800)
  }
  
  const handleSearch = (query: string, filter: 'buy' | 'rent') => {
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
    <div className="container mx-auto px-4 md:px-6 py-8 md:py-12">
      <div className="mb-8 max-w-6xl mx-auto">
        <h1 className="text-2xl md:text-3xl font-bold mb-6 text-center">Find Your Perfect Cape Town Property</h1>
        <SearchBar 
          onSearch={handleSearch} 
          className="mb-6"
          suggestions={suggestionQueries}
        />
        
        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center">
            <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            <p className="mt-4 text-muted-foreground">Searching for properties...</p>
          </div>
        ) : (
          searchResults.searchTerm || searchResults.properties.length > 0 ? (
            <div className="flex gap-6">
              {/* Desktop Filter Panel - Left Side */}
              <div className="hidden lg:block flex-shrink-0">
                <div className="sticky top-24">
                  <FilterPanel
                    properties={searchResults.properties}
                    onFilterChange={handleFilterChange}
                  />
                </div>
              </div>

              {/* Main Content - Right Side */}
              <div className="flex-1 min-w-0">
                <div className="space-y-6">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex flex-col gap-2">
                      <h2 className="text-xl font-semibold">
                        {filteredProperties.length > 0 
                          ? `${filteredProperties.length} ${filteredProperties.length === 1 ? 'property' : 'properties'} found`
                          : 'No properties found'
                        }
                      </h2>
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
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                      {/* Mobile Filter Button */}
                      <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
                        <SheetTrigger asChild>
                          <Button variant="outline" size="sm" className="lg:hidden">
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
                        <SheetContent side="left" className="w-80 p-0">
                          <SheetHeader className="p-6 pb-0">
                            <SheetTitle>Filters & Sort</SheetTitle>
                          </SheetHeader>
                          <div className="p-6 pt-0">
                            <FilterPanel
                              properties={searchResults.properties}
                              onFilterChange={handleFilterChange}
                              className="w-full border-0 shadow-none"
                            />
                          </div>
                        </SheetContent>
                      </Sheet>
                      
                      {searchResults.searchTerm && searchResults.searchTerm.trim() && (
                        <div className="text-sm text-muted-foreground">
                          <span>Search: &quot;{searchResults.searchTerm}&quot;</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {filteredProperties.length > 0 ? (
                    <PropertyGrid
                      properties={filteredProperties}
                      searchTerm={searchResults.searchTerm}
                    />
                  ) : searchResults.properties.length > 0 ? (
                    <div className="py-12 text-center">
                      <div className="max-w-md mx-auto space-y-4">
                        <div className="text-6xl">🔍</div>
                        <h3 className="text-lg font-semibold">No matches found</h3>
                        <p className="text-muted-foreground">
                          Try adjusting your filters or search criteria to find more properties.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="py-12 text-center">
                      <div className="max-w-md mx-auto space-y-4">
                        <div className="text-6xl">🏠</div>
                        <h3 className="text-lg font-semibold">No properties found</h3>
                        <p className="text-muted-foreground">
                          Try a different search term or browse all properties.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">
                Enter your search above to find properties in Cape Town
              </p>
            </div>
          )
        )}
      </div>
    </div>
  )
}