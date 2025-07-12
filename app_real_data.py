"""
Backend Mejorado con Datos Reales
Sistema de Apoyo a la Toma de Decisiones de Inversión
Integración con Yahoo Finance para datos en tiempo real
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import requests_cache
import logging
from functools import wraps
import time

# Configurar cache para optimizar las llamadas a Yahoo Finance
session = requests_cache.CachedSession('yfinance_cache', expire_after=300)  # 5 minutos

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123456789')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-987654321')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Configurar CORS para permitir conexiones desde cualquier origen
    CORS(app, origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Configurar JWT
    jwt = JWTManager(app)
    
    # Base de datos simulada en memoria para demo
    users_db = {
        'demo': {
            'id': 1,
            'username': 'demo',
            'email': 'demo@example.com',
            'password_hash': generate_password_hash('Demo123!'),
            'full_name': 'Usuario Demo',
            'created_at': datetime.now().isoformat()
        },
        'admin': {
            'id': 2,
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': generate_password_hash('Admin123!'),
            'full_name': 'Administrador',
            'created_at': datetime.now().isoformat()
        }
    }
    
    # Portafolios simulados en memoria
    portfolios_db = {
        'demo': {
            'cash': 100000.0,
            'positions': {
                'AAPL': {'quantity': 10, 'avg_price': 180.0},
                'GOOGL': {'quantity': 5, 'avg_price': 2800.0}
            },
            'transactions': []
        },
        'admin': {
            'cash': 50000.0,
            'positions': {},
            'transactions': []
        }
    }
    
    # Símbolos soportados
    SUPPORTED_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'BTC-USD', 'ETH-USD']
    
    def handle_errors(f):
        """Decorador para manejo de errores"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error interno del servidor: {str(e)}'
                }), 500
        return decorated_function
    
    def get_real_stock_data(symbol):
        """Obtener datos reales de Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol, session=session)
            
            # Obtener información básica
            info = ticker.info
            
            # Obtener datos históricos (últimos 30 días)
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                raise ValueError(f"No hay datos disponibles para {symbol}")
            
            # Datos más recientes
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Calcular cambio
            current_price = float(latest['Close'])
            previous_price = float(previous['Close'])
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
            
            # Calcular indicadores técnicos
            closes = hist['Close']
            sma_20 = closes.rolling(window=20).mean().iloc[-1] if len(closes) >= 20 else current_price
            sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else current_price
            
            # RSI simplificado
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not rsi.empty else 50
            
            # Preparar datos históricos
            historical_data = []
            for date, row in hist.tail(30).iterrows():
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': int(latest['Volume']),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'sma_20': float(sma_20) if not pd.isna(sma_20) else current_price,
                'sma_50': float(sma_50) if not pd.isna(sma_50) else current_price,
                'rsi': float(rsi_value) if not pd.isna(rsi_value) else 50,
                'historical_data': historical_data,
                'last_updated': datetime.now().isoformat(),
                'source': 'yahoo_finance'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
            # Fallback a datos simulados
            return get_fallback_data(symbol)
    
    def get_fallback_data(symbol):
        """Datos de fallback cuando Yahoo Finance no está disponible"""
        fallback_data = {
            'AAPL': {'price': 190.50, 'change': 3.21, 'change_percent': 1.72, 'volume': 85000000},
            'GOOGL': {'price': 175.20, 'change': -1.80, 'change_percent': -1.02, 'volume': 23456789},
            'MSFT': {'price': 420.75, 'change': 5.25, 'change_percent': 1.27, 'volume': 34567890},
            'TSLA': {'price': 248.90, 'change': -8.10, 'change_percent': -3.15, 'volume': 67890123},
            'AMZN': {'price': 178.30, 'change': 3.45, 'change_percent': 1.97, 'volume': 28901234},
            'BTC-USD': {'price': 67890.50, 'change': 1234.50, 'change_percent': 1.85, 'volume': 12345678},
            'ETH-USD': {'price': 3456.78, 'change': -89.12, 'change_percent': -2.51, 'volume': 9876543}
        }
        
        data = fallback_data.get(symbol, fallback_data['AAPL'])
        
        return {
            'symbol': symbol,
            'current_price': data['price'],
            'change': data['change'],
            'change_percent': data['change_percent'],
            'volume': data['volume'],
            'market_cap': 'N/A',
            'pe_ratio': 'N/A',
            'dividend_yield': 'N/A',
            'sma_20': data['price'] * 0.98,
            'sma_50': data['price'] * 0.95,
            'rsi': 50 + (data['change_percent'] * 2),
            'historical_data': [],
            'last_updated': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    # Rutas básicas
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Información básica de la API"""
        return jsonify({
            'message': 'Sistema de Apoyo a la Toma de Decisiones de Inversión - API',
            'version': '2.0.0',
            'status': 'active',
            'features': ['real_data', 'yahoo_finance', 'predictions', 'portfolio'],
            'documentation': '/api/docs'
        })
    
    @app.route('/api/docs', methods=['GET'])
    def api_docs():
        """Documentación de la API"""
        return jsonify({
            'endpoints': {
                'auth': {
                    'POST /api/auth/login': 'Autenticación de usuario'
                },
                'data': {
                    'GET /api/data/market/<symbol>': 'Datos de mercado para un símbolo',
                    'GET /api/data/market-overview': 'Resumen general del mercado'
                },
                'predictions': {
                    'GET /api/predictions/<symbol>': 'Predicciones SVM y LSTM para un símbolo'
                },
                'portfolio': {
                    'GET /api/portfolio': 'Obtener portafolio del usuario',
                    'POST /api/portfolio/buy': 'Comprar activos',
                    'POST /api/portfolio/sell': 'Vender activos'
                },
                'monitoring': {
                    'GET /api/monitoring/status': 'Estado del sistema'
                }
            },
            'supported_symbols': SUPPORTED_SYMBOLS
        })
    
    # Rutas de autenticación
    @app.route('/api/auth/login', methods=['POST'])
    @handle_errors
    def login():
        """Endpoint de login"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Usuario y contraseña son requeridos'
            }), 400
        
        user = users_db.get(username)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({
                'success': False,
                'error': 'Credenciales inválidas'
            }), 401
        
        access_token = create_access_token(identity=username)
        
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name']
        }
        
        return jsonify({
            'success': True,
            'token': access_token,
            'user': user_data,
            'message': 'Login exitoso'
        })
    
    # Rutas de datos
    @app.route('/api/data/market/<symbol>', methods=['GET'])
    @handle_errors
    def get_market_data(symbol):
        """Obtener datos de mercado para un símbolo específico"""
        symbol = symbol.upper()
        
        if symbol not in SUPPORTED_SYMBOLS:
            return jsonify({
                'success': False,
                'error': f'Símbolo {symbol} no soportado. Símbolos disponibles: {", ".join(SUPPORTED_SYMBOLS)}'
            }), 400
        
        data = get_real_stock_data(symbol)
        
        return jsonify({
            'success': True,
            'data': data
        })
    
    @app.route('/api/data/market-overview', methods=['GET'])
    @handle_errors
    def market_overview():
        """Obtener resumen del mercado"""
        # Obtener datos para los principales índices y acciones
        market_data = {
            'indices': [],
            'top_stocks': [],
            'last_updated': datetime.now().isoformat()
        }
        
        # Datos de índices (simulados por ahora)
        indices_data = [
            {'symbol': 'SPY', 'price': 445.67, 'change': 2.34, 'changePercent': 0.53},
            {'symbol': 'QQQ', 'price': 378.92, 'change': -1.45, 'changePercent': -0.38},
            {'symbol': 'IWM', 'price': 198.45, 'change': 0.87, 'changePercent': 0.44}
        ]
        market_data['indices'] = indices_data
        
        # Obtener datos reales para las principales acciones
        main_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        for symbol in main_stocks:
            try:
                stock_data = get_real_stock_data(symbol)
                market_data['top_stocks'].append({
                    'symbol': symbol,
                    'price': stock_data['current_price'],
                    'change': stock_data['change'],
                    'changePercent': stock_data['change_percent']
                })
            except Exception as e:
                logger.error(f"Error obteniendo datos para {symbol}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'data': market_data
        })
    
    # Rutas de predicciones
    @app.route('/api/predictions/<symbol>', methods=['GET'])
    @handle_errors
    def get_predictions(symbol):
        """Obtener predicciones SVM y LSTM para un símbolo"""
        symbol = symbol.upper()
        
        if symbol not in SUPPORTED_SYMBOLS:
            return jsonify({
                'success': False,
                'error': f'Símbolo {symbol} no soportado'
            }), 400
        
        # Obtener datos reales del mercado
        market_data = get_real_stock_data(symbol)
        
        # Generar predicción SVM basada en indicadores técnicos
        rsi = market_data['rsi']
        current_price = market_data['current_price']
        sma_20 = market_data['sma_20']
        
        # Lógica SVM simplificada
        if rsi < 30 and current_price < sma_20:
            svm_prediction = 'subida'
            svm_confidence = 0.85
        elif rsi > 70 and current_price > sma_20:
            svm_prediction = 'bajada'
            svm_confidence = 0.80
        else:
            svm_prediction = 'subida' if rsi < 50 else 'bajada'
            svm_confidence = 0.65
        
        # Generar predicción LSTM (precio futuro estimado)
        trend_factor = 1.02 if svm_prediction == 'subida' else 0.98
        lstm_prediction = current_price * trend_factor
        
        # Confianza general basada en volatilidad
        volatility = abs(market_data['change_percent']) / 100
        general_confidence = max(0.6, 0.9 - volatility)
        
        predictions = {
            'symbol': symbol,
            'svm': svm_prediction,
            'lstm': lstm_prediction,
            'confidence': general_confidence,
            'details': {
                'svm_confidence': svm_confidence,
                'current_price': current_price,
                'rsi': rsi,
                'sma_20': sma_20,
                'trend_factor': trend_factor
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': predictions
        })
    
    # Rutas de portafolio
    @app.route('/api/portfolio', methods=['GET'])
    @jwt_required()
    @handle_errors
    def get_portfolio():
        """Obtener portafolio del usuario"""
        username = get_jwt_identity()
        portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
        
        # Calcular valores actuales con datos reales
        total_value = portfolio['cash']
        positions_with_current_value = []
        
        for symbol, position in portfolio['positions'].items():
            try:
                market_data = get_real_stock_data(symbol)
                current_price = market_data['current_price']
                current_value = position['quantity'] * current_price
                total_value += current_value
                pnl = (current_price - position['avg_price']) * position['quantity']
                
                positions_with_current_value.append({
                    'symbol': symbol,
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': current_price,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_percent': (pnl / (position['avg_price'] * position['quantity'])) * 100
                })
            except Exception as e:
                logger.error(f"Error calculando valor para {symbol}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'portfolio': {
                'cash': portfolio['cash'],
                'total_value': total_value,
                'positions': positions_with_current_value,
                'transactions': portfolio['transactions'][-10:]  # Últimas 10 transacciones
            }
        })
    
    @app.route('/api/portfolio/buy', methods=['POST'])
    @jwt_required()
    @handle_errors
    def buy_stock():
        """Comprar acciones"""
        username = get_jwt_identity()
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        quantity = float(data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return jsonify({
                'success': False,
                'error': 'Símbolo y cantidad válidos son requeridos'
            }), 400
        
        if symbol not in SUPPORTED_SYMBOLS:
            return jsonify({
                'success': False,
                'error': f'Símbolo {symbol} no soportado'
            }), 400
        
        # Obtener precio actual real
        market_data = get_real_stock_data(symbol)
        current_price = market_data['current_price']
        total_cost = quantity * current_price
        
        # Verificar fondos
        portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
        if portfolio['cash'] < total_cost:
            return jsonify({
                'success': False,
                'error': f'Fondos insuficientes. Disponible: ${portfolio["cash"]:.2f}, Requerido: ${total_cost:.2f}'
            }), 400
        
        # Ejecutar compra
        portfolio['cash'] -= total_cost
        
        if symbol in portfolio['positions']:
            # Actualizar posición existente
            old_quantity = portfolio['positions'][symbol]['quantity']
            old_avg_price = portfolio['positions'][symbol]['avg_price']
            new_quantity = old_quantity + quantity
            new_avg_price = ((old_quantity * old_avg_price) + (quantity * current_price)) / new_quantity
            
            portfolio['positions'][symbol] = {
                'quantity': new_quantity,
                'avg_price': new_avg_price
            }
        else:
            # Nueva posición
            portfolio['positions'][symbol] = {
                'quantity': quantity,
                'avg_price': current_price
            }
        
        # Registrar transacción
        transaction = {
            'type': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': current_price,
            'total': total_cost,
            'timestamp': datetime.now().isoformat()
        }
        portfolio['transactions'].append(transaction)
        
        # Actualizar base de datos
        portfolios_db[username] = portfolio
        
        return jsonify({
            'success': True,
            'message': f'Compra exitosa: {quantity} acciones de {symbol} a ${current_price:.2f}',
            'transaction': transaction,
            'new_cash_balance': portfolio['cash']
        })
    
    @app.route('/api/portfolio/sell', methods=['POST'])
    @jwt_required()
    @handle_errors
    def sell_stock():
        """Vender acciones"""
        username = get_jwt_identity()
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        quantity = float(data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return jsonify({
                'success': False,
                'error': 'Símbolo y cantidad válidos son requeridos'
            }), 400
        
        # Verificar posición
        portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
        if symbol not in portfolio['positions']:
            return jsonify({
                'success': False,
                'error': f'No tienes posición en {symbol}'
            }), 400
        
        current_position = portfolio['positions'][symbol]['quantity']
        if current_position < quantity:
            return jsonify({
                'success': False,
                'error': f'Cantidad insuficiente. Disponible: {current_position}, Solicitado: {quantity}'
            }), 400
        
        # Obtener precio actual real
        market_data = get_real_stock_data(symbol)
        current_price = market_data['current_price']
        total_proceeds = quantity * current_price
        
        # Ejecutar venta
        portfolio['cash'] += total_proceeds
        
        # Actualizar posición
        new_quantity = current_position - quantity
        if new_quantity == 0:
            del portfolio['positions'][symbol]
        else:
            portfolio['positions'][symbol]['quantity'] = new_quantity
        
        # Registrar transacción
        transaction = {
            'type': 'SELL',
            'symbol': symbol,
            'quantity': quantity,
            'price': current_price,
            'total': total_proceeds,
            'timestamp': datetime.now().isoformat()
        }
        portfolio['transactions'].append(transaction)
        
        # Actualizar base de datos
        portfolios_db[username] = portfolio
        
        return jsonify({
            'success': True,
            'message': f'Venta exitosa: {quantity} acciones de {symbol} a ${current_price:.2f}',
            'transaction': transaction,
            'new_cash_balance': portfolio['cash']
        })
    
    # Rutas de monitoreo
    @app.route('/api/monitoring/status', methods=['GET'])
    @handle_errors
    def system_status():
        """Estado del sistema"""
        import psutil
        
        # Métricas del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Verificar APIs externas
        apis_status = {}
        
        # Test Yahoo Finance
        try:
            test_ticker = yf.Ticker("AAPL")
            test_data = test_ticker.history(period="1d")
            apis_status['yahoo_finance'] = 'online' if not test_data.empty else 'offline'
        except:
            apis_status['yahoo_finance'] = 'offline'
        
        apis_status['database'] = 'online'  # Simulado
        apis_status['cache'] = 'online'     # Simulado
        
        return jsonify({
            'success': True,
            'system_status': {
                'system': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'uptime': 'Sistema activo'
                },
                'apis': apis_status,
                'last_updated': datetime.now().isoformat()
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

