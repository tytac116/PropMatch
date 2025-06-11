"use client"

import Link from 'next/link'
import { Home, Search, Menu, X } from 'lucide-react'
import { ThemeToggle } from './ui/theme-toggle'
import { Button } from './ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet'
import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  
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
      <div className="container mx-auto flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center space-x-2">
          <Home className="h-6 w-6" />
          <span className="font-bold text-lg">PropMatch</span>
        </Link>
        
        {/* Desktop Navigation */}
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
          
          {/* Mobile Menu */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Open menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <SheetHeader>
                <SheetTitle className="flex items-center space-x-2">
                  <Home className="h-5 w-5" />
                  <span>PropMatch</span>
                </SheetTitle>
              </SheetHeader>
              <nav className="flex flex-col space-y-4 mt-6">
                <Link 
                  href="/"
                  className="text-lg font-medium transition-colors hover:text-foreground/80 py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Home
                </Link>
                <Link 
                  href="/search"
                  className="text-lg font-medium transition-colors hover:text-foreground/80 py-2 flex items-center space-x-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Search className="h-5 w-5" />
                  <span>Search Properties</span>
                </Link>
                <a 
                  href="#"
                  className="text-lg font-medium transition-colors hover:text-foreground/80 py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  About
                </a>
                <a 
                  href="#"
                  className="text-lg font-medium transition-colors hover:text-foreground/80 py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Contact
                </a>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}