"use client"

import { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

interface AnimatedSearchLoaderProps {
  searchQuery: string
  className?: string
}

export function AnimatedSearchLoader({ searchQuery, className }: AnimatedSearchLoaderProps) {
  const [displayText, setDisplayText] = useState('')
  const [currentPhase, setCurrentPhase] = useState(0)
  const [showSpinner, setShowSpinner] = useState(false)
  const typewriterRef = useRef<number | null>(null)
  const phaseTimeoutRef = useRef<number | null>(null)

  const phases = [
    `Searching for: ${searchQuery}`,
    'Analyzing properties with AI...',
    'Looking harder...',
    'Almost there...',
    'Finding the perfect matches...'
  ]

  useEffect(() => {
    // Start with the first phase
    setCurrentPhase(0)
    setDisplayText('')
    setShowSpinner(false)
    
    const typeText = (text: string, phaseIndex: number) => {
      let index = 0
      setDisplayText('')
      
      const typeChar = () => {
        if (index < text.length) {
          setDisplayText(text.slice(0, index + 1))
          index++
          typewriterRef.current = window.setTimeout(typeChar, 50) // Moderate typing speed
        } else {
          // Text is fully typed, wait before next phase or show spinner
          if (phaseIndex === 0) {
            // After typing the search query, wait 2 seconds then move to next phase
            phaseTimeoutRef.current = window.setTimeout(() => {
              if (phaseIndex + 1 < phases.length) {
                setCurrentPhase(phaseIndex + 1)
              } else {
                setShowSpinner(true)
              }
            }, 2000)
          } else if (phaseIndex < phases.length - 1) {
            // Wait 3 seconds before next encouraging message
            phaseTimeoutRef.current = window.setTimeout(() => {
              setCurrentPhase(phaseIndex + 1)
            }, 3000)
          } else {
            // Last phase, show spinner
            setShowSpinner(true)
          }
        }
      }
      
      typeChar()
    }

    return () => {
      if (typewriterRef.current) {
        clearTimeout(typewriterRef.current)
      }
      if (phaseTimeoutRef.current) {
        clearTimeout(phaseTimeoutRef.current)
      }
    }
  }, [searchQuery])

  // Start typing when phase changes
  useEffect(() => {
    if (currentPhase < phases.length) {
      typeText(phases[currentPhase], currentPhase)
    }
  }, [currentPhase])

  const typeText = (text: string, phaseIndex: number) => {
    // Clear any existing timeouts
    if (typewriterRef.current) {
      clearTimeout(typewriterRef.current)
    }
    if (phaseTimeoutRef.current) {
      clearTimeout(phaseTimeoutRef.current)
    }

    let index = 0
    setDisplayText('')
    
    const typeChar = () => {
      if (index < text.length) {
        setDisplayText(text.slice(0, index + 1))
        index++
        typewriterRef.current = window.setTimeout(typeChar, 50)
      } else {
        // Text is fully typed
        if (phaseIndex === 0) {
          // After typing the search query, wait 2 seconds then move to next phase
          phaseTimeoutRef.current = window.setTimeout(() => {
            if (phaseIndex + 1 < phases.length) {
              setCurrentPhase(phaseIndex + 1)
            }
          }, 2000)
        } else if (phaseIndex < phases.length - 1) {
          // Wait 3 seconds before next encouraging message
          phaseTimeoutRef.current = window.setTimeout(() => {
            setCurrentPhase(phaseIndex + 1)
          }, 3000)
        } else {
          // Last phase, show spinner
          setShowSpinner(true)
        }
      }
    }
    
    typeChar()
  }

  return (
    <div className={cn("py-12 flex flex-col items-center justify-center", className)}>
      <div className="text-center space-y-4 max-w-md">
        <div className="text-lg font-medium min-h-[1.5rem] flex items-center justify-center">
          <span className="mr-2">{displayText}</span>
          {!showSpinner && (
            <span className="animate-pulse bg-primary/80 w-0.5 h-5 inline-block"></span>
          )}
        </div>
        
        {showSpinner && (
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="w-6 h-6 text-primary animate-spin" />
            <span className="text-muted-foreground">Still searching...</span>
          </div>
        )}
        
        <div className="text-sm text-muted-foreground">
          Using AI to find the best property matches
        </div>
      </div>
    </div>
  )
} 