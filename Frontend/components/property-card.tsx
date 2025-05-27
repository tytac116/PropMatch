"use client"

import Image from 'next/image'
import { useState } from 'react'
import Link from 'next/link'
import { BedDouble, Bath, Move, MapPin, Tag, Calendar, Home } from 'lucide-react'
import { cn, formatCurrency, getScoreColor, truncateText } from '@/lib/utils'
import { Property } from '@/lib/mock-data'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

interface PropertyCardProps {
  property: Property
  showScore?: boolean
  className?: string
}

export function PropertyCard({ property, showScore = true, className }: PropertyCardProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  const nextImage = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImageIndex((prevIndex) => 
      prevIndex === property.images.length - 1 ? 0 : prevIndex + 1
    )
  }

  const prevImage = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setCurrentImageIndex((prevIndex) => 
      prevIndex === 0 ? property.images.length - 1 : prevIndex - 1
    )
  }
  
  const formattedPrice = formatCurrency(property.price, property.currency)
  
  // Debug: Log score and color for troubleshooting
  const score = property.searchScore || 85
  const scoreColor = getScoreColor(score)
  if (typeof window !== 'undefined' && score === 77) {
    console.log(`Property ${property.title}: score=${score}, color=${scoreColor}`)
  }

  return (
    <Link href={`/property/${property.id}`}>
      <Card className={cn(
        "overflow-hidden transition-all duration-300 hover:shadow-lg",
        "transform hover:-translate-y-1",
        className
      )}>
        <div className="relative aspect-[16/10] overflow-hidden">
          <Image 
            src={property.images[currentImageIndex]} 
            alt={property.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 hover:scale-105"
            priority
          />
          
          {/* Image navigation */}
          {property.images.length > 1 && (
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
                {property.images.map((_, idx) => (
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
                {score}% Match
              </div>
            </div>
          )}
        </div>

        <CardContent className="p-4">
          <h3 className="font-semibold text-lg line-clamp-1 mb-1">{property.title}</h3>
          
          <div className="flex items-center text-sm text-muted-foreground mb-3">
            <MapPin className="h-3.5 w-3.5 mr-1" />
            <span className="line-clamp-1">{property.location.neighborhood}, {property.location.city}</span>
          </div>
          
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {truncateText(property.description, 120)}
          </p>
          
          <div className="mb-4 flex justify-between">
            <div className="text-lg font-bold">
              {formattedPrice}
              {property.status === 'for_rent' && <span className="text-sm font-normal text-muted-foreground"> / month</span>}
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-2">
              <BedDouble className="h-4 w-4 mb-1" />
              <span>{property.bedrooms} {property.bedrooms === 1 ? 'Bed' : 'Beds'}</span>
            </div>
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-2">
              <Bath className="h-4 w-4 mb-1" />
              <span>{property.bathrooms} {property.bathrooms === 1 ? 'Bath' : 'Baths'}</span>
            </div>
            <div className="flex flex-col items-center bg-muted/40 rounded-md p-2">
              <Move className="h-4 w-4 mb-1" />
              <span>{property.area} {property.areaUnit}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}