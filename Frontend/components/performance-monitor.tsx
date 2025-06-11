"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { getCacheStats, getHealthStatus } from '@/lib/api'
import { Activity, Clock, Zap, AlertCircle, CheckCircle } from 'lucide-react'

interface PerformanceStats {
  searchLatency?: number
  cacheHitRate?: number
  totalRequests?: number
  backendHealth?: boolean
  redisConnected?: boolean
}

interface PerformanceMonitorProps {
  searchTime?: number
  className?: string
}

export function PerformanceMonitor({ searchTime, className }: PerformanceMonitorProps) {
  const [stats, setStats] = useState<PerformanceStats>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [cacheStats, healthStatus] = await Promise.all([
          getCacheStats(),
          getHealthStatus()
        ])

        setStats({
          searchLatency: searchTime,
          cacheHitRate: cacheStats.cache_statistics.hit_rate_percentage,
          totalRequests: cacheStats.cache_statistics.total_requests,
          backendHealth: healthStatus.components.openai_client && healthStatus.components.redis_cache,
          redisConnected: cacheStats.cache_statistics.redis_connected
        })
      } catch (error) {
        console.error('Failed to fetch performance stats:', error)
        setStats({
          searchLatency: searchTime,
          backendHealth: false,
          redisConnected: false
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [searchTime])

  if (process.env.NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING !== 'true') {
    return null
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Performance Monitor
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading stats...</div>
        ) : (
          <>
            {/* Search Performance */}
            {stats.searchLatency && (
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <Clock className="h-3 w-3" />
                  Last Search
                </span>
                <Badge variant={stats.searchLatency < 3000 ? 'default' : 'secondary'}>
                  {stats.searchLatency.toFixed(0)}ms
                </Badge>
              </div>
            )}

            {/* Cache Performance */}
            {stats.cacheHitRate !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <Zap className="h-3 w-3" />
                  Cache Hit Rate
                </span>
                <Badge variant={stats.cacheHitRate > 50 ? 'default' : 'secondary'}>
                  {stats.cacheHitRate.toFixed(1)}%
                </Badge>
              </div>
            )}

            {/* Total Requests */}
            {stats.totalRequests !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Requests</span>
                <Badge variant="outline">
                  {stats.totalRequests}
                </Badge>
              </div>
            )}

            {/* Backend Status */}
            <div className="flex items-center justify-between">
              <span className="text-sm">Backend Status</span>
              <div className="flex items-center gap-1">
                {stats.backendHealth ? (
                  <CheckCircle className="h-3 w-3 text-green-500" />
                ) : (
                  <AlertCircle className="h-3 w-3 text-red-500" />
                )}
                <Badge variant={stats.backendHealth ? 'default' : 'destructive'}>
                  {stats.backendHealth ? 'Healthy' : 'Error'}
                </Badge>
              </div>
            </div>

            {/* Redis Status */}
            <div className="flex items-center justify-between">
              <span className="text-sm">Cache Status</span>
              <div className="flex items-center gap-1">
                {stats.redisConnected ? (
                  <CheckCircle className="h-3 w-3 text-green-500" />
                ) : (
                  <AlertCircle className="h-3 w-3 text-red-500" />
                )}
                <Badge variant={stats.redisConnected ? 'default' : 'destructive'}>
                  {stats.redisConnected ? 'Connected' : 'Offline'}
                </Badge>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
} 