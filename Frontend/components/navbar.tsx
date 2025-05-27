"use client"

import Link from 'next/link'
import { Home, Search } from 'lucide-react'
import { ThemeToggle } from './ui/theme-toggle'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  
  useEffect(() => {
    const handleScroll = () => {
      const isScrolled = window.scrollY > 10
      if (isScrolled !== scrolled) {
        setScrolled(isScrolled)
      }
    }
    
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [scrolled])
  
  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
      scrolled
        ? "bg-background/80 backdrop-blur-md border-b shadow-sm"
        : "bg-transparent"
    )}>
      <div className="container mx-auto flex items-center justify-between h-16 px-4 md:px-6">
        <Link href="/" className="flex items-center space-x-2">
          <Home className="h-6 w-6" />
          <span className="font-bold text-lg">PropMatch</span>
        </Link>
        
        <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
          <Link 
            href="/"
            className="transition-colors hover:text-foreground/80"
          >
            Home
          </Link>
          <Link 
            href="/search"
            className="transition-colors hover:text-foreground/80"
          >
            Search
          </Link>
          <a 
            href="#"
            className="transition-colors hover:text-foreground/80"
          >
            About
          </a>
          <a 
            href="#"
            className="transition-colors hover:text-foreground/80"
          >
            Contact
          </a>
        </nav>
        
        <div className="flex items-center space-x-2">
          <Link href="/search">
            <Button variant="ghost" size="icon" className="hidden sm:flex">
              <Search className="h-5 w-5" />
              <span className="sr-only">Search</span>
            </Button>
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}