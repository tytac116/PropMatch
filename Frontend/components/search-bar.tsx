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
}

export function SearchBar({ onSearch, className, suggestions = [] }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<'buy' | 'rent'>('buy')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchContainerRef = useRef<HTMLDivElement>(null)

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
    if (query.trim()) {
      onSearch(query, filter)
      setShowSuggestions(false)
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
    <div className={cn("w-full max-w-3xl mx-auto", className)}>
      <div className="flex flex-col items-center space-y-4 w-full">
        <Tabs defaultValue="buy" className="w-full max-w-md" onValueChange={(value) => setFilter(value as 'buy' | 'rent')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="buy" className="text-lg">Buy</TabsTrigger>
            <TabsTrigger value="rent" className="text-lg">Rent</TabsTrigger>
          </TabsList>
        </Tabs>

        <div ref={searchContainerRef} className="relative w-full">
          <div className="flex w-full">
            <div className="relative flex-grow">
              <Input
                className="pr-10 h-12 text-lg rounded-l-lg focus-visible:ring-2 focus-visible:ring-primary"
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
              className="rounded-r-lg h-12"
            >
              <Search className="h-5 w-5 mr-2" />
              <span>Search</span>
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
              <div className="p-2 text-sm text-muted-foreground">
                Try searching for:
              </div>
              <ul className="p-2 space-y-1">
                {suggestions.map((suggestion, index) => (
                  <li key={index}>
                    <button
                      className="w-full text-left p-2 hover:bg-muted rounded-md transition-colors text-sm duration-150"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}