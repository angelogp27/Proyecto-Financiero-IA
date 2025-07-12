// Cliente API completamente offline - sin llamadas al backend
export class ApiClient {
  constructor(baseUrl = null) {
    this.baseUrl = 'offline'
    this.maxRetries = 0
    this.retryDelay = 0
    this.connectionStatus = 'offline'
    this.listeners = []
    this.offlineMode = true
    
    console.log('ApiClient iniciado en modo completamente offline')
  }

  // Simular datos de mercado
  async getMarketData(symbol) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockData = this.generateMockMarketData(symbol)
        resolve({
          success: true,
          data: mockData,
          source: 'offline'
        })
      }, 300)
    })
  }

  // Simular predicciones
  async getPredictions(symbol) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockPredictions = this.generateMockPredictions(symbol)
        resolve({
          success: true,
          data: mockPredictions,
          source: 'offline'
        })
      }, 500)
    })
  }

  // Simular login
  async login(credentials) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: {
            token: 'offline_token_' + Date.now(),
            user: {
              username: credentials.username || 'demo',
              role: 'demo',
              full_name: credentials.username === 'admin' ? 'Administrador' : 'Usuario Demo'
            }
          },
          source: 'offline'
        })
      }, 1000)
    })
  }

  // Simular datos de portafolio
  async getPortfolio() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: {
            cash: 10000,
            positions: [
              { symbol: 'AAPL', quantity: 10, avgPrice: 185.50 },
              { symbol: 'GOOGL', quantity: 5, avgPrice: 170.20 }
            ],
            totalValue: 12000
          },
          source: 'offline'
        })
      }, 400)
    })
  }

  // Simular noticias
  async getNews() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: [
            {
              title: 'Mercados en alza tras datos económicos positivos',
              summary: 'Los índices principales muestran tendencia alcista...',
              sentiment: 'positive',
              date: new Date().toISOString()
            },
            {
              title: 'Tecnológicas lideran las ganancias del día',
              summary: 'Apple y Microsoft registran aumentos significativos...',
              sentiment: 'positive',
              date: new Date().toISOString()
            }
          ],
          source: 'offline'
        })
      }, 600)
    })
  }

  // Generar datos de mercado simulados
  generateMockMarketData(symbol) {
    const baseData = {
      'AAPL': { price: 190.50, change: 3.21, changePercent: 1.72 },
      'GOOGL': { price: 175.20, change: -1.80, changePercent: -1.02 },
      'MSFT': { price: 420.75, change: 5.25, changePercent: 1.27 },
      'TSLA': { price: 248.90, change: -8.10, changePercent: -3.15 },
      'AMZN': { price: 178.30, change: 3.45, changePercent: 1.97 },
      'BTC-USD': { price: 67890.50, change: 1234.50, changePercent: 1.85 },
      'ETH-USD': { price: 3456.78, change: -89.12, changePercent: -2.51 }
    }

    const data = baseData[symbol] || baseData['AAPL']
    
    return {
      symbol,
      price: data.price,
      change: data.change,
      changePercent: data.changePercent,
      volume: Math.floor(Math.random() * 100000000),
      high: data.price * 1.05,
      low: data.price * 0.95,
      open: data.price * 0.98
    }
  }

  // Generar predicciones simuladas
  generateMockPredictions(symbol) {
    const baseData = {
      'AAPL': { svm: 'subida', lstm: 195.50, confidence: 0.78 },
      'GOOGL': { svm: 'bajada', lstm: 170.20, confidence: 0.65 },
      'MSFT': { svm: 'subida', lstm: 430.75, confidence: 0.82 },
      'TSLA': { svm: 'bajada', lstm: 240.90, confidence: 0.71 },
      'AMZN': { svm: 'subida', lstm: 185.30, confidence: 0.69 },
      'BTC-USD': { svm: 'subida', lstm: 70000.50, confidence: 0.75 },
      'ETH-USD': { svm: 'bajada', lstm: 3300.78, confidence: 0.68 }
    }

    return baseData[symbol] || baseData['AAPL']
  }

  // Métodos de estado de conexión (siempre offline)
  getConnectionStatus() {
    return 'offline'
  }

  addConnectionListener(callback) {
    // No hacer nada en modo offline
  }

  removeConnectionListener(callback) {
    // No hacer nada en modo offline
  }

  async checkConnection() {
    return false
  }
}

// Instancia global del cliente API
export const apiClient = new ApiClient()

