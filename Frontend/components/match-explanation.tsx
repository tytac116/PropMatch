"use client"

import { useState, useEffect, useRef } from 'react'
import { Property } from '@/lib/api'
import { streamExplanation, generateExplanation, PerformanceMonitor, APIError } from '@/lib/api'
import type { PropertyExplanation, ExplanationPoint } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { BadgeCheck, BadgeX, Loader2, AlertCircle, Zap, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface MatchExplanationProps {
  property: Property
  searchTerm: string
  className?: string
  enableStreaming?: boolean
}

export function MatchExplanation({ 
  property, 
  searchTerm, 
  className,
  enableStreaming = true 
}: MatchExplanationProps) {
  const [explanation, setExplanation] = useState<PropertyExplanation | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const [displayText, setDisplayText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isCached, setIsCached] = useState(false)
  const [loadTime, setLoadTime] = useState<number | null>(null)
  const [mounted, setMounted] = useState(false)
  const typewriterRef = useRef<number | null>(null)
  
  const hasValidSearchTerm = searchTerm && searchTerm.trim().length > 0
  
  // Session-based explanation caching
  const getExplanationCacheKey = (query: string, listingNumber: string) => 
    `explanation_${query.trim()}_${listingNumber}`
  
  const loadCachedExplanation = (query: string, listingNumber: string) => {
    if (typeof window === 'undefined') return null
    
    try {
      const cacheKey = getExplanationCacheKey(query, listingNumber)
      const cached = sessionStorage.getItem(cacheKey)
      if (cached) {
        const cachedData = JSON.parse(cached)
        // Check if cache is still fresh (10 minutes for explanations)
        const cacheAge = Date.now() - cachedData.timestamp
        if (cacheAge < 10 * 60 * 1000) { // 10 minutes
          console.log('Loading cached explanation for:', query, listingNumber)
          return cachedData.explanation
        } else {
          sessionStorage.removeItem(cacheKey)
        }
      }
    } catch (error) {
      console.warn('Failed to load cached explanation:', error)
    }
    return null
  }
  
  const saveCachedExplanation = (query: string, listingNumber: string, explanation: PropertyExplanation) => {
    if (typeof window === 'undefined') return
    
    try {
      const cacheKey = getExplanationCacheKey(query, listingNumber)
      const cacheData = {
        explanation,
        timestamp: Date.now()
      }
      sessionStorage.setItem(cacheKey, JSON.stringify(cacheData))
      console.log('Cached explanation for:', query, listingNumber)
    } catch (error) {
      console.warn('Failed to cache explanation:', error)
    }
  }
  
  const generateExplanationHandler = async () => {
    if (!hasValidSearchTerm || !property.listing_number) return
    
    // Check for cached explanation first
    const cached = loadCachedExplanation(searchTerm.trim(), property.listing_number)
    if (cached) {
      setExplanation(cached)
      setIsCached(true)
      setLoadTime(50) // Instant load time for cached
      console.log('Used cached explanation, no API call needed')
      return
    }
    
    setIsLoading(true)
    setError(null)
    setExplanation(null)
    setStreamContent('')
    
    try {
      if (enableStreaming) {
        // Use streaming API
        setIsStreaming(true)
        const startTime = performance.now()
        
        const stream = streamExplanation(searchTerm.trim(), property.listing_number)
        
        for await (const chunk of stream) {
          if (chunk.type === 'cached' && chunk.explanation) {
            // Cached response - show immediately
            setExplanation(chunk.explanation)
            setIsCached(true)
            setLoadTime(performance.now() - startTime)
            saveCachedExplanation(searchTerm.trim(), property.listing_number, chunk.explanation)
            break
          } else if (chunk.type === 'chunk' && chunk.content) {
            // Streaming content
            setStreamContent(prev => prev + chunk.content)
          } else if (chunk.type === 'complete' && chunk.explanation) {
            // Final explanation
            setExplanation(chunk.explanation)
            setIsCached(chunk.cached || false)
            setLoadTime(performance.now() - startTime)
            saveCachedExplanation(searchTerm.trim(), property.listing_number, chunk.explanation)
            break
          } else if (chunk.type === 'error') {
            throw new Error(chunk.message || 'Streaming failed')
          }
        }
        
        setIsStreaming(false)
        setStreamContent('')
      } else {
        // Use cached/direct API
        const response = await PerformanceMonitor.measure('explanation', () =>
          generateExplanation({
            search_query: searchTerm.trim(),
            listing_number: property.listing_number
          })
        )
        
        setExplanation(response)
        setIsCached(response.cached)
        setLoadTime(response.__duration)
        saveCachedExplanation(searchTerm.trim(), property.listing_number, response)
      }
      
    } catch (err) {
      console.error('Explanation generation error:', err)
      const errorMessage = err instanceof APIError 
        ? `API Error: ${err.message}` 
        : `Failed to generate explanation: ${err instanceof Error ? err.message : 'Unknown error'}`
      setError(errorMessage)
    } finally {
      setIsLoading(false)
      setIsStreaming(false)
    }
  }
  
  // Auto-generate explanation when streaming is enabled and we have the required data
  useEffect(() => {
    if (enableStreaming && searchTerm && searchTerm.trim() && property.listing_number && !explanation && !isLoading) {
      generateExplanationHandler()
    }
  }, [enableStreaming, searchTerm, property.listing_number, explanation, isLoading])
    
  // Ensure component is mounted to prevent hydration issues
  useEffect(() => {
    setMounted(true)
  }, [])

  // Improved typewriter effect
  useEffect(() => {
    if (!mounted || !streamContent || !isStreaming) {
      setDisplayText('')
      return
    }

    // Clear any existing timeout
    if (typewriterRef.current) {
      clearTimeout(typewriterRef.current)
    }

    let index = 0
    setDisplayText('')
    
    const typeChar = () => {
      if (index < streamContent.length) {
        setDisplayText(streamContent.slice(0, index + 1))
        index++
        typewriterRef.current = window.setTimeout(typeChar, 20) // Faster typing
      }
    }

    typeChar()

    return () => {
      if (typewriterRef.current) {
        clearTimeout(typewriterRef.current)
      }
    }
  }, [streamContent, isStreaming, mounted])
  
  if (!hasValidSearchTerm) {
    return (
      <Card className={cn("overflow-hidden", className)}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Enter a search query to see AI explanation</p>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>AI Match Analysis</span>
          {searchTerm && (
            <span className="text-sm font-normal text-muted-foreground bg-muted px-2 py-1 rounded-md">
              "{searchTerm}"
            </span>
          )}
        </h3>
        
          <div className="flex items-center gap-2">
            {loadTime && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {loadTime.toFixed(0)}ms
              </span>
            )}
            {isCached && (
              <span className="text-xs bg-green-500/10 text-green-600 px-2 py-1 rounded-full flex items-center gap-1">
                <Zap className="h-3 w-3" />
                Cached
              </span>
            )}
          </div>
        </div>
        
        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>{error}</span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={generateExplanationHandler}
                disabled={isLoading}
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}
        
        {/* Loading State */}
        {isLoading && !explanation && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center space-y-3">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
              <p className="text-sm text-muted-foreground">
                {isStreaming ? 'Generating AI explanation...' : 'Loading explanation...'}
              </p>
            </div>
          </div>
        )}
        
        {/* Streaming Content */}
        {isStreaming && streamContent && (
          <div className="space-y-3">
            {/* Show match score immediately when streaming */}
            {property.searchScore !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Match Score:</span>
                <div className={cn(
                  "px-2 py-1 rounded-full text-xs font-bold",
                  property.searchScore >= 90 ? "bg-emerald-500 text-white" :
                  property.searchScore >= 75 ? "bg-green-500 text-white" :
                  property.searchScore >= 60 ? "bg-yellow-500 text-white" :
                  "bg-red-500 text-white"
                )}>
                  {Math.round(property.searchScore)}%
                </div>
              </div>
            )}
            
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>AI is analyzing this property...</span>
            </div>
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 rounded-lg p-4 border border-blue-200/50 dark:border-blue-800/50">
              <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                {displayText}
                {/* Blinking cursor effect */}
                <span className="animate-pulse ml-0.5 bg-blue-500 w-0.5 h-4 inline-block align-text-bottom"></span>
              </p>
            </div>
          </div>
        )}
        
        {/* Generated Explanation */}
        {explanation && (
        <div className="space-y-4">
            {/* Match Score - use property's searchScore or explanation's match_score */}
            {(property.searchScore !== undefined || explanation.match_score !== undefined) && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Match Score:</span>
                <div className={cn(
                  "px-2 py-1 rounded-full text-xs font-bold",
                  (property.searchScore || explanation.match_score || 0) >= 90 ? "bg-emerald-500 text-white" :
                  (property.searchScore || explanation.match_score || 0) >= 75 ? "bg-green-500 text-white" :
                  (property.searchScore || explanation.match_score || 0) >= 60 ? "bg-yellow-500 text-white" :
                  "bg-red-500 text-white"
                )}>
                  {Math.round(property.searchScore || explanation.match_score || 0)}%
                </div>
              </div>
            )}
            
            {/* Positive Points */}
            {explanation.positive_points && explanation.positive_points.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-green-700 dark:text-green-400">
                  ✅ What matches your search:
                </h4>
                {explanation.positive_points.map((point, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <BadgeCheck className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium">{point.point}</p>
                      {point.details && (
                        <p className="text-muted-foreground mt-1">{point.details}</p>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          )}
          
            {/* Negative Points */}
            {explanation.negative_points && explanation.negative_points.length > 0 && (
            <div className="space-y-2">
                <h4 className="text-sm font-medium text-amber-700 dark:text-amber-400">
                  ⚠️ Areas that don't quite match:
                </h4>
                {explanation.negative_points.map((point, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <BadgeX className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium">{point.point}</p>
                      {point.details && (
                        <p className="text-muted-foreground mt-1">{point.details}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Overall Summary */}
            {explanation.overall_summary && (
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-2">📋 Overall Assessment:</h4>
                <p className="text-sm text-muted-foreground">{explanation.overall_summary}</p>
            </div>
          )}
        </div>
        )}
        
        {/* Action Button */}
        {!isLoading && !explanation && !error && (
          <div className="text-center py-4">
            <Button onClick={generateExplanationHandler} variant="outline">
              Generate AI Explanation
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}