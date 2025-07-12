"""
Módulo de Ingesta y Validación de Datos
Implementa la conexión con Yahoo Finance y CoinMarketCap para obtener datos reales
"""

from flask import Blueprint, jsonify, request
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import logging

data_bp = Blueprint('data', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionManager:
    def __init__(self):
        self.supported_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        self.supported_crypto = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'SOL-USD']
        self.data_cache = {}
        
    def get_yahoo_finance_data(self, symbol, period='1y'):
        """
        Obtiene datos de Yahoo Finance para un símbolo específico
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No se encontraron datos para {symbol}")
                return None
                
            # Agregar información adicional
            info = ticker.info
            
            result = {
                'symbol': symbol,
                'data': data.to_dict('records'),
                'info': {
                    'longName': info.get('longName', symbol),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'marketCap': info.get('marketCap', 0),
                    'currentPrice': info.get('currentPrice', data['Close'].iloc[-1] if not data.empty else 0)
                },
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Datos obtenidos exitosamente para {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de Yahoo Finance para {symbol}: {str(e)}")
            return None
    
    def validate_and_clean_data(self, data):
        """
        Valida y limpia los datos obtenidos
        """
        if not data or 'data' not in data:
            return None
            
        try:
            df = pd.DataFrame(data['data'])
            
            # Eliminar filas con valores nulos en columnas críticas
            df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Verificar que los precios sean positivos
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                df = df[df[col] > 0]
            
            # Verificar que High >= Low
            df = df[df['High'] >= df['Low']]
            
            # Verificar que el volumen sea positivo
            df = df[df['Volume'] >= 0]
            
            # Calcular indicadores técnicos básicos
            df = self.calculate_technical_indicators(df)
            
            data['data'] = df.to_dict('records')
            data['validation'] = {
                'is_valid': True,
                'records_count': len(df),
                'date_range': {
                    'start': df.index.min().isoformat() if not df.empty else None,
                    'end': df.index.max().isoformat() if not df.empty else None
                }
            }
            
            logger.info(f"Datos validados exitosamente para {data['symbol']}")
            return data
            
        except Exception as e:
            logger.error(f"Error validando datos: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, df):
        """
        Calcula indicadores técnicos básicos
        """
        try:
            # RSI (Relative Strength Index)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Medias móviles
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores técnicos: {str(e)}")
            return df
    
    def get_multiple_symbols_data(self, symbols, period='1y'):
        """
        Obtiene datos para múltiples símbolos
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_yahoo_finance_data(symbol, period)
            if data:
                validated_data = self.validate_and_clean_data(data)
                if validated_data:
                    results[symbol] = validated_data
                    
        return results

# Instancia global del manager
data_manager = DataIngestionManager()

@data_bp.route('/data/stocks', methods=['GET'])
def get_stocks_data():
    """
    Endpoint para obtener datos de acciones
    """
    try:
        symbols = request.args.get('symbols', '').split(',')
        period = request.args.get('period', '1y')
        
        if not symbols or symbols == ['']:
            symbols = data_manager.supported_stocks
        
        # Filtrar símbolos soportados
        valid_symbols = [s.upper().strip() for s in symbols if s.upper().strip() in data_manager.supported_stocks]
        
        if not valid_symbols:
            return jsonify({
                'error': 'No se proporcionaron símbolos válidos',
                'supported_symbols': data_manager.supported_stocks
            }), 400
        
        data = data_manager.get_multiple_symbols_data(valid_symbols, period)
        
        return jsonify({
            'success': True,
            'data': data,
            'symbols_requested': valid_symbols,
            'symbols_found': list(data.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_stocks_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/data/crypto', methods=['GET'])
def get_crypto_data():
    """
    Endpoint para obtener datos de criptomonedas
    """
    try:
        symbols = request.args.get('symbols', '').split(',')
        period = request.args.get('period', '1y')
        
        if not symbols or symbols == ['']:
            symbols = data_manager.supported_crypto
        
        # Filtrar símbolos soportados
        valid_symbols = [s.upper().strip() for s in symbols if s.upper().strip() in data_manager.supported_crypto]
        
        if not valid_symbols:
            return jsonify({
                'error': 'No se proporcionaron símbolos válidos de criptomonedas',
                'supported_symbols': data_manager.supported_crypto
            }), 400
        
        data = data_manager.get_multiple_symbols_data(valid_symbols, period)
        
        return jsonify({
            'success': True,
            'data': data,
            'symbols_requested': valid_symbols,
            'symbols_found': list(data.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_crypto_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/data/symbol/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """
    Endpoint para obtener datos de un símbolo específico
    """
    try:
        period = request.args.get('period', '1y')
        symbol = symbol.upper()
        
        # Verificar si el símbolo es soportado
        if symbol not in data_manager.supported_stocks + data_manager.supported_crypto:
            return jsonify({
                'error': f'Símbolo {symbol} no soportado',
                'supported_symbols': {
                    'stocks': data_manager.supported_stocks,
                    'crypto': data_manager.supported_crypto
                }
            }), 400
        
        data = data_manager.get_yahoo_finance_data(symbol, period)
        if not data:
            return jsonify({'error': f'No se pudieron obtener datos para {symbol}'}), 404
        
        validated_data = data_manager.validate_and_clean_data(data)
        if not validated_data:
            return jsonify({'error': f'Los datos para {symbol} no pasaron la validación'}), 422
        
        return jsonify({
            'success': True,
            'data': validated_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_symbol_data para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/data/supported-symbols', methods=['GET'])
def get_supported_symbols():
    """
    Endpoint para obtener la lista de símbolos soportados
    """
    return jsonify({
        'success': True,
        'supported_symbols': {
            'stocks': data_manager.supported_stocks,
            'crypto': data_manager.supported_crypto
        },
        'total_symbols': len(data_manager.supported_stocks) + len(data_manager.supported_crypto)
    })

@data_bp.route('/data/validate', methods=['POST'])
def validate_data():
    """
    Endpoint para validar datos proporcionados por el usuario
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos para validar'}), 400
        
        validated_data = data_manager.validate_and_clean_data(data)
        
        if validated_data:
            return jsonify({
                'success': True,
                'message': 'Datos validados exitosamente',
                'data': validated_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Los datos no pasaron la validación'
            }), 422
            
    except Exception as e:
        logger.error(f"Error en endpoint validate_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/data/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado del módulo de ingesta de datos
    """
    try:
        # Probar conexión con Yahoo Finance
        test_symbol = 'AAPL'
        test_data = data_manager.get_yahoo_finance_data(test_symbol, period='5d')
        
        yahoo_status = 'OK' if test_data else 'ERROR'
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'yahoo_finance': yahoo_status
            },
            'supported_symbols_count': {
                'stocks': len(data_manager.supported_stocks),
                'crypto': len(data_manager.supported_crypto)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

