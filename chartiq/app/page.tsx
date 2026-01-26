'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Activity, TrendingUp, AlertTriangle, RefreshCw, Flame, Users, Zap, Bitcoin, Timer } from 'lucide-react'
import { toast } from 'sonner'

interface CryptoNews {
  id: string
  title: string
  snippet: string
  url: string
  source: string
  category: string
  tokens: string
  impactLevel: string
  sentiment: string
  publishedAt: string
  createdAt: string
}

interface CryptoInfluencer {
  id: string
  name: string
  handle: string
  platform: string
  influenceLevel: string
  focus: string
  active: boolean
  posts?: any[]
}

interface CryptoAlert {
  id: string
  title: string
  description: string
  severity: string
  sourceType: string
  tokens: string
  resolved: boolean
  createdAt: string
}

export default function Home() {
  const [news, setNews] = useState<CryptoNews[]>([])
  const [influencers, setInfluencers] = useState<CryptoInfluencer[]>([])
  const [alerts, setAlerts] = useState<CryptoAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('all')

  const fetchData = async () => {
    try {
      setLoading(true)

      const [newsRes, influencersRes, alertsRes] = await Promise.all([
        fetch('/api/crypto/news'),
        fetch('/api/crypto/influencers'),
        fetch('/api/crypto/alerts?unresolved=true')
      ])

      if (newsRes.ok) {
        const data = await newsRes.json()
        setNews(data)
      }

      if (influencersRes.ok) {
        const data = await influencersRes.json()
        setInfluencers(data)
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json()
        setAlerts(data)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerScrape = async () => {
    try {
      toast.loading('Scraping crypto news...')
      const res = await fetch('/api/crypto/scrape', { method: 'POST' })
      const data = await res.json()

      if (data.success) {
        toast.success(`Found ${data.count} new items`)
        await fetchData()
      } else {
        toast.error('Scraping failed')
      }
    } catch (error) {
      toast.error('Error scraping news')
    }
  }

  useEffect(() => {
    fetchData()

    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchData, 2 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const filteredNews = news.filter(item => {
    if (selectedCategory === 'all') return true
    return item.category === selectedCategory
  })

  const activeAlerts = alerts.filter(a => !a.resolved).slice(0, 3)
  const highImpactNews = news.filter(n => n.impactLevel === 'high' || n.impactLevel === 'critical').slice(0, 3)

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-600 text-white'
      case 'high': return 'bg-red-500 text-white'
      case 'medium': return 'bg-orange-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return '📈'
      case 'bearish': return '📉'
      default: return '➡️'
    }
  }

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      defi: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      nft: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
      regulation: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      tech: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      trading: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      general: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
    return colors[category] || colors.general
  }

  const getInfluenceBadge = (level: string) => {
    switch (level) {
      case 'legendary': return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white'
      case 'high': return 'bg-purple-500 text-white'
      case 'medium': return 'bg-blue-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header Widget */}
        <Card className="bg-black/40 backdrop-blur-xl border-purple-500/20 mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Bitcoin className="h-10 w-10 text-orange-400" />
                  <Zap className="h-4 w-4 text-yellow-400 absolute -top-1 -right-1" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">CryptoPulse</h1>
                  <p className="text-xs text-purple-300">Real-time crypto intelligence</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <Timer className="h-4 w-4" />
                  <span>{news[0] ? formatTimeAgo(news[0].createdAt) : 'Just now'}</span>
                </div>
                <Button
                  onClick={triggerScrape}
                  disabled={loading}
                  size="sm"
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-black/30 backdrop-blur-lg border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Flame className="h-5 w-5 text-orange-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{highImpactNews.length}</p>
                  <p className="text-xs text-gray-400">Hot News</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-black/30 backdrop-blur-lg border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-500/20 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{activeAlerts.length}</p>
                  <p className="text-xs text-gray-400">Active Alerts</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-black/30 backdrop-blur-lg border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Users className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{influencers.length}</p>
                  <p className="text-xs text-gray-400">Influencers</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-black/30 backdrop-blur-lg border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{filteredNews.length}</p>
                  <p className="text-xs text-gray-400">Total News</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* News Feed */}
          <Card className="md:col-span-2 bg-black/30 backdrop-blur-lg border-purple-500/20">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Activity className="h-5 w-5 text-orange-400" />
                  Latest Crypto News
                </h2>
                <div className="flex gap-2">
                  {['all', 'defi', 'nft', 'regulation', 'tech', 'trading'].map((cat) => (
                    <Button
                      key={cat}
                      variant={selectedCategory === cat ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory(cat)}
                      className={selectedCategory === cat ? 'bg-orange-500 hover:bg-orange-600' : 'border-purple-500/30'}
                    >
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] pr-4">
                {loading && filteredNews.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin" />
                    Loading crypto news...
                  </div>
                ) : filteredNews.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No news found yet</p>
                    <p className="text-sm mt-2">Click refresh to fetch latest updates</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredNews.map((item) => (
                      <Card key={item.id} className="bg-black/40 border-purple-500/10 hover:border-orange-500/30 transition-all hover:scale-[1.02]">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2 flex-wrap">
                                <Badge className={getImpactColor(item.impactLevel)}>
                                  {item.impactLevel.toUpperCase()}
                                </Badge>
                                <Badge className={getCategoryColor(item.category)}>
                                  {item.category}
                                </Badge>
                                {item.tokens && item.tokens.split(',').slice(0, 3).map(token => (
                                  <Badge key={token} variant="outline" className="border-orange-500/50 text-orange-300">
                                    {token.toUpperCase()}
                                  </Badge>
                                ))}
                                <span className="text-xs text-gray-500">{getSentimentIcon(item.sentiment)}</span>
                              </div>

                              <h3 className="font-semibold text-white mb-2 line-clamp-2">
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="hover:text-orange-400 transition-colors"
                                >
                                  {item.title}
                                </a>
                              </h3>

                              <p className="text-sm text-gray-400 mb-2 line-clamp-2">
                                {item.snippet}
                              </p>

                              <div className="flex items-center gap-3 text-xs text-gray-500">
                                <span>{item.source}</span>
                                <span>•</span>
                                <span>{formatTimeAgo(item.publishedAt)}</span>
                              </div>
                            </div>

                            {item.impactLevel === 'high' || item.impactLevel === 'critical' ? (
                              <Zap className="h-5 w-5 text-yellow-400 animate-pulse flex-shrink-0" />
                            ) : null}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Critical Alerts */}
            <Card className="bg-black/30 backdrop-blur-lg border-red-500/20">
              <CardHeader className="pb-3">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  Critical Alerts
                </h2>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[200px] pr-4">
                  <div className="space-y-3">
                    {activeAlerts.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-4">No active alerts</p>
                    ) : (
                      activeAlerts.map(alert => (
                        <Alert key={alert.id} className="bg-red-950/30 border-red-500/50">
                          <AlertTriangle className="h-4 w-4 text-red-400" />
                          <AlertDescription>
                            <p className="font-medium text-white">{alert.title}</p>
                            <p className="text-sm text-gray-400 mt-1">{alert.description}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge variant="outline" className="border-red-500/50 text-red-300">
                                {alert.sourceType}
                              </Badge>
                              <span className="text-xs text-gray-500">{formatTimeAgo(alert.createdAt)}</span>
                            </div>
                          </AlertDescription>
                        </Alert>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Top Influencers */}
            <Card className="bg-black/30 backdrop-blur-lg border-purple-500/20">
              <CardHeader className="pb-3">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Users className="h-5 w-5 text-purple-400" />
                  Crypto Influencers
                </h2>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[280px] pr-4">
                  <div className="space-y-3">
                    {influencers.slice(0, 10).map(influencer => (
                      <div
                        key={influencer.id}
                        className="p-3 bg-black/40 rounded-lg border border-purple-500/10 hover:border-purple-500/30 transition-all"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white text-xs font-bold">
                              {influencer.name.charAt(0)}
                            </div>
                            <div>
                              <p className="font-medium text-white text-sm">{influencer.name}</p>
                              <p className="text-xs text-gray-400">{influencer.handle}</p>
                            </div>
                          </div>
                          <Badge className={getInfluenceBadge(influencer.influenceLevel)}>
                            {influencer.influenceLevel}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="border-purple-500/30 text-purple-300 text-xs">
                            {influencer.focus}
                          </Badge>
                          <Badge variant="outline" className="border-gray-500/30 text-gray-400 text-xs">
                            {influencer.platform}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Hot Takes */}
            <Card className="bg-black/30 backdrop-blur-lg border-orange-500/20">
              <CardHeader className="pb-3">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Flame className="h-5 w-5 text-orange-400" />
                  Hot Takes
                </h2>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {highImpactNews.map(item => (
                    <div
                      key={item.id}
                      className="p-3 bg-gradient-to-r from-orange-950/50 to-red-950/50 rounded-lg border border-orange-500/20"
                    >
                      <div className="flex items-start gap-2">
                        <Zap className="h-4 w-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white line-clamp-2">
                            {item.title}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            {item.tokens && item.tokens.split(',').slice(0, 2).map(token => (
                              <Badge key={token} variant="outline" className="border-orange-500/50 text-orange-300 text-xs">
                                {token.toUpperCase()}
                              </Badge>
                            ))}
                            <span className="text-xs text-gray-500">{formatTimeAgo(item.publishedAt)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
