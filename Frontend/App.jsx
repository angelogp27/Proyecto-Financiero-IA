import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  PieChart,
  Activity,
  Brain,
  Newspaper,
  Shield,
  Settings,
  User,
  LogIn,
  LogOut,
  Home,
  Briefcase,
  LineChart,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ExternalLink,
  RefreshCw,
  Target
} from 'lucide-react'
import './App.css'

// Datos simulados
const SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'BTC-USD', 'ETH-USD']

const MARKET_DATA = {
  'AAPL': { price: 190.50, change: 3.21, changePercent: 1.72, volume: 85000000 },
  'GOOGL': { price: 175.20, change: -1.80, changePercent: -1.02, volume: 23456789 },
  'MSFT': { price: 420.75, change: 5.25, changePercent: 1.27, volume: 34567890 },
  'TSLA': { price: 248.90, change: -8.10, changePercent: -3.15, volume: 67890123 },
  'AMZN': { price: 178.30, change: 3.45, changePercent: 1.97, volume: 28901234 },
  'BTC-USD': { price: 67890.50, change: 1234.50, changePercent: 1.85, volume: 12345678 },
  'ETH-USD': { price: 3456.78, change: -89.12, changePercent: -2.51, volume: 9876543 }
}

const PREDICTION_DATA = {
  'AAPL': { svm: 'subida', lstm: 195.50, confidence: 0.78 },
  'GOOGL': { svm: 'bajada', lstm: 170.20, confidence: 0.65 },
  'MSFT': { svm: 'subida', lstm: 430.75, confidence: 0.82 },
  'TSLA': { svm: 'bajada', lstm: 240.90, confidence: 0.71 },
  'AMZN': { svm: 'subida', lstm: 185.30, confidence: 0.69 },
  'BTC-USD': { svm: 'subida', lstm: 70000.50, confidence: 0.75 },
  'ETH-USD': { svm: 'bajada', lstm: 3300.78, confidence: 0.68 }
}

// Componente de Análisis Simplificado
function AnalysisModule() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [loading, setLoading] = useState(false)

  const data = MARKET_DATA[selectedSymbol]

  const handleAnalyze = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 1000)
  }

  const generateSimpleChart = () => {
    const basePrice = data.price
    const days = 30
    const chartData = []

    for (let i = days; i >= 0; i--) {
      const variation = (Math.sin(i * 0.1) + Math.random() * 0.4 - 0.2) * 0.05
      const price = basePrice * (1 + variation)
      chartData.push({
        day: i,
        price: price.toFixed(2)
      })
    }

    return chartData
  }

  const chartData = generateSimpleChart()
  const maxPrice = Math.max(...chartData.map(d => parseFloat(d.price)))
  const minPrice = Math.min(...chartData.map(d => parseFloat(d.price)))
  const priceRange = maxPrice - minPrice

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Análisis de Mercado</h2>
          <p className="text-gray-600">Análisis técnico y fundamental de activos</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Información del Activo */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{selectedSymbol}</span>
              <Badge variant="outline" className="text-green-600 border-green-300">
                Modo Offline
              </Badge>
            </CardTitle>
            <CardDescription>Información del activo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Precio Actual</span>
                <span className="text-2xl font-bold">${data.price.toFixed(2)}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Cambio</span>
                <div className="flex items-center gap-1">
                  {data.change >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  <span className={`font-medium ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${Math.abs(data.change).toFixed(2)} ({Math.abs(data.changePercent).toFixed(2)}%)
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Volumen</span>
                <span className="font-medium">{data.volume.toLocaleString()}</span>
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
                    <div className="font-medium">${(data.price * 0.98).toFixed(2)}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">SMA 50</span>
                    <div className="font-medium">${(data.price * 0.95).toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Recomendación</span>
                  <Badge variant={data.change >= 0 ? "default" : "destructive"}>
                    {data.change >= 0 ? "COMPRAR" : "VENDER"}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Gráfico Simple */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Gráfico de Precios
            </CardTitle>
            <CardDescription>Evolución del precio - Últimos 30 días</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full h-64 bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-medium">Precio de {selectedSymbol}</h4>
                <div className="text-sm text-gray-600">
                  Max: ${maxPrice.toFixed(2)} | Min: ${minPrice.toFixed(2)}
                </div>
              </div>
              
              <div className="relative h-40 border-l-2 border-b-2 border-gray-300">
                <svg width="100%" height="100%" className="absolute inset-0">
                  <polyline
                    fill="none"
                    stroke={data.change >= 0 ? "#22c55e" : "#ef4444"}
                    strokeWidth="2"
                    points={chartData.map((point, index) => {
                      const x = (index / (chartData.length - 1)) * 100
                      const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                      return `${x}%,${y}%`
                    }).join(' ')}
                  />
                  
                  {chartData.map((point, index) => {
                    if (index % 5 === 0) {
                      const x = (index / (chartData.length - 1)) * 100
                      const y = 100 - ((parseFloat(point.price) - minPrice) / priceRange) * 100
                      return (
                        <circle
                          key={index}
                          cx={`${x}%`}
                          cy={`${y}%`}
                          r="3"
                          fill={data.change >= 0 ? "#22c55e" : "#ef4444"}
                        />
                      )
                    }
                    return null
                  })}
                </svg>
                
                <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 -ml-12">
                  <span>${maxPrice.toFixed(2)}</span>
                  <span>${((maxPrice + minPrice) / 2).toFixed(2)}</span>
                  <span>${minPrice.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Componente de Predicciones Simplificado
function PredictionModule() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [loading, setLoading] = useState(false)

  const marketData = MARKET_DATA[selectedSymbol]
  const predictionData = PREDICTION_DATA[selectedSymbol]

  const handlePredict = () => {
    setLoading(true)
    setTimeout(() => setLoading(false), 1200)
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
          <p className="text-gray-600">Modelos de machine learning para predicción de precios</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resultados de Predicción */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Predicciones para {selectedSymbol}
              </span>
              <Badge variant="outline" className="text-green-600 border-green-300">
                Modo Offline
              </Badge>
            </CardTitle>
            <CardDescription>Resultados de modelos de inteligencia artificial</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Precio Actual */}
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">Precio Actual</div>
                <div className="text-3xl font-bold text-blue-600">
                  ${marketData.price.toFixed(2)}
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
                    predictionData.lstm > marketData.price ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {predictionData.lstm > marketData.price ? '+' : ''}
                    {((predictionData.lstm - marketData.price) / marketData.price * 100).toFixed(2)}%
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
                    variant={predictionData.svm === 'subida' && predictionData.lstm > marketData.price ? 'default' : 'destructive'}
                    className="text-sm"
                  >
                    {predictionData.svm === 'subida' && predictionData.lstm > marketData.price ? 'COMPRAR' : 'VENDER'}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {predictionData.svm === 'subida' && predictionData.lstm > marketData.price
                    ? 'Ambos modelos sugieren una tendencia alcista'
                    : 'Los modelos sugieren cautela o tendencia bajista'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Información Adicional */}
        <Card>
          <CardHeader>
            <CardTitle>Información del Modelo</CardTitle>
            <CardDescription>Detalles sobre las predicciones generadas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">Modelo SVM</h4>
                <p className="text-sm text-blue-700">
                  Support Vector Machine entrenado con indicadores técnicos para predecir la dirección del precio.
                </p>
              </div>
              
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-purple-800 mb-2">Modelo LSTM</h4>
                <p className="text-sm text-purple-700">
                  Red neuronal recurrente especializada en series temporales para pronóstico de precios.
                </p>
              </div>
              
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium text-yellow-800 mb-2">Nivel de Confianza</h4>
                <p className="text-sm text-yellow-700">
                  Métrica que indica la certeza del modelo en sus predicciones basada en datos históricos.
                </p>
              </div>
              
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 text-red-800">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm font-medium">Aviso Importante</span>
                </div>
                <p className="text-xs text-red-700 mt-1">
                  Las predicciones son estimaciones y no garantizan resultados futuros. 
                  Consulte siempre con un asesor financiero.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Componente principal simplificado
function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [user] = useState({ username: 'demo', full_name: 'Usuario Demo' })

  const handleLogin = () => {
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setActiveTab('overview')
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">Sistema de Inversión</CardTitle>
            <CardDescription>
              Plataforma de análisis financiero con IA
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Usuario</label>
                <input
                  type="text"
                  defaultValue="demo"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ingresa tu usuario"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Contraseña</label>
                <input
                  type="password"
                  defaultValue="Demo123!"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ingresa tu contraseña"
                />
              </div>
              <Button onClick={handleLogin} className="w-full">
                Iniciar Sesión
              </Button>
              <Button onClick={handleLogin} variant="outline" className="w-full">
                Usar Cuenta Demo
              </Button>
            </div>
            <div className="mt-6 text-center text-sm text-gray-600">
              <p>Cuenta Demo: demo / Demo123!</p>
              <p>Cuenta Admin: admin / Admin123!</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-xl font-semibold text-gray-900">
                Sistema de Inversión
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="text-green-600 border-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Modo Offline
              </Badge>
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span className="text-sm font-medium">{user.full_name}</span>
              </div>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Salir
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <Home className="h-4 w-4" />
              <span>Resumen</span>
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center space-x-2">
              <LineChart className="h-4 w-4" />
              <span>Análisis</span>
            </TabsTrigger>
            <TabsTrigger value="predictions" className="flex items-center space-x-2">
              <Brain className="h-4 w-4" />
              <span>Predicciones</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                    Mercado General
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">S&P 500</p>
                        <p className="text-sm text-gray-600">$4,567.89</p>
                      </div>
                      <div className="text-right text-green-600">
                        <p className="text-sm font-medium">+1.23%</p>
                        <p className="text-xs">+56.78</p>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">NASDAQ</p>
                        <p className="text-sm text-gray-600">$14,234.56</p>
                      </div>
                      <div className="text-right text-red-600">
                        <p className="text-sm font-medium">-0.45%</p>
                        <p className="text-xs">-64.12</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Activity className="h-5 w-5 mr-2 text-blue-600" />
                    Acciones Destacadas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(MARKET_DATA).slice(0, 3).map(([symbol, data]) => (
                      <div key={symbol} className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{symbol}</p>
                          <p className="text-sm text-gray-600">${data.price.toFixed(2)}</p>
                        </div>
                        <div className={`text-right ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          <p className="text-sm font-medium">{data.changePercent.toFixed(2)}%</p>
                          <p className="text-xs">{data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Shield className="h-5 w-5 mr-2 text-purple-600" />
                    Estado del Sistema
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Modo Operación</span>
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Offline
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Modelos ML</span>
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Operativo
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Datos</span>
                      <Badge variant="outline" className="text-green-600 border-green-600">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Simulados
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Acciones Rápidas</CardTitle>
                <CardDescription>
                  Accede rápidamente a las funciones principales del sistema
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2" 
                    onClick={() => setActiveTab('analysis')}
                  >
                    <LineChart className="h-6 w-6" />
                    <span className="text-sm">Analizar Acción</span>
                  </Button>
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2" 
                    onClick={() => setActiveTab('predictions')}
                  >
                    <Brain className="h-6 w-6" />
                    <span className="text-sm">Predicciones IA</span>
                  </Button>
                  <Button 
                    variant="outline" 
                    className="h-20 flex flex-col items-center justify-center space-y-2" 
                    onClick={() => window.open('https://finance.yahoo.com', '_blank')}
                  >
                    <ExternalLink className="h-6 w-6" />
                    <span className="text-sm">Yahoo Finance</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis">
            <AnalysisModule />
          </TabsContent>

          {/* Predictions Tab */}
          <TabsContent value="predictions">
            <PredictionModule />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App

