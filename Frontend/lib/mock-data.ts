import { StaticImageData } from 'next/image';

export interface Property {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  type: 'house' | 'apartment' | 'condo' | 'villa' | 'townhouse';
  bedrooms: number;
  bathrooms: number;
  area: number;
  areaUnit: string;
  location: {
    address: string;
    neighborhood: string;
    city: string;
    postalCode: string;
    country: string;
  };
  images: string[];
  features: string[];
  status: 'for_sale' | 'for_rent';
  listedDate: string;
  searchScore?: number;
  matchExplanation?: string;
}

export interface SearchResult {
  properties: Property[];
  searchTerm: string;
  totalResults: number;
}

export const suggestionQueries = [
  "Modern 2-bedroom apartment in Sea Point with ocean views",
  "Family home with garden in Constantia close to schools",
  "Secure apartment in Cape Town CBD walking distance to restaurants",
  "Beachfront property in Camps Bay with private pool",
  "Affordable studio near UCT for students",
  "Luxury villa in Clifton with panoramic views of the ocean"
];

export const mockProperties: Property[] = [
  {
    id: "prop-001",
    title: "Modern Sea Point Apartment",
    description: "Beautiful 2-bedroom apartment with stunning ocean views in Sea Point. This recently renovated property features an open floor plan, high ceilings, and a large balcony perfect for watching sunsets over the Atlantic Ocean. Walking distance to promenade and local restaurants.",
    price: 2500000,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 2,
    bathrooms: 2,
    area: 110,
    areaUnit: "m²",
    location: {
      address: "15 Ocean View Drive, Apt 7B",
      neighborhood: "Sea Point",
      city: "Cape Town",
      postalCode: "8005",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/1918291/pexels-photo-1918291.jpeg",
      "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg",
      "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg"
    ],
    features: ["Ocean View", "Security", "Balcony", "Pool", "Gym", "Parking"],
    status: "for_sale",
    listedDate: "2023-11-15",
    searchScore: 95,
    matchExplanation: "This property strongly matches your search for 'modern apartment in Sea Point with ocean views' because it is a contemporary 2-bedroom apartment located directly in Sea Point with unobstructed views of the Atlantic Ocean. The recently renovated interior features modern finishes throughout. The property's proximity to the Sea Point Promenade and local amenities adds to its appeal. The only aspect not addressed is specific interior design details beyond the mention of high ceilings and open floor plan."
  },
  {
    id: "prop-002",
    title: "Luxury Clifton Villa",
    description: "Spectacular villa in exclusive Clifton with panoramic ocean views. This 4-bedroom luxury property features a private pool, designer kitchen, and multiple entertainment areas. Floor-to-ceiling windows showcase the breathtaking views of the Atlantic Ocean and Twelve Apostles mountain range.",
    price: 45000000,
    currency: "ZAR",
    type: "villa",
    bedrooms: 4,
    bathrooms: 5,
    area: 450,
    areaUnit: "m²",
    location: {
      address: "10 Clifton Road",
      neighborhood: "Clifton",
      city: "Cape Town",
      postalCode: "8005",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/32870/pexels-photo.jpg",
      "https://images.pexels.com/photos/2724749/pexels-photo-2724749.jpeg",
      "https://images.pexels.com/photos/2119713/pexels-photo-2119713.jpeg"
    ],
    features: ["Ocean View", "Private Pool", "Security", "Garden", "Smart Home", "Wine Cellar", "Home Theater"],
    status: "for_sale",
    listedDate: "2023-09-20",
    searchScore: 98,
    matchExplanation: "This property perfectly matches your search for 'luxury villa in Clifton with panoramic views of the ocean' as it is a high-end villa located directly in Clifton featuring spectacular panoramic ocean views. The property offers 4 bedrooms and 5 bathrooms spread across 450 m² of living space with floor-to-ceiling windows designed to maximize the Atlantic Ocean vistas. Additional luxury amenities include a private pool, designer kitchen, wine cellar, and home theater."
  },
  {
    id: "prop-003",
    title: "Constantia Family Home",
    description: "Spacious family home in Constantia with beautiful garden and mountain views. Located in a quiet cul-de-sac close to top schools and Constantia Village shopping center. Features 4 bedrooms, study, pool, and established garden.",
    price: 8500000,
    currency: "ZAR",
    type: "house",
    bedrooms: 4,
    bathrooms: 3,
    area: 280,
    areaUnit: "m²",
    location: {
      address: "12 Oak Lane",
      neighborhood: "Constantia",
      city: "Cape Town",
      postalCode: "7806",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/1396122/pexels-photo-1396122.jpeg",
      "https://images.pexels.com/photos/259588/pexels-photo-259588.jpeg",
      "https://images.pexels.com/photos/1080721/pexels-photo-1080721.jpeg"
    ],
    features: ["Garden", "Pool", "Security", "Study", "Double Garage", "Mountain Views"],
    status: "for_sale",
    listedDate: "2023-10-05",
    searchScore: 92,
    matchExplanation: "This property strongly matches your search for 'family home with garden in Constantia close to schools' as it is a 4-bedroom house in the Constantia neighborhood with a beautiful established garden. It's located in a quiet cul-de-sac specifically mentioned as being close to top schools and Constantia Village shopping center. The property offers family-friendly features including a study, pool, and double garage with a total living area of 280 m². The only aspect not directly addressed is the specific types of schools nearby."
  },
  {
    id: "prop-004",
    title: "Cape Town CBD Apartment",
    description: "Secure modern apartment in the heart of Cape Town CBD. Walking distance to restaurants, cafes, and attractions. Features 1 bedroom, open-plan living area, and balcony with city views. 24-hour security and basement parking included.",
    price: 12000,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 1,
    bathrooms: 1,
    area: 65,
    areaUnit: "m²",
    location: {
      address: "905 The Apartments, 40 Long Street",
      neighborhood: "City Center",
      city: "Cape Town",
      postalCode: "8001",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/1457842/pexels-photo-1457842.jpeg",
      "https://images.pexels.com/photos/275484/pexels-photo-275484.jpeg",
      "https://images.pexels.com/photos/1643384/pexels-photo-1643384.jpeg"
    ],
    features: ["Security", "Balcony", "City Views", "Parking", "Elevator", "Gym"],
    status: "for_rent",
    listedDate: "2023-11-01",
    searchScore: 90,
    matchExplanation: "This property strongly matches your search for 'secure apartment in Cape Town CBD walking distance to restaurants' as it is a modern apartment located directly in the Cape Town CBD with explicitly mentioned 24-hour security features. The listing specifically notes it is within walking distance to restaurants, cafes, and attractions. The apartment offers 1 bedroom with an open-plan living area and city views from the balcony. The property includes basement parking which adds to the security aspect you requested."
  },
  {
    id: "prop-005",
    title: "Student Studio near UCT",
    description: "Affordable studio apartment in Rondebosch, perfect for UCT students. Just a 10-minute walk to the University of Cape Town main campus. The unit is fully furnished and includes utilities in the rental price. Secure complex with communal garden and study area.",
    price: 7500,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 0,
    bathrooms: 1,
    area: 35,
    areaUnit: "m²",
    location: {
      address: "20 Main Road, Unit 5",
      neighborhood: "Rondebosch",
      city: "Cape Town",
      postalCode: "7700",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/439227/pexels-photo-439227.jpeg",
      "https://images.pexels.com/photos/1082355/pexels-photo-1082355.jpeg",
      "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg"
    ],
    features: ["Furnished", "Security", "WiFi", "Utilities Included", "Study Area", "Communal Garden"],
    status: "for_rent",
    listedDate: "2023-10-25",
    searchScore: 95,
    matchExplanation: "This property perfectly matches your search for 'affordable studio near UCT for students' as it is specifically marketed as an affordable studio apartment for UCT students. Located in Rondebosch, it's just a 10-minute walk to the University of Cape Town main campus. At 7,500 ZAR per month with utilities included, it offers good value. Additional student-friendly features include full furnishing, WiFi, a communal study area, and security. The 35 m² space is efficiently designed for a single student's needs."
  },
  {
    id: "prop-006",
    title: "Camps Bay Beachfront Villa",
    description: "Stunning beachfront property in Camps Bay with uninterrupted ocean views and direct beach access. This luxury 5-bedroom villa features a private infinity pool, multiple entertainment areas, and state-of-the-art kitchen. Perfect for luxurious beach living or high-end vacation rentals.",
    price: 55000000,
    currency: "ZAR",
    type: "villa",
    bedrooms: 5,
    bathrooms: 6,
    area: 550,
    areaUnit: "m²",
    location: {
      address: "5 Victoria Road",
      neighborhood: "Camps Bay",
      city: "Cape Town",
      postalCode: "8005",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/2581922/pexels-photo-2581922.jpeg",
      "https://images.pexels.com/photos/53610/large-home-residential-house-architecture-53610.jpeg",
      "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg"
    ],
    features: ["Beachfront", "Private Pool", "Security", "Smart Home", "Home Theater", "Wine Cellar", "Staff Quarters"],
    status: "for_sale",
    listedDate: "2023-08-15",
    searchScore: 97,
    matchExplanation: "This property excellently matches your search for 'beachfront property in Camps Bay with private pool' as it is literally on the beachfront in Camps Bay with explicitly mentioned direct beach access. The listing features a private infinity pool overlooking the ocean. With 5 bedrooms and 6 bathrooms across 550 m², the property offers ample space. Additional luxury amenities include multiple entertainment areas, a state-of-the-art kitchen, home theater, wine cellar, and staff quarters. The property is ideal for both luxury living and high-end vacation rentals."
  },
  {
    id: "prop-007",
    title: "Green Point Modern Apartment",
    description: "Contemporary 2-bedroom apartment in Green Point with partial sea views and mountain vistas. Walking distance to V&A Waterfront and Green Point Park. Features open-plan living, modern finishes, and a small balcony. Building has 24/7 security and underground parking.",
    price: 15000,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 2,
    bathrooms: 2,
    area: 85,
    areaUnit: "m²",
    location: {
      address: "15 Main Road, Apt 301",
      neighborhood: "Green Point",
      city: "Cape Town",
      postalCode: "8051",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/1743228/pexels-photo-1743228.jpeg",
      "https://images.pexels.com/photos/1648776/pexels-photo-1648776.jpeg",
      "https://images.pexels.com/photos/276724/pexels-photo-276724.jpeg"
    ],
    features: ["Partial Sea View", "Mountain View", "Security", "Balcony", "Parking", "Elevator"],
    status: "for_rent",
    listedDate: "2023-11-05",
    searchScore: 80,
    matchExplanation: "This property partially matches your search for 'modern apartment with ocean views' as it is a contemporary 2-bedroom apartment with partial (not full) sea views. Located in Green Point rather than directly on the ocean, it does offer some water vistas along with mountain views. The apartment features modern design elements including open-plan living and contemporary finishes. Additional amenities include 24/7 security, underground parking, and a small balcony. While it's within walking distance to V&A Waterfront, it's not directly oceanfront property."
  },
  {
    id: "prop-008",
    title: "Observatory Student Apartment",
    description: "Comfortable 1-bedroom apartment in Observatory, perfect for students or young professionals. Close to UCT medical campus and main campus. The unit comes partially furnished with basic appliances and has good security. Communal laundry facilities available in the building.",
    price: 8500,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 1,
    bathrooms: 1,
    area: 45,
    areaUnit: "m²",
    location: {
      address: "42 Lower Main Road, Unit 7",
      neighborhood: "Observatory",
      city: "Cape Town",
      postalCode: "7925",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/2029731/pexels-photo-2029731.jpeg",
      "https://images.pexels.com/photos/1454806/pexels-photo-1454806.jpeg",
      "https://images.pexels.com/photos/2062431/pexels-photo-2062431.jpeg"
    ],
    features: ["Partially Furnished", "Security", "Communal Laundry", "Close to UCT", "WiFi Ready"],
    status: "for_rent",
    listedDate: "2023-10-30",
    searchScore: 85,
    matchExplanation: "This property mostly matches your search for 'affordable accommodation near UCT' as it is a 1-bedroom apartment close to both UCT medical and main campuses. Located in Observatory, it's in a neighborhood popular with students. At 8,500 ZAR per month, it's relatively affordable for the area. The unit comes partially furnished with basic appliances, saving on initial setup costs. While not a studio as you might have specified, the 45 m² space is compact and efficient for a single student or young professional. Security features and communal laundry add convenience."
  },
  {
    id: "prop-009",
    title: "Basic Woodstock Flat",
    description: "Simple 1-bedroom flat in Woodstock. Basic accommodation with essential amenities. Needs some renovation but offers affordable living in an up-and-coming area. Close to public transport and local shops.",
    price: 6500,
    currency: "ZAR",
    type: "apartment",
    bedrooms: 1,
    bathrooms: 1,
    area: 40,
    areaUnit: "m²",
    location: {
      address: "78 Victoria Road, Unit 2",
      neighborhood: "Woodstock",
      city: "Cape Town",
      postalCode: "7925",
      country: "South Africa"
    },
    images: [
      "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg",
      "https://images.pexels.com/photos/2062431/pexels-photo-2062431.jpeg",
      "https://images.pexels.com/photos/1454806/pexels-photo-1454806.jpeg"
    ],
    features: ["Basic Amenities", "Public Transport", "Affordable"],
    status: "for_rent",
    listedDate: "2023-11-10",
    searchScore: 52,
    matchExplanation: "This property partially matches your search criteria as it provides basic accommodation in Woodstock. While it offers affordable rent at 6,500 ZAR per month, the property needs renovation and only provides essential amenities. The location has good public transport access but may not meet higher-end requirements you might be looking for."
  }
];

// Utility function to simulate AI search based on query
export const searchProperties = (query: string, filter: 'buy' | 'rent' | 'all' = 'all'): SearchResult => {
  // Convert filter to status
  const statusFilter = filter === 'buy' ? 'for_sale' : filter === 'rent' ? 'for_rent' : null;
  
  // Filter properties by status if filter is applied
  let filtered = [...mockProperties];
  if (statusFilter) {
    filtered = filtered.filter(property => property.status === statusFilter);
  }

  // If no query provided, return all properties with default scores
  if (!query.trim()) {
    const propertiesWithScores = filtered.map(property => ({
      ...property,
      searchScore: property.searchScore || 85 // Default score for browsing
    }));
    
    return {
      properties: propertiesWithScores,
      searchTerm: '',
      totalResults: propertiesWithScores.length
    };
  }
  
  // Apply mock search scores based on query keywords
  const scoredProperties = filtered.map(property => {
    // This is a simple mock of AI scoring that would normally be done by backend
    const keywords = query.toLowerCase().split(' ');
    
    // Count matches in title, description, features, location
    let matches = 0;
    let totalFactors = 0;
    
    // Check title (high importance)
    const titleWords = property.title.toLowerCase();
    keywords.forEach(word => {
      if (word.length > 3 && titleWords.includes(word)) matches += 3;
    });
    totalFactors += 3;
    
    // Check neighborhood (high importance)
    const neighborhood = property.location.neighborhood.toLowerCase();
    keywords.forEach(word => {
      if (word.length > 3 && neighborhood.includes(word)) matches += 3;
    });
    totalFactors += 3;
    
    // Check description (medium importance)
    const desc = property.description.toLowerCase();
    keywords.forEach(word => {
      if (word.length > 3 && desc.includes(word)) matches += 2;
    });
    totalFactors += 2;
    
    // Check features (medium importance)
    const features = property.features.join(' ').toLowerCase();
    keywords.forEach(word => {
      if (word.length > 3 && features.includes(word)) matches += 2;
    });
    totalFactors += 2;
    
    // Calculate score percentage
    const score = Math.min(100, Math.floor((matches / totalFactors) * 100));
    
    // Add some randomization to simulate AI variability (but within reasonable bounds)
    const finalScore = Math.min(100, Math.max(50, score + (Math.random() * 30 - 10)));
    
    return {
      ...property,
      searchScore: Math.round(finalScore)
    };
  });
  
  // Sort by score (highest first)
  const sortedProperties = scoredProperties.sort((a, b) => 
    (b.searchScore || 0) - (a.searchScore || 0)
  );
  
  return {
    properties: sortedProperties,
    searchTerm: query,
    totalResults: sortedProperties.length
  };
};