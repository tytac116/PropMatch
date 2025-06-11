"use client"

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, Filter, X, SlidersHorizontal, ArrowUpDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { Property } from '@/lib/mock-data'

export interface FilterOptions {
  priceRange: [number, number]
  propertyTypes: string[]
  bedrooms: string
  bathrooms: string
  areaRange: [number, number]
  neighborhoods: string[]
  features: string[]
  sortBy: 'match_score' | 'price_low' | 'price_high' | 'area_low' | 'area_high' | 'newest' | 'oldest'
}

interface FilterPanelProps {
  properties: Property[]
  onFilterChange: (filteredProperties: Property[], activeFilters: FilterOptions) => void
  className?: string
}

const PROPERTY_TYPES = ['apartment', 'house', 'villa', 'condo', 'townhouse']
const BEDROOM_OPTIONS = ['Any', '1', '2', '3', '4', '5+']
const BATHROOM_OPTIONS = ['Any', '1', '2', '3', '4', '5+']
const SORT_OPTIONS = [
  { value: 'match_score', label: 'AI Match Score' },
  { value: 'price_low', label: 'Price: Low to High' },
  { value: 'price_high', label: 'Price: High to Low' },
  { value: 'area_low', label: 'Area: Small to Large' },
  { value: 'area_high', label: 'Area: Large to Small' },
  { value: 'newest', label: 'Newest Listed' },
  { value: 'oldest', label: 'Oldest Listed' }
]

export function FilterPanel({ properties, onFilterChange, className }: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [filters, setFilters] = useState<FilterOptions>({
    priceRange: [0, 60000000],
    propertyTypes: [],
    bedrooms: 'Any',
    bathrooms: 'Any',
    areaRange: [0, 600],
    neighborhoods: [],
    features: [],
    sortBy: 'match_score'
  })

  // Extract unique values from properties
  const allNeighborhoods = Array.from(new Set(properties.map(p => p.location.neighborhood))).sort()
  const allFeatures = Array.from(new Set(properties.flatMap(p => p.features))).sort()
  const maxPrice = Math.max(...properties.map(p => p.price))
  const maxArea = Math.max(...properties.map(p => p.area))

  // Initialize price and area ranges based on actual data
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      priceRange: [0, maxPrice],
      areaRange: [0, maxArea]
    }))
  }, [maxPrice, maxArea])

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...properties]

    // Price filter
    filtered = filtered.filter(p => 
      p.price >= filters.priceRange[0] && p.price <= filters.priceRange[1]
    )

    // Property type filter
    if (filters.propertyTypes.length > 0) {
      filtered = filtered.filter(p => filters.propertyTypes.includes(p.type))
    }

    // Bedroom filter
    if (filters.bedrooms !== 'Any') {
      const bedroomCount = filters.bedrooms === '5+' ? 5 : parseInt(filters.bedrooms)
      filtered = filtered.filter(p => 
        filters.bedrooms === '5+' ? p.bedrooms >= 5 : p.bedrooms === bedroomCount
      )
    }

    // Bathroom filter
    if (filters.bathrooms !== 'Any') {
      const bathroomCount = filters.bathrooms === '5+' ? 5 : parseInt(filters.bathrooms)
      filtered = filtered.filter(p => 
        filters.bathrooms === '5+' ? p.bathrooms >= 5 : p.bathrooms === bathroomCount
      )
    }

    // Area filter
    filtered = filtered.filter(p => 
      p.area >= filters.areaRange[0] && p.area <= filters.areaRange[1]
    )

    // Neighborhood filter
    if (filters.neighborhoods.length > 0) {
      filtered = filtered.filter(p => filters.neighborhoods.includes(p.location.neighborhood))
    }

    // Features filter
    if (filters.features.length > 0) {
      filtered = filtered.filter(p => 
        filters.features.every(feature => p.features.includes(feature))
      )
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'match_score':
          return (b.searchScore || 0) - (a.searchScore || 0)
        case 'price_low':
          return a.price - b.price
        case 'price_high':
          return b.price - a.price
        case 'area_low':
          return a.area - b.area
        case 'area_high':
          return b.area - a.area
        case 'newest':
          return new Date(b.listedDate).getTime() - new Date(a.listedDate).getTime()
        case 'oldest':
          return new Date(a.listedDate).getTime() - new Date(b.listedDate).getTime()
        default:
          return 0
      }
    })

    onFilterChange(filtered, filters)
  }, [filters, properties, onFilterChange])

  const handlePropertyTypeChange = (type: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      propertyTypes: checked 
        ? [...prev.propertyTypes, type]
        : prev.propertyTypes.filter(t => t !== type)
    }))
  }

  const handleNeighborhoodChange = (neighborhood: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      neighborhoods: checked 
        ? [...prev.neighborhoods, neighborhood]
        : prev.neighborhoods.filter(n => n !== neighborhood)
    }))
  }

  const handleFeatureChange = (feature: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      features: checked 
        ? [...prev.features, feature]
        : prev.features.filter(f => f !== feature)
    }))
  }

  const clearAllFilters = () => {
    setFilters({
      priceRange: [0, maxPrice],
      propertyTypes: [],
      bedrooms: 'Any',
      bathrooms: 'Any',
      areaRange: [0, maxArea],
      neighborhoods: [],
      features: [],
      sortBy: 'match_score'
    })
  }

  const getActiveFilterCount = () => {
    let count = 0
    if (filters.priceRange[0] > 0 || filters.priceRange[1] < maxPrice) count++
    if (filters.propertyTypes.length > 0) count++
    if (filters.bedrooms !== 'Any') count++
    if (filters.bathrooms !== 'Any') count++
    if (filters.areaRange[0] > 0 || filters.areaRange[1] < maxArea) count++
    if (filters.neighborhoods.length > 0) count++
    if (filters.features.length > 0) count++
    return count
  }

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `R${(price / 1000000).toFixed(1)}M`
    }
    return `R${(price / 1000).toFixed(0)}K`
  }

  return (
    <Card className={cn("w-80 h-fit", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Filter className="h-5 w-5" />
            Filters
            {getActiveFilterCount() > 0 && (
              <Badge variant="secondary" className="ml-1">
                {getActiveFilterCount()}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-1">
            {getActiveFilterCount() > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="h-8 px-2 text-xs"
              >
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Sort By */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2 text-sm font-medium">
              <ArrowUpDown className="h-4 w-4" />
              Sort By
            </Label>
            <Select value={filters.sortBy} onValueChange={(value: any) => setFilters(prev => ({ ...prev, sortBy: value }))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Separator />

          {/* Price Range */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Price Range</Label>
            <div className="px-2">
              <Slider
                value={filters.priceRange}
                onValueChange={(value) => setFilters(prev => ({ ...prev, priceRange: value as [number, number] }))}
                max={maxPrice}
                min={0}
                step={100000}
                className="w-full"
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{formatPrice(filters.priceRange[0])}</span>
              <span>{formatPrice(filters.priceRange[1])}</span>
            </div>
          </div>

          {/* Property Type */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Property Type</Label>
            <div className="grid grid-cols-2 gap-2">
              {PROPERTY_TYPES.map(type => (
                <div key={type} className="flex items-center space-x-2">
                  <Checkbox
                    id={type}
                    checked={filters.propertyTypes.includes(type)}
                    onCheckedChange={(checked) => handlePropertyTypeChange(type, checked as boolean)}
                  />
                  <Label htmlFor={type} className="text-sm capitalize cursor-pointer">
                    {type}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Bedrooms */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Bedrooms</Label>
            <Select value={filters.bedrooms} onValueChange={(value) => setFilters(prev => ({ ...prev, bedrooms: value }))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BEDROOM_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Bathrooms */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Bathrooms</Label>
            <Select value={filters.bathrooms} onValueChange={(value) => setFilters(prev => ({ ...prev, bathrooms: value }))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BATHROOM_OPTIONS.map(option => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Area Range */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Area (m²)</Label>
            <div className="px-2">
              <Slider
                value={filters.areaRange}
                onValueChange={(value) => setFilters(prev => ({ ...prev, areaRange: value as [number, number] }))}
                max={maxArea}
                min={0}
                step={10}
                className="w-full"
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{filters.areaRange[0]}m²</span>
              <span>{filters.areaRange[1]}m²</span>
            </div>
          </div>

          {/* Neighborhoods */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Neighborhoods</Label>
            <div className="max-h-32 overflow-y-auto space-y-2">
              {allNeighborhoods.map(neighborhood => (
                <div key={neighborhood} className="flex items-center space-x-2">
                  <Checkbox
                    id={neighborhood}
                    checked={filters.neighborhoods.includes(neighborhood)}
                    onCheckedChange={(checked) => handleNeighborhoodChange(neighborhood, checked as boolean)}
                  />
                  <Label htmlFor={neighborhood} className="text-sm cursor-pointer">
                    {neighborhood}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Features</Label>
            <div className="max-h-40 overflow-y-auto space-y-2">
              {allFeatures.map(feature => (
                <div key={feature} className="flex items-center space-x-2">
                  <Checkbox
                    id={feature}
                    checked={filters.features.includes(feature)}
                    onCheckedChange={(checked) => handleFeatureChange(feature, checked as boolean)}
                  />
                  <Label htmlFor={feature} className="text-sm cursor-pointer">
                    {feature}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
} 