"use client"

import { Property } from '@/lib/mock-data'
import { cn, getScoreColor } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'

interface MatchScoreProps {
  property: Property
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function MatchScore({ property, className, size = 'md' }: MatchScoreProps) {
  const score = property.searchScore ?? 0
  const scoreColor = getScoreColor(score)
  
  // Extract the background color class from the combined classes
  const bgColorClass = scoreColor.split(' ')[0]
  
  let sizeClasses
  switch(size) {
    case 'sm':
      sizeClasses = 'text-xs py-0.5 px-1.5'
      break
    case 'lg':
      sizeClasses = 'text-base py-1.5 px-3'
      break
    default:
      sizeClasses = 'text-sm py-1 px-2'
  }
  
  // Extract negative aspect from matchExplanation if present
  let negativeText = ''
  if (property.matchExplanation) {
    const explanation = property.matchExplanation
    const hasNegative = explanation.includes('not addressed') ||
      explanation.includes("doesn't include") ||
      explanation.includes('missing') ||
      explanation.includes('only aspect') ||
      explanation.includes('rather than')
    if (hasNegative) {
      const sentences = explanation.split('. ')
      const negativeIndex = sentences.findIndex(s =>
        s.includes('not addressed') ||
        s.includes("doesn't include") ||
        s.includes('missing') ||
        s.includes('only aspect') ||
        s.includes('rather than')
      )
      if (negativeIndex !== -1) {
        negativeText = sentences.slice(negativeIndex).join('. ')
      }
    }
  }
  
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">AI Match Score</span>
        <span className={cn(
          "font-bold rounded",
          sizeClasses,
          scoreColor
        )}>
          {Math.round(score)}%
        </span>
      </div>
      
      <Progress value={score} className="h-2" /* TODO: custom indicator color if needed */ />
      
      {negativeText && (
        <div className="text-xs text-amber-600 bg-amber-100 rounded px-2 py-1 mt-2">
          <strong>Missing:</strong> {negativeText}
        </div>
      )}
      
      {size === 'lg' && (
        <div className="text-sm text-muted-foreground">
          {score >= 90 ? 'Perfect match for your criteria' :
           score >= 80 ? 'Excellent match for your criteria' :
           score >= 70 ? 'Good match for your criteria' :
           score >= 60 ? 'Decent match for your criteria' :
           score >= 50 ? 'Partial match for your criteria' :
           'Limited match for your criteria'}
        </div>
      )}
    </div>
  )
}