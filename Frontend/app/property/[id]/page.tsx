import { notFound } from 'next/navigation'
import { mockProperties } from '@/lib/mock-data'
import { PropertyViewer } from '@/components/property-viewer'

// This function tells Next.js which property IDs should be pre-rendered at build time
export async function generateStaticParams() {
  return mockProperties.map((property) => ({
    id: property.id,
  }))
}

export default function PropertyPage({ params, searchParams }: { 
  params: { id: string }
  searchParams: { q?: string }
}) {
  const property = mockProperties.find(p => p.id === params.id)
  
  if (!property) {
    notFound()
  }
  
  return <PropertyViewer property={property} searchTerm={searchParams.q} />
}