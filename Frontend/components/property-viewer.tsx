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
import { Expand, MapPin } from 'lucide-react'
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
    <div className="container mx-auto px-4 py-6 lg:py-8">
      <Button
        variant="outline"
        className="mb-4 lg:mb-6"
        onClick={handleBackClick}
      >
        ← Back to results
      </Button>
      
      <Card className="overflow-hidden">
        {/* Mobile Layout - AI Analysis First */}
        <div className="lg:hidden">
          <div className="p-4 space-y-4">
            {/* AI Explanation - Mobile First */}
            {searchTerm && searchTerm.trim() && (
              <MatchExplanation 
                searchTerm={searchTerm} 
                property={{
                  ...property,
                  listing_number: property.id
                } as any} 
                enableStreaming={enableStreaming}
              />
            )}
            
            {/* Match Score - Mobile */}
            {searchTerm && searchTerm.trim() && (
              <div className="bg-card border rounded-lg p-4">
                <MatchScore property={property} size="lg" />
              </div>
            )}

            {/* Image Carousel - Mobile */}
            <div className="relative w-full">
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
                          className="w-full h-[250px] object-cover rounded-lg transition-transform duration-300 group-hover:scale-[1.02]"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement
                            target.src = '/placeholder-property.svg'
                          }}
                        />
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
              
              {displayImages.length > 1 && (
                <div className="absolute bottom-4 right-4 bg-black/50 text-white px-2 py-1 rounded text-sm">
                  {currentCarouselIndex + 1} / {displayImages.length}
                </div>
              )}
            </div>

            {/* Property Title & Price - Mobile */}
            <div className="bg-card border rounded-lg p-4">
              <h1 className="text-xl font-bold mb-2">{property.title}</h1>
              <p className="text-xl font-bold text-primary mb-2">
                {formatCurrency(property.price, property.currency)}
              </p>
              <div className="flex items-center text-muted-foreground">
                <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                <span className="text-sm">{property.location.address}, {property.location.neighborhood}</span>
              </div>
            </div>
            
            {/* Property Features - Mobile */}
            <div className="bg-card border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">Features & Amenities</h3>
              <PropertyFeatures property={property} />
            </div>

            {/* Property Details Grid - Mobile */}
            <div className="bg-card border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">Property Information</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Property Type</span>
                  <p className="font-semibold capitalize text-sm">{property.type}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Status</span>
                  <p className="font-semibold capitalize text-sm">
                    {property.status === 'for_sale' ? 'For Sale' : 'For Rent'}
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Floor Area</span>
                  <p className="font-semibold text-sm">{property.area} {property.areaUnit}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Listed Date</span>
                  <p className="font-semibold text-sm">
                    {new Date(property.listedDate).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Description - Mobile */}
            <div className="bg-card border rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-3">Property Description</h2>
              <p className="text-muted-foreground leading-relaxed text-sm">
                {property.description || 'No description available for this property.'}
              </p>
            </div>
          </div>
        </div>

        {/* Desktop Layout */}
        <div className="hidden lg:block">
          <div className="grid lg:grid-cols-2 gap-6 lg:gap-8 p-4 lg:p-6">
            {/* Left Column - Images, Price, and Features */}
            <div className="flex flex-col space-y-4 lg:space-y-6">
              {/* Image Carousel */}
              <div className="relative w-full">
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
                            className="w-full h-[300px] lg:h-[400px] object-cover rounded-lg transition-transform duration-300 group-hover:scale-[1.02]"
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

              {/* Property Title & Price */}
              <div className="bg-card border rounded-lg p-4 lg:p-6">
                <h1 className="text-xl lg:text-2xl xl:text-3xl font-bold mb-3">{property.title}</h1>
                <p className="text-xl lg:text-2xl xl:text-3xl font-bold text-primary mb-2">
                  {formatCurrency(property.price, property.currency)}
                </p>
                <div className="flex items-center text-muted-foreground">
                  <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="text-sm lg:text-base">{property.location.address}, {property.location.neighborhood}</span>
                </div>
              </div>
              
              {/* Property Features */}
              <div className="bg-card border rounded-lg p-4 lg:p-6">
                <h3 className="text-lg font-semibold mb-4">Features & Amenities</h3>
                <PropertyFeatures property={property} />
              </div>

              {/* Property Details Grid */}
              <div className="bg-card border rounded-lg p-4 lg:p-6">
                <h3 className="text-lg font-semibold mb-4">Property Information</h3>
                <div className="grid grid-cols-2 gap-3 lg:gap-4">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Property Type</span>
                    <p className="font-semibold capitalize text-sm lg:text-base">{property.type}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <p className="font-semibold capitalize text-sm lg:text-base">
                      {property.status === 'for_sale' ? 'For Sale' : 'For Rent'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Floor Area</span>
                    <p className="font-semibold text-sm lg:text-base">{property.area} {property.areaUnit}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">Listed Date</span>
                    <p className="font-semibold text-sm lg:text-base">
                      {new Date(property.listedDate).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - AI Content and Description */}
            <div className="flex flex-col space-y-4 lg:space-y-6">
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
              
              {/* Match Score - only show if we have a search term */}
              {searchTerm && searchTerm.trim() && (
                <div className="bg-card border rounded-lg p-4 lg:p-6">
                  <MatchScore property={property} size="lg" />
                </div>
              )}

              {/* Description */}
              <div className="bg-card border rounded-lg p-4 lg:p-6">
                <h2 className="text-lg font-semibold mb-4">Property Description</h2>
                <p className="text-muted-foreground leading-relaxed text-sm lg:text-base">
                  {property.description || 'No description available for this property.'}
                </p>
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