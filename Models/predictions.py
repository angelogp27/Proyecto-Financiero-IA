"""
Módulo de Predicciones con SVM y LSTM
Implementa modelos de machine learning para predicción de subidas (SVM) y pronóstico de precios (LSTM)
"""

from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import joblib
import os

predictions_bp = Blueprint('predictions', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SVMPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, data):
        """
        Prepara las características para el modelo SVM
        """
        try:
            df = pd.DataFrame(data)
            
            # Calcular características técnicas
            features = []
            
            for i in range(len(df)):
                if i < 20:  # Necesitamos al menos 20 días de historia
                    continue
                    
                current_data = df.iloc[max(0, i-20):i+1]
                
                # Características de precio
                price_change = (current_data['Close'].iloc[-1] - current_data['Close'].iloc[-2]) / current_data['Close'].iloc[-2]
                volume_ratio = current_data['Volume'].iloc[-1] / current_data['Volume'].mean()
                
                # RSI
                rsi = current_data.get('RSI', pd.Series([50])).iloc[-1] if 'RSI' in current_data.columns else 50
                
                # MACD
                macd = current_data.get('MACD', pd.Series([0])).iloc[-1] if 'MACD' in current_data.columns else 0
                
                # Medias móviles
                sma_20 = current_data.get('SMA_20', current_data['Close']).iloc[-1]
                price_vs_sma = (current_data['Close'].iloc[-1] - sma_20) / sma_20
                
                # Volatilidad
                volatility = current_data['Close'].pct_change().std()
                
                feature_vector = [
                    price_change,
                    volume_ratio,
                    rsi / 100,  # Normalizar RSI
                    macd,
                    price_vs_sma,
                    volatility
                ]
                
                features.append(feature_vector)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparando características SVM: {str(e)}")
            return np.array([])
    
    def create_labels(self, data, lookforward=5):
        """
        Crea etiquetas para el entrenamiento (1 si sube, 0 si baja)
        """
        try:
            df = pd.DataFrame(data)
            labels = []
            
            for i in range(len(df)):
                if i < 20 or i + lookforward >= len(df):
                    continue
                    
                current_price = df['Close'].iloc[i]
                future_price = df['Close'].iloc[i + lookforward]
                
                # 1 si el precio sube más del 2%, 0 en caso contrario
                label = 1 if (future_price - current_price) / current_price > 0.02 else 0
                labels.append(label)
            
            return np.array(labels)
            
        except Exception as e:
            logger.error(f"Error creando etiquetas SVM: {str(e)}")
            return np.array([])
    
    def train(self, data):
        """
        Entrena el modelo SVM
        """
        try:
            features = self.prepare_features(data)
            labels = self.create_labels(data)
            
            if len(features) == 0 or len(labels) == 0 or len(features) != len(labels):
                logger.warning("No hay suficientes datos para entrenar el modelo SVM")
                return False
            
            # Normalizar características
            features_scaled = self.scaler.fit_transform(features)
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, labels, test_size=0.2, random_state=42
            )
            
            # Entrenar modelo
            self.model = SVC(kernel='rbf', probability=True, random_state=42)
            self.model.fit(X_train, y_train)
            
            # Evaluar
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            logger.info(f"SVM entrenado - Train Score: {train_score:.3f}, Test Score: {test_score:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelo SVM: {str(e)}")
            return False
    
    def predict(self, data):
        """
        Realiza predicciones con el modelo SVM
        """
        try:
            if not self.is_trained:
                # Entrenar con los datos proporcionados
                if not self.train(data):
                    return None
            
            features = self.prepare_features(data)
            if len(features) == 0:
                return None
            
            # Usar solo la última observación para predicción
            last_features = features[-1:].reshape(1, -1)
            features_scaled = self.scaler.transform(last_features)
            
            # Predicción
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            
            return {
                'prediction': int(prediction),
                'probability_down': float(probability[0]),
                'probability_up': float(probability[1]),
                'confidence': float(max(probability)),
                'signal': 'BUY' if prediction == 1 else 'HOLD'
            }
            
        except Exception as e:
            logger.error(f"Error en predicción SVM: {str(e)}")
            return None

class LSTMPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.sequence_length = 60
        
    def prepare_sequences(self, data):
        """
        Prepara secuencias para el modelo LSTM
        """
        try:
            df = pd.DataFrame(data)
            prices = df['Close'].values.reshape(-1, 1)
            
            # Normalizar precios
            scaled_prices = self.scaler.fit_transform(prices)
            
            X, y = [], []
            for i in range(self.sequence_length, len(scaled_prices)):
                X.append(scaled_prices[i-self.sequence_length:i, 0])
                y.append(scaled_prices[i, 0])
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparando secuencias LSTM: {str(e)}")
            return np.array([]), np.array([])
    
    def build_model(self):
        """
        Construye la arquitectura del modelo LSTM
        """
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(self.sequence_length, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model
    
    def train(self, data):
        """
        Entrena el modelo LSTM
        """
        try:
            X, y = self.prepare_sequences(data)
            
            if len(X) == 0 or len(y) == 0:
                logger.warning("No hay suficientes datos para entrenar el modelo LSTM")
                return False
            
            # Reshape para LSTM
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            # Dividir datos
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Construir y entrenar modelo
            self.model = self.build_model()
            
            history = self.model.fit(
                X_train, y_train,
                epochs=50,
                batch_size=32,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # Evaluar
            train_loss = self.model.evaluate(X_train, y_train, verbose=0)
            test_loss = self.model.evaluate(X_test, y_test, verbose=0)
            
            logger.info(f"LSTM entrenado - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logger.error(f"Error entrenando modelo LSTM: {str(e)}")
            return False
    
    def predict(self, data, days_ahead=7):
        """
        Realiza predicciones con el modelo LSTM
        """
        try:
            if not self.is_trained:
                # Entrenar con los datos proporcionados
                if not self.train(data):
                    return None
            
            df = pd.DataFrame(data)
            prices = df['Close'].values.reshape(-1, 1)
            
            if len(prices) < self.sequence_length:
                logger.warning("No hay suficientes datos históricos para predicción LSTM")
                return None
            
            # Normalizar precios
            scaled_prices = self.scaler.transform(prices)
            
            # Usar los últimos sequence_length días para predicción
            last_sequence = scaled_prices[-self.sequence_length:].reshape(1, self.sequence_length, 1)
            
            # Predicción
            predictions = []
            current_sequence = last_sequence.copy()
            
            for _ in range(days_ahead):
                pred_scaled = self.model.predict(current_sequence, verbose=0)
                pred_price = self.scaler.inverse_transform(pred_scaled.reshape(-1, 1))[0, 0]
                predictions.append(pred_price)
                
                # Actualizar secuencia para siguiente predicción
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1, 0] = pred_scaled[0, 0]
            
            current_price = prices[-1, 0]
            price_change = (predictions[-1] - current_price) / current_price
            
            return {
                'predictions': [float(p) for p in predictions],
                'current_price': float(current_price),
                'predicted_price': float(predictions[-1]),
                'price_change_percent': float(price_change * 100),
                'days_ahead': days_ahead,
                'trend': 'UPWARD' if price_change > 0 else 'DOWNWARD'
            }
            
        except Exception as e:
            logger.error(f"Error en predicción LSTM: {str(e)}")
            return None

# Instancias globales de los predictores
svm_predictor = SVMPredictor()
lstm_predictor = LSTMPredictor()

@predictions_bp.route('/predictions/svm/<symbol>', methods=['POST'])
def predict_svm(symbol):
    """
    Endpoint para predicción SVM de un símbolo específico
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Se requieren datos históricos para la predicción'}), 400
        
        prediction = svm_predictor.predict(data['data'])
        
        if prediction is None:
            return jsonify({'error': 'No se pudo generar la predicción SVM'}), 500
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'model': 'SVM',
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint predict_svm para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@predictions_bp.route('/predictions/lstm/<symbol>', methods=['POST'])
def predict_lstm(symbol):
    """
    Endpoint para predicción LSTM de un símbolo específico
    """
    try:
        data = request.get_json()
        days_ahead = request.args.get('days', 7, type=int)
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Se requieren datos históricos para la predicción'}), 400
        
        prediction = lstm_predictor.predict(data['data'], days_ahead)
        
        if prediction is None:
            return jsonify({'error': 'No se pudo generar la predicción LSTM'}), 500
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'model': 'LSTM',
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint predict_lstm para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@predictions_bp.route('/predictions/combined/<symbol>', methods=['POST'])
def predict_combined(symbol):
    """
    Endpoint para predicción combinada SVM + LSTM
    """
    try:
        data = request.get_json()
        days_ahead = request.args.get('days', 7, type=int)
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Se requieren datos históricos para la predicción'}), 400
        
        # Predicción SVM
        svm_result = svm_predictor.predict(data['data'])
        
        # Predicción LSTM
        lstm_result = lstm_predictor.predict(data['data'], days_ahead)
        
        if svm_result is None and lstm_result is None:
            return jsonify({'error': 'No se pudieron generar las predicciones'}), 500
        
        # Combinar resultados
        combined_signal = 'HOLD'
        confidence = 0.5
        
        if svm_result and lstm_result:
            svm_bullish = svm_result['signal'] == 'BUY'
            lstm_bullish = lstm_result['price_change_percent'] > 0
            
            if svm_bullish and lstm_bullish:
                combined_signal = 'STRONG_BUY'
                confidence = (svm_result['confidence'] + 0.7) / 2
            elif svm_bullish or lstm_bullish:
                combined_signal = 'BUY'
                confidence = 0.6
            else:
                combined_signal = 'SELL'
                confidence = 0.7
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'model': 'COMBINED',
            'svm_prediction': svm_result,
            'lstm_prediction': lstm_result,
            'combined_signal': combined_signal,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint predict_combined para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@predictions_bp.route('/predictions/batch', methods=['POST'])
def predict_batch():
    """
    Endpoint para predicciones en lote de múltiples símbolos
    """
    try:
        data = request.get_json()
        
        if not data or 'symbols_data' not in data:
            return jsonify({'error': 'Se requieren datos de múltiples símbolos'}), 400
        
        results = {}
        
        for symbol, symbol_data in data['symbols_data'].items():
            try:
                # Predicción SVM
                svm_result = svm_predictor.predict(symbol_data['data'])
                
                # Predicción LSTM
                lstm_result = lstm_predictor.predict(symbol_data['data'])
                
                results[symbol] = {
                    'svm': svm_result,
                    'lstm': lstm_result,
                    'status': 'success'
                }
                
            except Exception as e:
                results[symbol] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'results': results,
            'symbols_processed': len(results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint predict_batch: {str(e)}")
        return jsonify({'error': str(e)}), 500

@predictions_bp.route('/predictions/models/status', methods=['GET'])
def models_status():
    """
    Endpoint para verificar el estado de los modelos
    """
    return jsonify({
        'success': True,
        'models': {
            'svm': {
                'trained': svm_predictor.is_trained,
                'type': 'Support Vector Machine',
                'purpose': 'Predicción de dirección (subida/bajada)'
            },
            'lstm': {
                'trained': lstm_predictor.is_trained,
                'type': 'Long Short-Term Memory',
                'purpose': 'Pronóstico de precios futuros'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@predictions_bp.route('/predictions/models/retrain', methods=['POST'])
def retrain_models():
    """
    Endpoint para reentrenar los modelos con nuevos datos
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Se requieren datos para reentrenamiento'}), 400
        
        # Reentrenar SVM
        svm_success = svm_predictor.train(data['data'])
        
        # Reentrenar LSTM
        lstm_success = lstm_predictor.train(data['data'])
        
        return jsonify({
            'success': True,
            'retraining_results': {
                'svm': svm_success,
                'lstm': lstm_success
            },
            'message': 'Modelos reentrenados exitosamente',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en reentrenamiento de modelos: {str(e)}")
        return jsonify({'error': str(e)}), 500

