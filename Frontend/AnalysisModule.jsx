import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { TrendingUp, TrendingDown, BarChart3, AlertCircle, RefreshCw } from 'lucide-react'

const SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'BTC-USD', 'ETH-USD']

// Datos simulados realistas
const MARKET_DATA = {
  'AAPL': { price: 190.50, change: 3.21, changePercent: 1.72, volume: 85000000 },
  'GOOGL': { price: 175.20, change: -1.80, changePercent: -1.02, volume: 23456789 },
  'MSFT': { price: 420.75, change: 5.25, changePercent: 1.27, volume: 34567890 },
  'TSLA': { price: 248.90, change: -8.10, changePercent: -3.15, volume: 67890123 },
  'AMZN': { price: 178.30, change: 3.45, changePercent: 1.97, volume: 28901234 },
  'BTC-USD': { price: 67890.50, change: 1234.50, changePercent: 1.85, volume: 12345678 },
  'ETH-USD': { price: 3456.78, change: -89.12, changePercent: -2.51, volume: 9876543 }
}

function AnalysisModule({ token }) {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [analysisData, setAnalysisData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (selectedSymbol) {
      handleAnalyze()
    }
  }, [selectedSymbol])

  const handleAnalyze = () => {
    setLoading(true)
    
    // Simular carga de datos
    setTimeout(() => {
      const data = MARKET_DATA[selectedSymbol]
      setAnalysisData({
        symbol: selectedSymbol,
        price: data.price,
        change: data.change,
        changePercent: data.changePercent,
        volume: data.volume,
        source: 'offline'
      })
      setLoading(false)
    }, 800)
  }

  const generateSimpleChart = () => {
    if (!analysisData) return null

    const basePrice = analysisData.price
    const days = 30
    const chartData = []

    for (let i = days; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      
      // Generar precio con variación basada en el símbolo
      const variation = (Math.sin(i * 0.1) + Math.random() * 0.4 - 0.2) * 0.05
      const price = basePrice * (1 + variation)
      
      chartData.push({
        date: date.toLocaleDateString(),
        price: price.toFixed(2),
        day: i
      })
    }

    return chartData
  }

  const SimpleChart = ({ data }) => {
    if (!data || data.length === 0) return null

    const maxPrice = Math.max(...data.map(d => parseFloat(d.price)))
    const minPrice = Math.min(...data.map(d => parseFloat(d.price)))
    const priceRange = maxPrice - minPrice

    return (
      <div className="w-full h-64 bg-gray-50 rounded-lg p-4">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-medium">Precio de {selectedSymbol} - Últimos 30 días</h4>
          <div className="text-sm text-gray-600">
            Max: ${maxPrice.toFixed(2)} | Min: ${minPrice.toFixed(2)}
          </div>
        </div>
        
        <div className="relative h-40 border-l-2 border-b-2 border-gray-300">
          <svg width="100%" height="100%" className="absolute inset-0">
            {/* Línea del gráfico */}
            <polyline
              fill="none"
              stroke={analysisData.change >= 0 ? "#22c55e" : "#ef4444"}
              strokeWidth="2"
              points={data.map((point, index) => {
                const x = (index / (data.length - 1)) * 100
                const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                return `${x}%,${y}%`
              }).join(' ')}
            />
            
            {/* Puntos en la línea */}
            {data.map((point, index) => {
              if (index % 5 === 0) {
                const x = (index / (data.length - 1)) * 100
                const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                return (
                  <circle
                    key={index}
                    cx={`${x}%`}
                    cy={`${y}%`}
                    r="3"
                    fill={analysisData.change >= 0 ? "#22c55e" : "#ef4444"}
                  />
                )
              }
              return null
            })}
          </svg>
          
          {/* Etiquetas del eje Y */}
          <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-12">
            <span>${maxPrice.toFixed(2)}</span>
            <span>${((maxPrice + minPrice) / 2).toFixed(2)}</span>
            <span>${minPrice.toFixed(2)}</span>
          </div>
        </div>
        
        {/* Etiquetas del eje X */}
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>{data[0]?.date}</span>
          <span>{data[Math.floor(data.length / 2)]?.date}</span>
          <span>{data[data.length - 1]?.date}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Análisis de Mercado</h2>
          <p className="text-gray-600">Análisis técnico y fundamental de activos (Modo Offline)</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {SYMBOLS.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Analizando...
              </>
            ) : (
              'Analizar'
            )}
          </Button>
        </div>
      </div>

      {analysisData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Información del Activo */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{analysisData.symbol}</span>
                <Badge variant="outline" className="text-green-600 border-green-300">
                  Modo Offline
                </Badge>
              </CardTitle>
              <CardDescription>Información del activo simulada</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Precio Actual</span>
                  <span className="text-2xl font-bold">${analysisData.price.toFixed(2)}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Cambio</span>
                  <div className="flex items-center gap-1">
                    {analysisData.change >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`font-medium ${analysisData.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${Math.abs(analysisData.change).toFixed(2)} ({Math.abs(analysisData.changePercent).toFixed(2)}%)
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Volumen</span>
                  <span className="font-medium">{analysisData.volume.toLocaleString()}</span>
                </div>

                <div className="pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">RSI</span>
                      <div className="font-medium">65.4</div>
                    </div>
                    <div>
                      <span className="text-gray-600">MACD</span>
                      <div className="font-medium text-green-600">+2.1</div>
                    </div>
                    <div>
                      <span className="text-gray-600">SMA 20</span>
                      <div className="font-medium">${(analysisData.price * 0.98).toFixed(2)}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">SMA 50</span>
                      <div className="font-medium">${(analysisData.price * 0.95).toFixed(2)}</div>
                    </div>
                  </div>
                </div>

                {/* Recomendación */}
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Recomendación</span>
                    <Badge variant={analysisData.change >= 0 ? "default" : "destructive"}>
                      {analysisData.change >= 0 ? "COMPRAR" : "VENDER"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gráfico de Precios */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Gráfico de Precios
              </CardTitle>
              <CardDescription>Evolución del precio simulada</CardDescription>
            </CardHeader>
            <CardContent>
              <SimpleChart data={generateSimpleChart()} />
            </CardContent>
          </Card>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Cargando análisis...</span>
        </div>
      )}
    </div>
  )
}

export default AnalysisModule

