import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Brain, TrendingUp, TrendingDown, Target, AlertCircle, RefreshCw } from 'lucide-react'

const SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'BTC-USD', 'ETH-USD']

// Datos simulados para predicciones
const PREDICTION_DATA = {
  'AAPL': { 
    currentPrice: 190.50, 
    svm: 'subida', 
    lstm: 195.50, 
    confidence: 0.78 
  },
  'GOOGL': { 
    currentPrice: 175.20, 
    svm: 'bajada', 
    lstm: 170.20, 
    confidence: 0.65 
  },
  'MSFT': { 
    currentPrice: 420.75, 
    svm: 'subida', 
    lstm: 430.75, 
    confidence: 0.82 
  },
  'TSLA': { 
    currentPrice: 248.90, 
    svm: 'bajada', 
    lstm: 240.90, 
    confidence: 0.71 
  },
  'AMZN': { 
    currentPrice: 178.30, 
    svm: 'subida', 
    lstm: 185.30, 
    confidence: 0.69 
  },
  'BTC-USD': { 
    currentPrice: 67890.50, 
    svm: 'subida', 
    lstm: 70000.50, 
    confidence: 0.75 
  },
  'ETH-USD': { 
    currentPrice: 3456.78, 
    svm: 'bajada', 
    lstm: 3300.78, 
    confidence: 0.68 
  }
}

function PredictionModule({ token }) {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [predictionData, setPredictionData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (selectedSymbol) {
      handlePredict()
    }
  }, [selectedSymbol])

  const handlePredict = () => {
    setLoading(true)
    
    // Simular carga de predicciones
    setTimeout(() => {
      const data = PREDICTION_DATA[selectedSymbol]
      setPredictionData({
        symbol: selectedSymbol,
        currentPrice: data.currentPrice,
        svm: data.svm,
        lstm: data.lstm,
        confidence: data.confidence,
        source: 'offline'
      })
      setLoading(false)
    }, 1200)
  }

  const generatePredictionChart = () => {
    if (!predictionData) return null

    const currentPrice = predictionData.currentPrice
    const lstmPrice = predictionData.lstm
    const days = 7
    const chartData = []

    // Datos históricos simulados
    for (let i = days; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      
      const variation = Math.sin(i * 0.2) * 0.02
      const price = currentPrice * (1 + variation)
      
      chartData.push({
        date: date.toLocaleDateString(),
        price: price.toFixed(2),
        type: 'historical',
        day: -i
      })
    }

    // Predicciones futuras
    for (let i = 1; i <= days; i++) {
      const date = new Date()
      date.setDate(date.getDate() + i)
      
      const progress = i / days
      const targetPrice = lstmPrice
      const price = currentPrice + (targetPrice - currentPrice) * progress
      
      chartData.push({
        date: date.toLocaleDateString(),
        price: price.toFixed(2),
        type: 'prediction',
        day: i
      })
    }

    return chartData
  }

  const PredictionChart = ({ data }) => {
    if (!data || data.length === 0) return null

    const historicalData = data.filter(d => d.type === 'historical')
    const predictionData = data.filter(d => d.type === 'prediction')
    
    const allPrices = data.map(d => parseFloat(d.price))
    const maxPrice = Math.max(...allPrices)
    const minPrice = Math.min(...allPrices)
    const priceRange = maxPrice - minPrice

    return (
      <div className="w-full h-64 bg-gray-50 rounded-lg p-4">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-medium">Predicción de {selectedSymbol} - Próximos 7 días</h4>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-blue-500"></div>
              <span>Histórico</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-red-500 border-dashed border"></div>
              <span>Predicción</span>
            </div>
          </div>
        </div>
        
        <div className="relative h-40 border-l-2 border-b-2 border-gray-300">
          <svg width="100%" height="100%" className="absolute inset-0">
            {/* Línea histórica */}
            <polyline
              fill="none"
              stroke="#3b82f6"
              strokeWidth="2"
              points={historicalData.map((point, index) => {
                const x = (index / (data.length - 1)) * 100
                const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                return `${x}%,${y}%`
              }).join(' ')}
            />
            
            {/* Línea de predicción */}
            <polyline
              fill="none"
              stroke="#ef4444"
              strokeWidth="2"
              strokeDasharray="5,5"
              points={predictionData.map((point, index) => {
                const totalIndex = historicalData.length + index - 1
                const x = (totalIndex / (data.length - 1)) * 100
                const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                return `${x}%,${y}%`
              }).join(' ')}
            />
            
            {/* Punto actual */}
            {(() => {
              const currentIndex = historicalData.length - 1
              const x = (currentIndex / (data.length - 1)) * 100
              const currentPrice = parseFloat(historicalData[historicalData.length - 1].price)
              const y = 100 - ((currentPrice - minPrice) / priceRange) * 100
              return (
                <circle
                  cx={`${x}%`}
                  cy={`${y}%`}
                  r="4"
                  fill="#22c55e"
                  stroke="#fff"
                  strokeWidth="2"
                />
              )
            })()}
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
          <span className="text-green-600 font-medium">Hoy</span>
          <span>{data[data.length - 1]?.date}</span>
        </div>
      </div>
    )
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'Alta'
    if (confidence >= 0.6) return 'Media'
    return 'Baja'
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Predicciones IA</h2>
          <p className="text-gray-600">Modelos de machine learning simulados (Modo Offline)</p>
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
          <Button onClick={handlePredict} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Prediciendo...
              </>
            ) : (
              'Predecir'
            )}
          </Button>
        </div>
      </div>

      {predictionData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Resultados de Predicción */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Predicciones para {predictionData.symbol}
                </span>
                <Badge variant="outline" className="text-green-600 border-green-300">
                  Modo Offline
                </Badge>
              </CardTitle>
              <CardDescription>Resultados simulados de modelos de IA</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Precio Actual */}
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-sm text-gray-600">Precio Actual</div>
                  <div className="text-3xl font-bold text-blue-600">
                    ${predictionData.currentPrice.toFixed(2)}
                  </div>
                </div>

                {/* Predicción SVM */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Modelo SVM</span>
                    <Badge variant={predictionData.svm === 'subida' ? 'default' : 'destructive'}>
                      {predictionData.svm === 'subida' ? 'SUBIDA' : 'BAJADA'}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    {predictionData.svm === 'subida' ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <span>Predicción de dirección del precio</span>
                  </div>
                </div>

                {/* Predicción LSTM */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Modelo LSTM</span>
                    <span className="text-lg font-bold">
                      ${predictionData.lstm.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Target className="h-4 w-4 text-blue-500" />
                    <span>Precio objetivo en 7 días</span>
                  </div>
                  <div className="text-sm">
                    Cambio esperado: 
                    <span className={`ml-1 font-medium ${
                      predictionData.lstm > predictionData.currentPrice ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {predictionData.lstm > predictionData.currentPrice ? '+' : ''}
                      {((predictionData.lstm - predictionData.currentPrice) / predictionData.currentPrice * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>

                {/* Nivel de Confianza */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Nivel de Confianza</span>
                    <span className={`font-bold ${getConfidenceColor(predictionData.confidence)}`}>
                      {getConfidenceLabel(predictionData.confidence)} ({(predictionData.confidence * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        predictionData.confidence >= 0.8 ? 'bg-green-500' :
                        predictionData.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${predictionData.confidence * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Recomendación Final */}
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Recomendación</span>
                    <Badge 
                      variant={predictionData.svm === 'subida' && predictionData.lstm > predictionData.currentPrice ? 'default' : 'destructive'}
                      className="text-sm"
                    >
                      {predictionData.svm === 'subida' && predictionData.lstm > predictionData.currentPrice ? 'COMPRAR' : 'VENDER'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {predictionData.svm === 'subida' && predictionData.lstm > predictionData.currentPrice
                      ? 'Ambos modelos sugieren una tendencia alcista'
                      : 'Los modelos sugieren cautela o tendencia bajista'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gráfico de Predicción */}
          <Card>
            <CardHeader>
              <CardTitle>Gráfico de Predicción</CardTitle>
              <CardDescription>Evolución histórica y predicción futura simulada</CardDescription>
            </CardHeader>
            <CardContent>
              <PredictionChart data={generatePredictionChart()} />
              
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Aviso Importante</span>
                </div>
                <p className="text-xs text-yellow-700 mt-1">
                  Las predicciones mostradas son simuladas para fines demostrativos. 
                  En un entorno real, consulte siempre con un asesor financiero.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Generando predicciones...</span>
        </div>
      )}
    </div>
  )
}

export default PredictionModule

