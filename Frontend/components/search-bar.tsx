"use client"

import { useState, useRef, useEffect } from 'react'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

interface SearchBarProps {
  onSearch: (query: string, filter: 'buy' | 'rent') => void;
  className?: string;
  suggestions?: string[];
  initialQuery?: string;
  initialFilter?: 'buy' | 'rent';
}

export function SearchBar({ onSearch, className, suggestions = [], initialQuery = '', initialFilter = 'buy' }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)
  const [filter, setFilter] = useState<'buy' | 'rent'>(initialFilter)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [showRentMessage, setShowRentMessage] = useState(false)
  const searchContainerRef = useRef<HTMLDivElement>(null)

  // Update query when initialQuery changes (e.g., from URL params)
  useEffect(() => {
    if (initialQuery && initialQuery !== query) {
      setQuery(initialQuery)
    }
  }, [initialQuery])

  // Update filter when initialFilter changes
  useEffect(() => {
    if (initialFilter && initialFilter !== filter) {
      setFilter(initialFilter)
    }
  }, [initialFilter])

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Handle escape key to close suggestions
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('keydown', handleEscapeKey)
    return () => {
      document.removeEventListener('keydown', handleEscapeKey)
    }
  }, [])

  const handleSearch = () => {
    if (query.trim() && filter === 'buy') {
      onSearch(query, filter)
      setShowSuggestions(false)
    } else if (filter === 'rent') {
      setShowRentMessage(true)
      setTimeout(() => setShowRentMessage(false), 3000) // Hide after 3 seconds
    }
  }

  const handleFilterChange = (value: 'buy' | 'rent') => {
    setFilter(value)
    if (value === 'rent') {
      setShowRentMessage(true)
      setTimeout(() => setShowRentMessage(false), 3000)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    onSearch(suggestion, filter)
    setShowSuggestions(false)
  }

  const handleClearSearch = () => {
    setQuery('')
    setShowSuggestions(true)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
    if (suggestions.length > 0) {
      setShowSuggestions(true)
    }
  }

  const handleInputFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true)
    }
  }

  return (
    <div className={cn("w-full max-w-4xl mx-auto", className)}>
      <div className="flex flex-col items-center space-y-4 w-full">
        <Tabs value={filter} className="w-full max-w-sm" onValueChange={(value) => handleFilterChange(value as 'buy' | 'rent')}>
          <TabsList className="grid w-full grid-cols-2 h-10 sm:h-11">
            <TabsTrigger value="buy" className="text-base sm:text-lg">Buy</TabsTrigger>
            <TabsTrigger value="rent" className="text-base sm:text-lg">Rent</TabsTrigger>
          </TabsList>
        </Tabs>

        <div ref={searchContainerRef} className="relative w-full">
          <div className="flex w-full gap-0">
            <div className="relative flex-grow">
              <Input
                className="pr-10 h-11 sm:h-12 text-base sm:text-lg rounded-l-lg rounded-r-none focus-visible:ring-2 focus-visible:ring-primary border-r-0"
                placeholder="Describe your dream property..."
                value={query}
                onChange={handleInputChange}
                onFocus={handleInputFocus}
                onKeyDown={handleKeyDown}
              />
              {query && (
                <Button 
                  variant="ghost" 
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 rounded-full"
                  onClick={handleClearSearch}
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Clear search</span>
                </Button>
              )}
            </div>
            <Button 
              onClick={handleSearch}
              className="rounded-r-lg rounded-l-none h-11 sm:h-12 px-4 sm:px-6 flex-shrink-0"
            >
              <Search className="h-4 w-4 sm:h-5 sm:w-5 sm:mr-2" />
              <span className="hidden sm:inline">Search</span>
            </Button>
          </div>

          {/* Animated suggestions dropdown */}
          <div className={cn(
            "absolute z-10 w-full mt-1 bg-background border rounded-lg shadow-lg max-h-60 overflow-hidden transition-all duration-300 ease-in-out",
            showSuggestions && suggestions.length > 0
              ? "opacity-100 translate-y-0 max-h-60"
              : "opacity-0 -translate-y-2 max-h-0 border-0"
          )}>
            <div className="overflow-auto max-h-60">
              <div className="p-3 text-sm text-muted-foreground">
                Try searching for:
              </div>
              <ul className="p-2 space-y-1">
                {suggestions.map((suggestion, index) => (
                  <li key={index}>
                    <button
                      className="w-full text-left p-3 hover:bg-muted rounded-md transition-colors text-sm duration-150"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Rent Coming Soon Message */}
          {showRentMessage && (
            <div className="absolute z-20 w-full mt-1 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg shadow-lg p-4">
              <div className="text-center">
                <div className="text-blue-600 dark:text-blue-400 font-medium mb-1">
                  🏠 Rental Properties Coming Soon!
                </div>
                <div className="text-sm text-blue-600/80 dark:text-blue-400/80">
                  We're working hard to bring you rental listings. For now, explore our amazing properties for sale!
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}