/**
 * PropMatch API Service Layer
 * Connects frontend to real backend APIs
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Property {
  id: string
  listing_number: string
  url?: string
  title: string
  description: string
  price: number
  currency: string
  type: string
  status: string
  bedrooms: number
  bathrooms: number
  area: number
  areaUnit: string
  garages?: number
  parking?: number
  features: string[]
  location: {
    address: string
    neighborhood: string
    city: string
    postalCode?: string
    country: string
  }
  points_of_interest: Array<{
    name: string
    category: string
    distance: number
    distance_str: string
  }>
  searchScore?: number
  scoring_breakdown?: {
    vector_score_raw?: number
    bm25_contribution?: number
    ai_score?: number
    final_score?: number
    scoring_method?: string
  }
  listedDate: string
  images: string[]
}

export interface SearchRequest {
  query: string
  page_size?: number
  page?: number
}

export interface SearchResponse {
  query: string
  total_results: number
  properties: Property[]
  timing: {
    vector_search_ms: number
    bm25_calculation_ms: number
    hybrid_scoring_ms: number
    ai_rerank_ms: number
    total_ms: number
  }
  hybrid_search: boolean
  message: string
}

export interface ExplanationPoint {
  point: string
  details: string
}

export interface PropertyExplanation {
  search_query: string
  listing_number: string
  property_title: string
  match_score: number
  positive_points: ExplanationPoint[]
  negative_points: ExplanationPoint[]
  overall_summary: string
  cached: boolean
}

export interface ExplanationRequest {
  search_query: string
  listing_number: string
}

// API Error handling
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

// Generic API request helper
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  }

  try {
    const response = await fetch(url, { ...defaultOptions, ...options })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    // Network or other errors
    throw new APIError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      error
    )
  }
}

/**
 * Search Properties API
 */
export async function searchProperties(request: SearchRequest): Promise<SearchResponse> {
  return apiRequest<SearchResponse>('/api/v1/hybrid-test/hybrid-search/', {
    method: 'POST',
    body: JSON.stringify({
      query: request.query,
      limit: request.page_size || 10
    })
  })
}

/**
 * Get Property by Listing Number API
 */
export async function getProperty(listingNumber: string): Promise<Property | null> {
  try {
    return await apiRequest<Property>(`/api/v1/properties/${listingNumber}`)
  } catch (error) {
    if (error instanceof APIError && error.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Generate Property Explanation API
 */
export async function generateExplanation(request: ExplanationRequest): Promise<PropertyExplanation> {
  return apiRequest<PropertyExplanation>('/api/v1/explanations/generate/', {
    method: 'POST',
    body: JSON.stringify(request)
  })
}

/**
 * Stream Property Explanation API
 */
export async function* streamExplanation(
  searchQuery: string,
  listingNumber: string
): AsyncGenerator<{
  type: 'start' | 'chunk' | 'complete' | 'error' | 'cached'
  content?: string
  explanation?: PropertyExplanation
  cached?: boolean
  message?: string
}> {
  const url = `${API_BASE_URL}/api/v1/explanations/stream/${listingNumber}`
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ search_query: searchQuery })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new APIError('Failed to get response reader')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // Process complete lines
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6) // Remove 'data: '
            
            if (data === '[DONE]') {
              return
            }

            try {
              const parsed = JSON.parse(data)
              yield parsed
            } catch (e) {
              console.warn('Failed to parse SSE data:', data)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    throw new APIError(
      `Streaming error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      error
    )
  }
}

/**
 * Get API Health Status
 */
export async function getHealthStatus(): Promise<{
  status: string
  service: string
  components: Record<string, boolean>
}> {
  return apiRequest('/api/v1/explanations/health/')
}

/**
 * Get Cache Statistics
 */
export async function getCacheStats(): Promise<{
  cache_statistics: {
    cache_hits: number
    cache_misses: number
    total_requests: number
    hit_rate_percentage: number
    redis_connected: boolean
  }
  service_status: {
    explanation_service_initialized: boolean
    streaming_enabled: boolean
  }
}> {
  return apiRequest('/api/v1/explanations/cache/stats/')
}

/**
 * Performance monitoring utilities
 */
export class PerformanceMonitor {
  private static measurements: Map<string, number> = new Map()

  static start(key: string): void {
    this.measurements.set(key, performance.now())
  }

  static end(key: string): number {
    const start = this.measurements.get(key)
    if (start === undefined) {
      console.warn(`Performance measurement '${key}' was not started`)
      return 0
    }
    
    const duration = performance.now() - start
    this.measurements.delete(key)
    return duration
  }

  static measure<T>(key: string, fn: () => Promise<T>): Promise<T & { __duration: number }> {
    return new Promise(async (resolve, reject) => {
      this.start(key)
      try {
        const result = await fn()
        const duration = this.end(key)
        resolve({ ...result, __duration: duration } as T & { __duration: number })
      } catch (error) {
        this.end(key)
        reject(error)
      }
    })
  }
} 