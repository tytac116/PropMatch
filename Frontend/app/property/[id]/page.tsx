import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import { getProperty } from '@/lib/api'
import { PropertyViewerWithCache } from '@/components/property-viewer-with-cache'
import { Loader2 } from 'lucide-react'

// Loading component
function PropertyLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
        <p className="text-muted-foreground">Loading property details...</p>
      </div>
    </div>
  )
}

// Property content component
async function PropertyContent({ 
  propertyId, 
  searchTerm 
}: { 
  propertyId: string
  searchTerm?: string 
}) {
  try {
    const property = await getProperty(propertyId)
  
    if (!property) {
      notFound()
    }
    
    // Convert API property to frontend-compatible format for PropertyViewer
    // Use defensive coding to handle potentially missing location data
    const location = property.location || {}
    const frontendProperty = {
      id: property.listing_number,
      title: property.title || `${mapPropertyType(property.type)} ${location.neighborhood ? `in ${location.neighborhood}` : ''}`.trim(),
      description: property.description || '',
      price: property.price || 0,
      currency: property.currency || 'ZAR',
      type: mapPropertyType(property.type),
      bedrooms: property.bedrooms || 0,
      bathrooms: property.bathrooms || 0,
      area: property.area || 0,
      areaUnit: property.areaUnit || 'm²',
      location: {
        address: location.address || '',
        neighborhood: location.neighborhood || '',
        city: location.city || 'Cape Town',
        postalCode: location.postalCode || '',
        country: location.country || 'South Africa'
      },
      images: property.images || [],
      features: property.features || [],
      status: mapPropertyStatus(property.status),
      listedDate: property.listedDate || new Date().toISOString(),
      searchScore: property.searchScore, // Will be enhanced by PropertyViewerWithCache
      matchExplanation: undefined
    }
    
    return <PropertyViewerWithCache 
      property={frontendProperty} 
      searchTerm={searchTerm}
      enableStreaming={!!searchTerm} // Only enable streaming if we have a search term
    />
  } catch (error) {
    console.error('Failed to fetch property:', error)
    notFound()
  }
}

function mapPropertyType(apiType: string): 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse' {
  // Remove enum prefix if present and handle various backend formats
  const cleanType = apiType?.replace('PropertyType.', '').toLowerCase() || ''
  
  const typeMap: Record<string, 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse'> = {
    'house': 'house',
    'apartment': 'apartment',
    'flat': 'apartment',
    'condo': 'condo',
    'villa': 'villa',
    'townhouse': 'townhouse',
    'penthouse': 'apartment'
  }
  return typeMap[cleanType] || 'house'
}

function mapPropertyStatus(apiStatus: string): 'for_sale' | 'for_rent' {
  // Remove enum prefix if present and handle various backend status formats
  const cleanStatus = apiStatus?.replace('PropertyStatus.', '').toLowerCase() || ''
  
  if (cleanStatus.includes('rent') || cleanStatus.includes('to_rent') || cleanStatus.includes('rental')) {
    return 'for_rent'
  }
  // Default to for_sale for sale, for_sale, or any other status
  return 'for_sale'
}

export default async function PropertyPage({ 
  params, 
  searchParams 
}: { 
  params: Promise<{ id: string }>
  searchParams: Promise<{ q?: string }>
}) {
  // Await the params and searchParams as required by Next.js 15
  const resolvedParams = await params
  const resolvedSearchParams = await searchParams
  
  return (
    <Suspense fallback={<PropertyLoading />}>
      <PropertyContent 
        propertyId={resolvedParams.id} 
        searchTerm={resolvedSearchParams.q} 
      />
    </Suspense>
  )
}