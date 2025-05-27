"use client"

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

interface AnimatedBackgroundProps {
  className?: string
  children?: React.ReactNode
}

export function AnimatedBackground({ className, children }: AnimatedBackgroundProps) {
  const [scrollY, setScrollY] = useState(0)
  const [mounted, setMounted] = useState(false)
  
  // Handle scroll events
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY)
    }
    
    window.addEventListener('scroll', handleScroll, { passive: true })
    setMounted(true)
    
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])
  
  // Calculate parallax effect
  const backgroundPositionY = mounted ? -(scrollY * 0.15) : 0
  const opacity = mounted ? Math.max(1 - scrollY / 700, 0.2) : 1
  
  return (
    <div className={cn("relative overflow-hidden", className)}>
      {/* Background gradient with parallax effect */}
      <div 
        className="absolute inset-0 transition-opacity duration-300 pointer-events-none"
        style={{ 
          opacity,
        }}
      >
        <div 
          className="absolute inset-0 bg-gradient-to-b from-blue-500/20 to-blue-800/40 dark:from-blue-900/40 dark:to-blue-950/60"
          style={{
            transform: `translateY(${backgroundPositionY}px)`,
          }}
        />
        
        {/* Cape Town skyline silhouette */}
        <div 
          className="absolute bottom-0 left-0 right-0 h-48 bg-[url('https://images.pexels.com/photos/1388030/pexels-photo-1388030.jpeg')] bg-bottom bg-cover"
          style={{
            WebkitMaskImage: 'linear-gradient(to top, black, transparent)',
            maskImage: 'linear-gradient(to top, black, transparent)',
            transform: `translateY(${backgroundPositionY * 0.5}px)`,
          }}
        />
      </div>
      
      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-20 -left-20 w-72 h-72 bg-purple-500/20 dark:bg-purple-700/20 rounded-full blur-3xl animate-blob"></div>
        <div className="absolute top-60 -right-20 w-72 h-72 bg-yellow-500/20 dark:bg-yellow-700/20 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-20 left-1/3 w-72 h-72 bg-blue-500/20 dark:bg-blue-700/20 rounded-full blur-3xl animate-blob animation-delay-4000"></div>
      </div>
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  )
}