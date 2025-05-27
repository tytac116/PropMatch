"use client"

import { Property } from '@/lib/mock-data'
import { cn, formatDate } from '@/lib/utils'
import { 
  BedDouble, Bath, Move, Home, Calendar, 
  Check, Landmark, Shield, Trees, Car 
} from 'lucide-react'

interface PropertyFeaturesProps {
  property: Property
  className?: string
}

export function PropertyFeatures({ property, className }: PropertyFeaturesProps) {
  const featureIcons: Record<string, React.ReactNode> = {
    "Ocean View": <Landmark className="h-4 w-4" />,
    "Security": <Shield className="h-4 w-4" />,
    "Garden": <Trees className="h-4 w-4" />,
    "Parking": <Car className="h-4 w-4" />,
    "Private Pool": <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M2 12h20"/><path d="M2 7h20"/><path d="M2 17h20"/><path d="M4 5v18"/><path d="M20 5v18"/></svg>,
    "Balcony": <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M4 12h16"/><path d="M2 8h20a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"/><path d="M7 8v13"/><path d="M17 8v13"/></svg>,
  }
  
  return (
    <div className={cn("space-y-6", className)}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex flex-col p-3 border rounded-lg">
          <span className="text-muted-foreground text-sm mb-1">Property Type</span>
          <div className="flex items-center">
            <Home className="h-4 w-4 mr-2 text-primary" />
            <span className="capitalize">{property.type}</span>
          </div>
        </div>
        <div className="flex flex-col p-3 border rounded-lg">
          <span className="text-muted-foreground text-sm mb-1">Bedrooms</span>
          <div className="flex items-center">
            <BedDouble className="h-4 w-4 mr-2 text-primary" />
            <span>{property.bedrooms}</span>
          </div>
        </div>
        <div className="flex flex-col p-3 border rounded-lg">
          <span className="text-muted-foreground text-sm mb-1">Bathrooms</span>
          <div className="flex items-center">
            <Bath className="h-4 w-4 mr-2 text-primary" />
            <span>{property.bathrooms}</span>
          </div>
        </div>
        <div className="flex flex-col p-3 border rounded-lg">
          <span className="text-muted-foreground text-sm mb-1">Floor Area</span>
          <div className="flex items-center">
            <Move className="h-4 w-4 mr-2 text-primary" />
            <span>{property.area} {property.areaUnit}</span>
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold mb-3">Features</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {property.features.map((feature, index) => (
            <div key={index} className="flex items-center p-2 border rounded-lg">
              {featureIcons[feature] || <Check className="h-4 w-4 mr-2 text-primary" />}
              <span className="text-sm">{feature}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="flex flex-wrap gap-4 text-sm">
        <div className="flex items-center">
          <Calendar className="h-4 w-4 mr-1 text-muted-foreground" />
          <span>Listed on {formatDate(property.listedDate)}</span>
        </div>
      </div>
    </div>
  )
}