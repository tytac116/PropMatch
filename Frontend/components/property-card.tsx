"use client"

import Image from 'next/image'
import { useState } from 'react'
import Link from 'next/link'
import { BedDouble, Bath, Move, MapPin, Tag, Calendar, Home, Loader2 } from 'lucide-react'
import { cn, formatCurrency, getScoreColor, truncateText } from '@/lib/utils'
import { Property } from '@/lib/mock-data'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

interface PropertyCardProps {
  property: Property
  showScore?: boolean
  className?: string
  searchTerm?: string
}

export function PropertyCard({ property, showScore = true, className, searchTerm }: PropertyCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [imageError, setImageError] = useState(false)
  const [isClicked, setIsClicked] = useState(false)

  // Use placeholder if no images or current image failed to load
  const hasImages = property.images && property.images.length > 0 && !imageError
  const currentImage = hasImages ? property.images[currentImageIndex] : '/placeholder-property.svg'

  // Build URL with search context if available
  const propertyUrl = searchTerm && searchTerm.trim() 
    ? `/property/${property.id}?q=${encodeURIComponent(searchTerm.trim())}`
    : `/property/${property.id}`

  const handleCardClick = () => {
    setIsClicked(true)
    // Reset after a short delay to prevent stuck state
    setTimeout(() => setIsClicked(false), 2000)
  }

  const nextImage = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (hasImages) {
    setCurrentImageIndex((prevIndex) => 
      prevIndex === property.images.length - 1 ? 0 : prevIndex + 1
    )
    }
  }

  const prevImage = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (hasImages) {
    setCurrentImageIndex((prevIndex) => 
      prevIndex === 0 ? property.images.length - 1 : prevIndex - 1
    )
    }
  }

  const handleImageError = () => {
    console.log('Image failed to load:', property.images?.[currentImageIndex])
    setImageError(true)
  }
  
  const formattedPrice = formatCurrency(property.price, property.currency)
  
  // Debug: Log score and color for troubleshooting
  const score = property.searchScore || 85
  const scoreColor = getScoreColor(score)
  if (typeof window !== 'undefined' && score === 77) {
    console.log(`Property ${property.title}: score=${score}, color=${scoreColor}`)
  }

  return (
    <Link href={propertyUrl} onClick={handleCardClick}>
      <Card className={cn(
        "overflow-hidden transition-all duration-300 hover:shadow-lg cursor-pointer h-full flex flex-col",
        "transform hover:-translate-y-1 active:scale-[0.98] active:shadow-md",
        isClicked && "scale-[0.98] shadow-md opacity-75",
        className
      )}>
        <div className="relative aspect-[16/10] overflow-hidden">
          {/* Loading overlay */}
          {isClicked && (
            <div className="absolute inset-0 bg-black/20 flex items-center justify-center z-50">
              <div className="bg-white/90 rounded-full p-2">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            </div>
          )}
          
          <Image 
            src={currentImage} 
            alt={property.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 hover:scale-105"
            priority
            onError={handleImageError}
          />
          
          {/* Image navigation - only show if we have multiple real images */}
          {hasImages && property.images.length > 1 && (
            <>
              <button 
                onClick={prevImage} 
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/30 hover:bg-black/60 text-white p-1 rounded-full"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>
              <button 
                onClick={nextImage} 
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/30 hover:bg-black/60 text-white p-1 rounded-full"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                {property.images.slice(0, 5).map((_, idx) => (
                  <div 
                    key={idx} 
                    className={cn(
                      "w-2 h-2 rounded-full transition-colors",
                      idx === currentImageIndex 
                        ? "bg-white" 
                        : "bg-white/40"
                    )}
                  />
                ))}
                {property.images.length > 5 && (
                  <div className="text-white text-xs bg-black/50 rounded-full px-1">
                    +{property.images.length - 5}
                  </div>
                )}
              </div>
            </>
          )}
          
          {/* Property status badge */}
          <div className="absolute top-2 left-2">
            <Badge className="text-xs font-medium px-2 py-1">
              {property.status === 'for_sale' ? 'For Sale' : 'For Rent'}
            </Badge>
          </div>
          
          {/* Search score */}
          {showScore && (
            <div className="absolute top-2 right-2">
              <div className={cn(
                "text-xs font-bold px-2 py-1 rounded-md shadow-sm",
                scoreColor
              )}>
                {Math.round(score)}% Match
              </div>
            </div>
          )}
        </div>

        <CardContent className="p-3 sm:p-4 flex-1 flex flex-col">
          <h3 className="font-semibold text-base sm:text-lg line-clamp-1 mb-1">{property.title}</h3>
          
          <div className="flex items-center text-xs sm:text-sm text-muted-foreground mb-2 sm:mb-3">
            <MapPin className="h-3 w-3 sm:h-3.5 sm:w-3.5 mr-1 flex-shrink-0" />
            <span className="line-clamp-1">{property.location.neighborhood}, {property.location.city}</span>
          </div>
          
          <p className="text-xs sm:text-sm text-muted-foreground mb-2 sm:mb-3 line-clamp-2 flex-1">
            {truncateText(property.description, 120)}
          </p>
          
          <div className="mb-3 sm:mb-4 flex justify-between">
            <div className="text-base sm:text-lg font-bold">
              {formattedPrice}
              {property.status === 'for_rent' && <span className="text-xs sm:text-sm font-normal text-muted-foreground"> / month</span>}
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-1 sm:gap-2 text-sm mt-auto">
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-1.5 sm:p-2 h-14 sm:h-16 justify-center">
              <BedDouble className="h-3.5 w-3.5 sm:h-4 sm:w-4 mb-1 flex-shrink-0" />
              <span className="text-center leading-tight text-xs">{property.bedrooms} {property.bedrooms === 1 ? 'Bed' : 'Beds'}</span>
            </div>
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-1.5 sm:p-2 h-14 sm:h-16 justify-center">
              <Bath className="h-3.5 w-3.5 sm:h-4 sm:w-4 mb-1 flex-shrink-0" />
              <span className="text-center leading-tight text-xs">
                {property.bathrooms % 1 === 0 ? property.bathrooms : property.bathrooms.toFixed(1)} {property.bathrooms === 1 ? 'Bath' : 'Baths'}
              </span>
            </div>
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-1.5 sm:p-2 h-14 sm:h-16 justify-center">
              <Move className="h-3.5 w-3.5 sm:h-4 sm:w-4 mb-1 flex-shrink-0" />
              <span className="text-center leading-tight text-xs">{property.area} {property.areaUnit}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}