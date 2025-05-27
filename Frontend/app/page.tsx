"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Home, Search, Building } from 'lucide-react'
import { AnimatedBackground } from '@/components/animated-background'
import { SearchBar } from '@/components/search-bar'
import { Button } from '@/components/ui/button'
import { suggestionQueries } from '@/lib/mock-data'

export default function HomePage() {
  const router = useRouter()
  const [searchType, setSearchType] = useState<'buy' | 'rent'>('buy')

  const handleSearch = (query: string, filter: 'buy' | 'rent') => {
    // Update the URL with the search query and filter
    const searchParams = new URLSearchParams()
    searchParams.set('q', query)
    searchParams.set('filter', filter)
    router.push(`/search?${searchParams.toString()}`)
  }

  return (
    <>
      <AnimatedBackground className="min-h-[90vh] flex flex-col items-center justify-center">
        <div className="container mx-auto px-4 md:px-6 py-24 space-y-12 text-center">
          <div className="space-y-4 max-w-3xl mx-auto text-center">
            <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-500 dark:from-white dark:to-gray-300 animate-gradient text-center">
              Find Your Perfect Cape Town Property with AI
            </h1>
            <p className="text-gray-700 dark:text-gray-300 md:text-xl max-w-2xl mx-auto">
              Describe what you're looking for in natural language, and our AI will find properties that match your needs.
            </p>
          </div>

          <div className="w-full max-w-3xl mx-auto">
            <SearchBar 
              onSearch={handleSearch} 
              suggestions={suggestionQueries}
            />
          </div>
        </div>
      </AnimatedBackground>

      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center space-y-4 mb-12">
            <h2 className="text-2xl md:text-3xl font-bold">How PropMatch Works</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Our AI-powered search understands what you're looking for, even when you describe it in your own words.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            <div className="flex flex-col items-center text-center p-4">
              <div className="bg-primary/10 p-3 rounded-lg mb-4">
                <Search className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Natural Language Search</h3>
              <p className="text-muted-foreground">
                Search for properties exactly how you'd describe them to a friend. No need to learn complicated filters.
              </p>
            </div>
            <div className="flex flex-col items-center text-center p-4">
              <div className="bg-primary/10 p-3 rounded-lg mb-4">
                <Home className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">AI Match Score</h3>
              <p className="text-muted-foreground">
                We rank properties by how well they match your description, with a clear percentage score.
              </p>
            </div>
            <div className="flex flex-col items-center text-center p-4">
              <div className="bg-primary/10 p-3 rounded-lg mb-4">
                <Building className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Detailed Explanations</h3>
              <p className="text-muted-foreground">
                Understand exactly why a property matches your search with our AI-generated explanations.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24 bg-muted/30">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center space-y-4 mb-12">
            <h2 className="text-2xl md:text-3xl font-bold">Discover Cape Town Properties</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From beachfront villas to city apartments, find your perfect Cape Town home.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3 mb-8 max-w-6xl mx-auto">
            <div className="relative group overflow-hidden rounded-lg bg-muted h-60">
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" style={{ backgroundImage: `url('https://images.pexels.com/photos/2581922/pexels-photo-2581922.jpeg')` }}></div>
              <div className="absolute inset-0 bg-black/30 flex items-end p-6">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">Beachfront Living</h3>
                  <Button variant="outline" className="text-white bg-transparent border-white hover:bg-white hover:text-black">
                    Explore
                  </Button>
                </div>
              </div>
            </div>
            <div className="relative group overflow-hidden rounded-lg bg-muted h-60">
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" style={{ backgroundImage: `url('https://images.pexels.com/photos/2119713/pexels-photo-2119713.jpeg')` }}></div>
              <div className="absolute inset-0 bg-black/30 flex items-end p-6">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">City Apartments</h3>
                  <Button variant="outline" className="text-white bg-transparent border-white hover:bg-white hover:text-black">
                    Explore
                  </Button>
                </div>
              </div>
            </div>
            <div className="relative group overflow-hidden rounded-lg bg-muted h-60">
              <div className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110" style={{ backgroundImage: `url('https://images.pexels.com/photos/1396122/pexels-photo-1396122.jpeg')` }}></div>
              <div className="absolute inset-0 bg-black/30 flex items-end p-6">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">Family Homes</h3>
                  <Button variant="outline" className="text-white bg-transparent border-white hover:bg-white hover:text-black">
                    Explore
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <Button 
              className="px-6"
              onClick={() => router.push('/search')}
            >
              <Search className="h-4 w-4 mr-2" />
              Browse All Properties
            </Button>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
            <div className="space-y-6">
              <h2 className="text-2xl md:text-3xl font-bold">Ready to find your dream home in Cape Town?</h2>
              <p className="text-muted-foreground">
                Whether you're looking to buy or rent, our AI-powered search makes finding the perfect property easier than ever.
              </p>
              <Button size="lg" onClick={() => router.push('/search')}>Start Your Search</Button>
            </div>
            <div className="relative">
              <div className="absolute -top-6 -left-6 w-24 h-24 bg-primary/10 rounded-lg"></div>
              <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-primary/10 rounded-lg"></div>
              <div className="relative bg-muted rounded-lg p-6 shadow-lg">
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                  <div className="bg-background rounded-md p-4 shadow-sm">
                    <p className="text-sm font-mono">
                      <span className="text-blue-500">{">"}</span> Find me a 3-bedroom house in Constantia with a garden and pool, close to good schools.
                    </p>
                  </div>
                  <div className="bg-primary/5 rounded-md p-4">
                    <p className="text-sm">
                      I found 5 properties matching your search. Here's the best match:
                    </p>
                    <p className="text-sm font-medium mt-2">
                      Spacious Family Home in Constantia with large garden, pool, and walking distance to top schools.
                    </p>
                    <div className="flex items-center mt-2">
                      <div className="bg-emerald-500 text-white text-xs font-bold px-2 py-0.5 rounded">
                        92% Match
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}