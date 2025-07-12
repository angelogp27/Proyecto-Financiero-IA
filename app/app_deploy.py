"""
Backend Simplificado para Despliegue
Sistema de Apoyo a la Toma de Decisiones de Inversión
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123456789')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-987654321')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Configurar CORS para permitir conexiones desde cualquier origen
    CORS(app, origins=['*'])
    
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
    
    # Datos simulados mejorados
    stock_data_db = {
        'AAPL': {
            'symbol': 'AAPL',
            'current_price': 190.50,
            'change': 3.21,
            'change_percent': 1.72,
            'volume': 85000000,
            'market_cap': '2.9T',
            'pe_ratio': 32.5,
            'dividend_yield': 'N/A',
            'sma_20': 180.00,
            'sma_50': 170.00,
            'rsi': 65.00,
            'historical_data': [
                {'date': '2024-06-01', 'open': 185.0, 'high': 192.0, 'low': 183.0, 'close': 190.5, 'volume': 85000000},
                {'date': '2024-06-02', 'open': 190.5, 'high': 195.0, 'low': 188.0, 'close': 193.2, 'volume': 92000000},
                {'date': '2024-06-03', 'open': 193.2, 'high': 196.0, 'low': 191.0, 'close': 194.8, 'volume': 88000000}
            ]
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'current_price': 2847.33,
            'change': -12.45,
            'change_percent': -0.44,
            'volume': 1200000,
            'market_cap': '1.8T',
            'pe_ratio': 28.3,
            'dividend_yield': 'N/A',
            'sma_20': 2850.00,
            'sma_50': 2820.00,
            'rsi': 45.00,
            'historical_data': [
                {'date': '2024-06-01', 'open': 2850.0, 'high': 2870.0, 'low': 2840.0, 'close': 2847.33, 'volume': 1200000},
                {'date': '2024-06-02', 'open': 2847.33, 'high': 2860.0, 'low': 2830.0, 'close': 2855.0, 'volume': 1300000},
                {'date': '2024-06-03', 'open': 2855.0, 'high': 2865.0, 'low': 2845.0, 'close': 2852.1, 'volume': 1150000}
            ]
        },
        'MSFT': {
            'symbol': 'MSFT',
            'current_price': 378.85,
            'change': 5.67,
            'change_percent': 1.52,
            'volume': 25000000,
            'market_cap': '2.8T',
            'pe_ratio': 35.2,
            'dividend_yield': '0.72%',
            'sma_20': 375.00,
            'sma_50': 370.00,
            'rsi': 58.00,
            'historical_data': [
                {'date': '2024-06-01', 'open': 375.0, 'high': 380.0, 'low': 373.0, 'close': 378.85, 'volume': 25000000},
                {'date': '2024-06-02', 'open': 378.85, 'high': 382.0, 'low': 376.0, 'close': 380.2, 'volume': 27000000},
                {'date': '2024-06-03', 'open': 380.2, 'high': 383.0, 'low': 378.0, 'close': 381.5, 'volume': 24000000}
            ]
        },
        'TSLA': {
            'symbol': 'TSLA',
            'current_price': 248.42,
            'change': -8.33,
            'change_percent': -3.24,
            'volume': 45000000,
            'market_cap': '790B',
            'pe_ratio': 65.8,
            'dividend_yield': 'N/A',
            'sma_20': 255.00,
            'sma_50': 260.00,
            'rsi': 35.00,
            'historical_data': [
                {'date': '2024-06-01', 'open': 255.0, 'high': 258.0, 'low': 248.0, 'close': 248.42, 'volume': 45000000},
                {'date': '2024-06-02', 'open': 248.42, 'high': 252.0, 'low': 245.0, 'close': 250.1, 'volume': 48000000},
                {'date': '2024-06-03', 'open': 250.1, 'high': 253.0, 'low': 247.0, 'close': 249.8, 'volume': 46000000}
            ]
        },
        'AMZN': {
            'symbol': 'AMZN',
            'current_price': 3342.88,
            'change': 23.45,
            'change_percent': 0.71,
            'volume': 3500000,
            'market_cap': '1.7T',
            'pe_ratio': 58.2,
            'dividend_yield': 'N/A',
            'sma_20': 3320.00,
            'sma_50': 3300.00,
            'rsi': 62.00,
            'historical_data': [
                {'date': '2024-06-01', 'open': 3320.0, 'high': 3350.0, 'low': 3315.0, 'close': 3342.88, 'volume': 3500000},
                {'date': '2024-06-02', 'open': 3342.88, 'high': 3360.0, 'low': 3335.0, 'close': 3355.2, 'volume': 3700000},
                {'date': '2024-06-03', 'open': 3355.2, 'high': 3370.0, 'low': 3345.0, 'close': 3358.9, 'volume': 3400000}
            ]
        }
    }
    
    # Rutas de autenticación
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Endpoint de login"""
        try:
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
                'access_token': access_token,
                'user': user_data,
                'message': 'Login exitoso'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    # Rutas de datos
    @app.route('/api/data/stock/<symbol>', methods=['GET'])
    @jwt_required()
    def get_stock_data(symbol):
        """Obtener datos de una acción específica"""
        try:
            symbol = symbol.upper()
            data = stock_data_db.get(symbol)
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudieron obtener datos para {symbol}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/data/market-overview', methods=['GET'])
    @jwt_required()
    def market_overview():
        """Obtener resumen del mercado"""
        try:
            market_data = {
                'indices': [
                    {'symbol': 'SPY', 'price': 445.67, 'change': 2.34, 'changePercent': 0.53},
                    {'symbol': 'QQQ', 'price': 378.92, 'change': -1.45, 'changePercent': -0.38},
                    {'symbol': 'IWM', 'price': 198.45, 'change': 0.87, 'changePercent': 0.44}
                ],
                'top_stocks': [
                    {'symbol': 'AAPL', 'price': 190.50, 'change': 3.21, 'changePercent': 1.72},
                    {'symbol': 'GOOGL', 'price': 2847.33, 'change': -12.45, 'changePercent': -0.44},
                    {'symbol': 'MSFT', 'price': 378.85, 'change': 5.67, 'changePercent': 1.52},
                    {'symbol': 'AMZN', 'price': 3342.88, 'change': 23.45, 'changePercent': 0.71},
                    {'symbol': 'TSLA', 'price': 248.42, 'change': -8.33, 'changePercent': -3.24}
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'data': market_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/predictions/svm/<symbol>', methods=['GET'])
    @jwt_required()
    def get_svm_prediction(symbol):
        """Obtener predicción SVM para un símbolo"""
        try:
            symbol = symbol.upper()
            data = stock_data_db.get(symbol)
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudieron obtener datos para {symbol}'
                }), 404
            
            # Generar predicción basada en RSI
            rsi = data['rsi']
            if rsi < 30:
                direction = 'BUY'
                confidence = 0.85
            elif rsi > 70:
                direction = 'SELL'
                confidence = 0.80
            else:
                direction = 'HOLD'
                confidence = 0.65
            
            prediction = {
                'symbol': symbol,
                'prediction': direction,
                'confidence': confidence,
                'model': 'SVM',
                'indicators': {
                    'rsi': rsi,
                    'sma_20': data['sma_20'],
                    'sma_50': data['sma_50'],
                    'current_price': data['current_price']
                }
            }
            
            return jsonify({
                'success': True,
                'prediction': prediction
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/predictions/lstm/<symbol>', methods=['GET'])
    @jwt_required()
    def get_lstm_prediction(symbol):
        """Obtener predicción LSTM para un símbolo"""
        try:
            symbol = symbol.upper()
            data = stock_data_db.get(symbol)
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudieron obtener datos para {symbol}'
                }), 404
            
            current_price = data['current_price']
            
            # Simular predicción de precio futuro
            import random
            trend = random.uniform(-0.02, 0.03)
            predictions = []
            price = current_price
            
            for i in range(5):
                price = price * (1 + trend + random.uniform(-0.01, 0.01))
                predictions.append(round(price, 2))
            
            prediction = {
                'symbol': symbol,
                'current_price': current_price,
                'predicted_price_24h': predictions[0],
                'predicted_prices_5d': predictions,
                'model': 'LSTM',
                'confidence': random.uniform(0.70, 0.90)
            }
            
            return jsonify({
                'success': True,
                'prediction': prediction
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/portfolio', methods=['GET'])
    @jwt_required()
    def get_portfolio():
        """Obtener portafolio del usuario"""
        try:
            username = get_jwt_identity()
            portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
            
            # Calcular valores actuales
            total_value = portfolio['cash']
            positions_with_current_value = []
            
            for symbol, position in portfolio['positions'].items():
                data = stock_data_db.get(symbol)
                if data:
                    current_value = position['quantity'] * data['current_price']
                    total_value += current_value
                    pnl = (data['current_price'] - position['avg_price']) * position['quantity']
                    
                    positions_with_current_value.append({
                        'symbol': symbol,
                        'quantity': position['quantity'],
                        'avg_price': position['avg_price'],
                        'current_price': data['current_price'],
                        'current_value': current_value,
                        'pnl': pnl
                    })
            
            return jsonify({
                'success': True,
                'portfolio': {
                    'cash': portfolio['cash'],
                    'total_value': total_value,
                    'positions': positions_with_current_value,
                    'transactions': portfolio['transactions']
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/portfolio/buy', methods=['POST'])
    @jwt_required()
    def buy_stock():
        """Comprar acciones"""
        try:
            username = get_jwt_identity()
            data = request.get_json()
            symbol = data.get('symbol', '').upper()
            quantity = float(data.get('quantity', 0))
            
            if not symbol or quantity <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Símbolo y cantidad válidos son requeridos'
                }), 400
            
            # Obtener precio actual
            stock_data = stock_data_db.get(symbol)
            if not stock_data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudieron obtener datos para {symbol}'
                }), 404
            
            current_price = stock_data['current_price']
            total_cost = quantity * current_price
            
            # Verificar fondos
            portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
            if portfolio['cash'] < total_cost:
                return jsonify({
                    'success': False,
                    'error': 'Fondos insuficientes'
                }), 400
            
            # Actualizar portafolio
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
            
            portfolios_db[username] = portfolio
            
            return jsonify({
                'success': True,
                'message': f'Compra exitosa: {quantity} acciones de {symbol}',
                'transaction': transaction
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/portfolio/sell', methods=['POST'])
    @jwt_required()
    def sell_stock():
        """Vender acciones"""
        try:
            username = get_jwt_identity()
            data = request.get_json()
            symbol = data.get('symbol', '').upper()
            quantity = float(data.get('quantity', 0))
            
            if not symbol or quantity <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Símbolo y cantidad válidos son requeridos'
                }), 400
            
            portfolio = portfolios_db.get(username, {'cash': 100000.0, 'positions': {}, 'transactions': []})
            
            # Verificar que tiene la posición
            if symbol not in portfolio['positions']:
                return jsonify({
                    'success': False,
                    'error': f'No tienes posición en {symbol}'
                }), 400
            
            current_position = portfolio['positions'][symbol]
            if current_position['quantity'] < quantity:
                return jsonify({
                    'success': False,
                    'error': f'Cantidad insuficiente. Tienes {current_position["quantity"]} acciones'
                }), 400
            
            # Obtener precio actual
            stock_data = stock_data_db.get(symbol)
            if not stock_data:
                return jsonify({
                    'success': False,
                    'error': f'No se pudieron obtener datos para {symbol}'
                }), 404
            
            current_price = stock_data['current_price']
            total_proceeds = quantity * current_price
            
            # Actualizar portafolio
            portfolio['cash'] += total_proceeds
            
            # Actualizar posición
            new_quantity = current_position['quantity'] - quantity
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
            
            portfolios_db[username] = portfolio
            
            return jsonify({
                'success': True,
                'message': f'Venta exitosa: {quantity} acciones de {symbol}',
                'transaction': transaction
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/monitoring/status', methods=['GET'])
    @jwt_required()
    def system_status():
        """Obtener estado del sistema"""
        try:
            status_data = {
                'overall_status': 'healthy',
                'services': {
                    'api': 'active',
                    'database': 'active',
                    'ml_models': 'active',
                    'data_feeds': 'active'
                },
                'metrics': {
                    'cpu_usage': 15.2,
                    'memory_usage': 42.1,
                    'disk_usage': 28.5,
                    'active_users': 2,
                    'api_calls_today': 1247,
                    'uptime_hours': 72.5
                },
                'last_check': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'system_status': status_data
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error interno del servidor: {str(e)}'
            }), 500
    
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """Información general de la API"""
        return jsonify({
            'name': 'Sistema de Apoyo a la Toma de Decisiones de Inversión',
            'version': '2.0.0',
            'description': 'API REST para análisis financiero con IA y datos simulados mejorados',
            'status': 'active',
            'endpoints': {
                'auth': ['/api/auth/login', '/api/auth/register', '/api/auth/profile'],
                'data': ['/api/data/market-overview', '/api/data/stock/<symbol>'],
                'predictions': ['/api/predictions/svm/<symbol>', '/api/predictions/lstm/<symbol>'],
                'portfolio': ['/api/portfolio', '/api/portfolio/buy', '/api/portfolio/sell'],
                'monitoring': ['/api/monitoring/status']
            }
        })
    
    @app.route('/')
    def index():
        """Página de inicio de la API"""
        return jsonify({
            'message': 'Sistema de Apoyo a la Toma de Decisiones de Inversión - API',
            'version': '2.0.0',
            'status': 'active',
            'documentation': '/api/info'
        })
    
    # Manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint no encontrado'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("🚀 Iniciando Sistema de Apoyo a la Toma de Decisiones de Inversión v2.0")
    print("📊 API REST con datos simulados mejorados disponible en: http://localhost:5000")
    print("🔐 Usuarios demo disponibles:")
    print("   - demo / Demo123!")
    print("   - admin / Admin123!")
    print("🌐 CORS configurado para cualquier origen")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

