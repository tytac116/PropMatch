"use client"

import { Property } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { BadgeCheck, BadgeX } from 'lucide-react'

interface MatchExplanationProps {
  property: Property
  searchTerm: string
  className?: string
}

export function MatchExplanation({ property, searchTerm, className }: MatchExplanationProps) {
  if (!property.matchExplanation) return null
  
  // Extract keywords from search term (words longer than 3 chars)
  const keywords = searchTerm
    .toLowerCase()
    .split(' ')
    .filter(word => word.length > 3)
  
  // Highlight explanation text with matches
  const highlightText = (text: string) => {
    if (keywords.length === 0) return text
    
    let highlightedText = text
    
    // Replace keywords with highlighted version
    keywords.forEach(keyword => {
      // Use word boundaries to match whole words
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi')
      highlightedText = highlightedText.replace(
        regex, 
        match => `<span class="bg-primary/10 text-primary font-medium rounded px-1">${match}</span>`
      )
    })
    
    return <div dangerouslySetInnerHTML={{ __html: highlightedText }} />
  }
  
  // Split explanation into positive and negative aspects
  // This is a simple implementation - in a real app this would be from the AI backend
  const explanation = property.matchExplanation
  const hasNegative = explanation.includes("not addressed") || 
                      explanation.includes("doesn't include") || 
                      explanation.includes("missing") ||
                      explanation.includes("only aspect") ||
                      explanation.includes("rather than")
  
  let positiveText = explanation
  let negativeText = ""
  
  if (hasNegative) {
    // Find a sentence mentioning negative aspects
    const sentences = explanation.split('. ')
    const negativeIndex = sentences.findIndex(s => 
      s.includes("not addressed") || 
      s.includes("doesn't include") || 
      s.includes("missing") ||
      s.includes("only aspect") ||
      s.includes("rather than")
    )
    
    if (negativeIndex !== -1) {
      positiveText = sentences.slice(0, negativeIndex).join('. ') + '.'
      negativeText = sentences.slice(negativeIndex).join('. ')
    }
  }
  
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-6 space-y-4">
        <h3 className="text-lg font-semibold flex items-center">
          <span>AI Match Explanation</span>
          <span className="text-muted-foreground ml-2 text-sm font-normal">
            (for "{searchTerm}")
          </span>
        </h3>
        
        <div className="space-y-4">
          {positiveText && (
            <div className="space-y-2">
              <div className="flex items-start">
                <BadgeCheck className="h-5 w-5 text-emerald-500 mr-2 mt-0.5 flex-shrink-0" />
                <div className="text-sm">{highlightText(positiveText)}</div>
              </div>
            </div>
          )}
          
          {negativeText && (
            <div className="space-y-2">
              <div className="flex items-start">
                <BadgeX className="h-5 w-5 text-amber-500 mr-2 mt-0.5 flex-shrink-0" />
                <div className="text-sm">{highlightText(negativeText)}</div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}