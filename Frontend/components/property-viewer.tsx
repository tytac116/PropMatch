'use client'

import { useState } from 'react'
import { Property } from '@/lib/mock-data' // Keep mock Property type for component compatibility
import { Card } from '@/components/ui/card'
import { PropertyFeatures } from '@/components/property-features'
import { MatchScore } from '@/components/match-score'
import { MatchExplanation } from '@/components/match-explanation'
import { Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext } from '@/components/ui/carousel'
import { ImageLightbox } from '@/components/image-lightbox'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Expand } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

export function PropertyViewer({ property, searchTerm, onBack, enableStreaming = false }: { 
  property: Property
  searchTerm?: string 
  onBack?: () => void
  enableStreaming?: boolean
}) {
  const router = useRouter()
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [currentCarouselIndex, setCurrentCarouselIndex] = useState(0)

  // Build back URL to preserve search state
  const getBackUrl = () => {
    if (searchTerm && searchTerm.trim()) {
      // If we have a search term, go back to search results with the query preserved
      return `/search?q=${encodeURIComponent(searchTerm.trim())}&filter=buy`
    }
    // Otherwise, go to home or use router.back()
    return null
  }

  const handleBackClick = () => {
    if (onBack) {
      onBack()
    } else {
      const backUrl = getBackUrl()
      if (backUrl) {
        router.push(backUrl)
      } else {
        router.back()
      }
    }
  }

  const openLightbox = (index: number) => {
    console.log('Opening lightbox at index:', index)
    setLightboxIndex(index)
    setLightboxOpen(true)
  }

  const handleCarouselApi = (api: any) => {
    if (!api) return
    
    // Set initial index
    const initialIndex = api.selectedScrollSnap()
    console.log('Carousel API initialized, initial index:', initialIndex)
    setCurrentCarouselIndex(initialIndex)
    
    // Listen for slide changes
    api.on('select', () => {
      const newIndex = api.selectedScrollSnap()
      console.log('Carousel changed to index:', newIndex)
      setCurrentCarouselIndex(newIndex)
    })
  }

  // Handle empty images array
  const hasImages = property.images && property.images.length > 0
  const displayImages = hasImages ? property.images : ['/placeholder-property.svg']

  return (
    <div className="container mx-auto px-4 py-8">
      <Button
        variant="outline"
        className="mb-6"
        onClick={handleBackClick}
      >
        ← Back to results
      </Button>
      
      <Card className="overflow-hidden">
        <div className="grid lg:grid-cols-2 gap-8 p-6 lg:items-start">
          {/* Left Column - Images and Description */}
          <div className="flex flex-col">
            {/* Image Carousel */}
            <div className="relative w-full mb-6">
              <Carousel className="w-full" setApi={handleCarouselApi}>
                <CarouselContent>
                  {displayImages.map((img, idx) => (
                    <CarouselItem key={idx} className="flex justify-center items-center">
                      <div className="relative group cursor-pointer" onClick={(e) => {
                        e.preventDefault()
                        console.log('Image clicked, current carousel index:', currentCarouselIndex)
                        openLightbox(currentCarouselIndex)
                      }}>
                        <img
                          src={img}
                          alt={`${property.title} photo ${idx + 1}`}
                          className="w-full h-[400px] object-cover rounded-lg transition-transform duration-300 group-hover:scale-[1.02]"
                          onError={(e) => {
                            // Fallback to placeholder on image error
                            const target = e.target as HTMLImageElement
                            target.src = '/placeholder-property.svg'
                          }}
                        />
                        {/* Overlay with expand icon */}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300 rounded-lg flex items-center justify-center">
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/90 rounded-full p-3">
                            <Expand className="h-6 w-6 text-gray-800" />
                          </div>
                        </div>
                      </div>
                    </CarouselItem>
                  ))}
                </CarouselContent>
                {displayImages.length > 1 && (
                  <>
                <CarouselPrevious className="absolute left-2 top-1/2 -translate-y-1/2 z-10" />
                <CarouselNext className="absolute right-2 top-1/2 -translate-y-1/2 z-10" />
                  </>
                )}
              </Carousel>
              
              {/* Image counter */}
              {displayImages.length > 1 && (
              <div className="absolute bottom-4 right-4 bg-black/50 text-white px-2 py-1 rounded text-sm">
                  {currentCarouselIndex + 1} / {displayImages.length}
              </div>
              )}
            </div>

            {/* Description */}
            <div>
              <h2 className="text-2xl font-semibold mb-4">Description</h2>
              <p className="text-muted-foreground leading-relaxed">
                {property.description || 'No description available for this property.'}
              </p>
            </div>
          </div>

          {/* Right Column - Property Details */}
          <div className="space-y-6">
            {/* AI Explanation - only show if we have a search term */}
            {searchTerm && searchTerm.trim() && (
              <MatchExplanation 
                searchTerm={searchTerm} 
                property={{
                  ...property,
                  listing_number: property.id // Map id to listing_number for API compatibility
                } as any} 
                enableStreaming={enableStreaming}
              />
            )}
            
            <div>
              <h1 className="text-3xl font-bold mb-2">{property.title}</h1>
              <p className="text-2xl font-semibold text-primary">
                {formatCurrency(property.price, property.currency)}
              </p>
              <p className="text-muted-foreground mt-1">
                {property.location.address}, {property.location.neighborhood}
              </p>
            </div>
            
            <PropertyFeatures property={property} />
            
            <div className="space-y-4">
              <MatchScore property={property} />
            </div>

            {/* Additional property info */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-3">Property Details</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Property Type:</span>
                  <p className="font-medium capitalize">{property.type}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p className="font-medium capitalize">
                    {property.status === 'for_sale' ? 'For Sale' : 'For Rent'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Area:</span>
                  <p className="font-medium">{property.area} {property.areaUnit}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Listed:</span>
                  <p className="font-medium">
                    {new Date(property.listedDate).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Image Lightbox */}
      <ImageLightbox
        images={displayImages}
        initialIndex={lightboxIndex}
        isOpen={lightboxOpen}
        onClose={() => setLightboxOpen(false)}
        title={property.title}
      />
    </div>
  )
}