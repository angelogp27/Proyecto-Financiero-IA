"""
Módulo de Estrategias de Inversión y Backtesting
Integra señales de SVM, LSTM y NLP para generar estrategias y realizar backtesting
"""

from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

strategies_bp = Blueprint('strategies', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Clase para representar una señal de trading"""
    source: str  # 'svm', 'lstm', 'nlp'
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 - 1.0
    timestamp: str
    details: Dict

@dataclass
class Trade:
    """Clase para representar una operación de trading"""
    symbol: str
    action: str  # 'BUY', 'SELL'
    quantity: int
    price: float
    timestamp: str
    strategy: str

class StrategyEngine:
    def __init__(self):
        self.strategies = {
            'conservative': {
                'name': 'Conservadora',
                'description': 'Estrategia de bajo riesgo con alta confianza requerida',
                'min_confidence': 0.8,
                'max_position_size': 0.1,  # 10% del portafolio
                'stop_loss': 0.05,  # 5%
                'take_profit': 0.15,  # 15%
                'required_signals': 2  # Mínimo 2 señales concordantes
            },
            'moderate': {
                'name': 'Moderada',
                'description': 'Estrategia equilibrada entre riesgo y retorno',
                'min_confidence': 0.6,
                'max_position_size': 0.2,  # 20% del portafolio
                'stop_loss': 0.08,  # 8%
                'take_profit': 0.25,  # 25%
                'required_signals': 1  # Mínimo 1 señal
            },
            'aggressive': {
                'name': 'Agresiva',
                'description': 'Estrategia de alto riesgo y alto retorno potencial',
                'min_confidence': 0.4,
                'max_position_size': 0.3,  # 30% del portafolio
                'stop_loss': 0.12,  # 12%
                'take_profit': 0.40,  # 40%
                'required_signals': 1  # Cualquier señal
            }
        }
        
        self.signal_weights = {
            'svm': 0.3,
            'lstm': 0.4,
            'nlp': 0.3
        }
    
    def combine_signals(self, signals: List[Signal]) -> Dict:
        """
        Combina múltiples señales para generar una recomendación final
        """
        try:
            if not signals:
                return {
                    'final_signal': 'HOLD',
                    'confidence': 0.0,
                    'reasoning': 'No hay señales disponibles'
                }
            
            # Agrupar señales por tipo
            signal_groups = {'BUY': [], 'SELL': [], 'HOLD': []}
            
            for signal in signals:
                if signal.signal_type in signal_groups:
                    signal_groups[signal.signal_type].append(signal)
            
            # Calcular scores ponderados
            buy_score = sum(s.confidence * self.signal_weights.get(s.source, 0.33) 
                           for s in signal_groups['BUY'])
            sell_score = sum(s.confidence * self.signal_weights.get(s.source, 0.33) 
                            for s in signal_groups['SELL'])
            hold_score = sum(s.confidence * self.signal_weights.get(s.source, 0.33) 
                            for s in signal_groups['HOLD'])
            
            # Determinar señal final
            scores = {'BUY': buy_score, 'SELL': sell_score, 'HOLD': hold_score}
            final_signal = max(scores, key=scores.get)
            final_confidence = scores[final_signal] / len(signals)
            
            # Generar razonamiento
            reasoning_parts = []
            for signal_type, signal_list in signal_groups.items():
                if signal_list:
                    sources = [s.source.upper() for s in signal_list]
                    reasoning_parts.append(f"{signal_type}: {', '.join(sources)}")
            
            reasoning = '; '.join(reasoning_parts)
            
            return {
                'final_signal': final_signal,
                'confidence': round(final_confidence, 3),
                'reasoning': reasoning,
                'signal_breakdown': {
                    'buy_score': round(buy_score, 3),
                    'sell_score': round(sell_score, 3),
                    'hold_score': round(hold_score, 3)
                },
                'individual_signals': [
                    {
                        'source': s.source,
                        'signal': s.signal_type,
                        'confidence': s.confidence,
                        'details': s.details
                    } for s in signals
                ]
            }
            
        except Exception as e:
            logger.error(f"Error combinando señales: {str(e)}")
            return {
                'final_signal': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'Error en análisis: {str(e)}'
            }
    
    def generate_strategy_recommendation(self, combined_signal: Dict, strategy_type: str = 'moderate') -> Dict:
        """
        Genera recomendación de estrategia basada en la señal combinada
        """
        try:
            if strategy_type not in self.strategies:
                strategy_type = 'moderate'
            
            strategy = self.strategies[strategy_type]
            signal = combined_signal['final_signal']
            confidence = combined_signal['confidence']
            
            # Verificar si cumple los criterios mínimos
            meets_criteria = (
                confidence >= strategy['min_confidence'] and
                len(combined_signal.get('individual_signals', [])) >= strategy['required_signals']
            )
            
            if not meets_criteria:
                return {
                    'action': 'HOLD',
                    'reason': 'No cumple criterios mínimos de la estrategia',
                    'strategy_used': strategy['name'],
                    'position_size': 0,
                    'stop_loss': None,
                    'take_profit': None
                }
            
            # Calcular tamaño de posición basado en confianza
            base_position_size = strategy['max_position_size']
            adjusted_position_size = base_position_size * confidence
            
            recommendation = {
                'action': signal,
                'strategy_used': strategy['name'],
                'confidence': confidence,
                'position_size': round(adjusted_position_size, 3),
                'stop_loss': strategy['stop_loss'],
                'take_profit': strategy['take_profit'],
                'reasoning': combined_signal['reasoning'],
                'risk_level': strategy_type.upper()
            }
            
            # Agregar detalles específicos según la acción
            if signal == 'BUY':
                recommendation['entry_criteria'] = 'Señales alcistas convergentes'
                recommendation['exit_strategy'] = f"Stop Loss: {strategy['stop_loss']*100}%, Take Profit: {strategy['take_profit']*100}%"
            elif signal == 'SELL':
                recommendation['entry_criteria'] = 'Señales bajistas convergentes'
                recommendation['exit_strategy'] = 'Venta inmediata recomendada'
            else:
                recommendation['entry_criteria'] = 'Mantener posición actual'
                recommendation['exit_strategy'] = 'Esperar señales más claras'
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generando recomendación de estrategia: {str(e)}")
            return {
                'action': 'HOLD',
                'reason': f'Error en generación de estrategia: {str(e)}',
                'strategy_used': 'N/A'
            }

class BacktestEngine:
    def __init__(self):
        self.trades = []
        self.portfolio_value = []
        
    def run_backtest(self, historical_data: List[Dict], signals_history: List[Dict], 
                    initial_capital: float = 10000, strategy_type: str = 'moderate') -> Dict:
        """
        Ejecuta backtesting de una estrategia
        """
        try:
            if not historical_data or not signals_history:
                return {'error': 'Datos insuficientes para backtesting'}
            
            # Inicializar variables
            capital = initial_capital
            positions = {}  # {symbol: quantity}
            trades = []
            portfolio_values = []
            
            strategy_engine = StrategyEngine()
            strategy = strategy_engine.strategies[strategy_type]
            
            # Procesar cada día
            for i, day_data in enumerate(historical_data):
                date = day_data.get('date', f'Day_{i}')
                prices = day_data.get('prices', {})
                
                # Buscar señales para este día
                day_signals = [s for s in signals_history if s.get('date') == date]
                
                # Calcular valor actual del portafolio
                portfolio_value = capital
                for symbol, quantity in positions.items():
                    if symbol in prices:
                        portfolio_value += quantity * prices[symbol]
                
                portfolio_values.append({
                    'date': date,
                    'value': portfolio_value,
                    'cash': capital,
                    'positions': positions.copy()
                })
                
                # Procesar señales del día
                for signal_data in day_signals:
                    symbol = signal_data.get('symbol')
                    if not symbol or symbol not in prices:
                        continue
                    
                    # Crear señales
                    signals = []
                    if 'svm_signal' in signal_data:
                        signals.append(Signal(
                            source='svm',
                            signal_type=signal_data['svm_signal'],
                            confidence=signal_data.get('svm_confidence', 0.5),
                            timestamp=date,
                            details=signal_data.get('svm_details', {})
                        ))
                    
                    if 'lstm_signal' in signal_data:
                        signals.append(Signal(
                            source='lstm',
                            signal_type=signal_data['lstm_signal'],
                            confidence=signal_data.get('lstm_confidence', 0.5),
                            timestamp=date,
                            details=signal_data.get('lstm_details', {})
                        ))
                    
                    if 'nlp_signal' in signal_data:
                        signals.append(Signal(
                            source='nlp',
                            signal_type=signal_data['nlp_signal'],
                            confidence=signal_data.get('nlp_confidence', 0.5),
                            timestamp=date,
                            details=signal_data.get('nlp_details', {})
                        ))
                    
                    # Combinar señales y generar recomendación
                    combined = strategy_engine.combine_signals(signals)
                    recommendation = strategy_engine.generate_strategy_recommendation(combined, strategy_type)
                    
                    # Ejecutar operación si es necesario
                    action = recommendation.get('action', 'HOLD')
                    if action == 'BUY' and capital > 0:
                        # Calcular cantidad a comprar
                        position_value = portfolio_value * recommendation.get('position_size', 0.1)
                        quantity = int(position_value / prices[symbol])
                        cost = quantity * prices[symbol]
                        
                        if cost <= capital:
                            capital -= cost
                            positions[symbol] = positions.get(symbol, 0) + quantity
                            
                            trades.append({
                                'date': date,
                                'symbol': symbol,
                                'action': 'BUY',
                                'quantity': quantity,
                                'price': prices[symbol],
                                'cost': cost,
                                'strategy': strategy_type
                            })
                    
                    elif action == 'SELL' and symbol in positions and positions[symbol] > 0:
                        # Vender toda la posición
                        quantity = positions[symbol]
                        revenue = quantity * prices[symbol]
                        capital += revenue
                        positions[symbol] = 0
                        
                        trades.append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'quantity': quantity,
                            'price': prices[symbol],
                            'revenue': revenue,
                            'strategy': strategy_type
                        })
            
            # Calcular métricas finales
            final_value = capital
            for symbol, quantity in positions.items():
                if symbol in historical_data[-1].get('prices', {}):
                    final_value += quantity * historical_data[-1]['prices'][symbol]
            
            total_return = (final_value - initial_capital) / initial_capital
            
            # Calcular Sharpe Ratio (simplificado)
            returns = []
            for i in range(1, len(portfolio_values)):
                prev_value = portfolio_values[i-1]['value']
                curr_value = portfolio_values[i]['value']
                daily_return = (curr_value - prev_value) / prev_value if prev_value > 0 else 0
                returns.append(daily_return)
            
            avg_return = np.mean(returns) if returns else 0
            std_return = np.std(returns) if returns else 0
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            
            # Calcular máximo drawdown
            peak = initial_capital
            max_drawdown = 0
            for pv in portfolio_values:
                if pv['value'] > peak:
                    peak = pv['value']
                drawdown = (peak - pv['value']) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'success': True,
                'initial_capital': initial_capital,
                'final_value': round(final_value, 2),
                'total_return': round(total_return * 100, 2),
                'total_trades': len(trades),
                'winning_trades': len([t for t in trades if t.get('revenue', 0) > t.get('cost', 0)]),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'max_drawdown': round(max_drawdown * 100, 2),
                'strategy_used': strategy_type,
                'trades': trades,
                'portfolio_evolution': portfolio_values,
                'final_positions': positions
            }
            
        except Exception as e:
            logger.error(f"Error en backtesting: {str(e)}")
            return {'error': str(e)}

# Instancias globales
strategy_engine = StrategyEngine()
backtest_engine = BacktestEngine()

@strategies_bp.route('/strategies/analyze', methods=['POST'])
def analyze_signals():
    """
    Endpoint para analizar señales y generar recomendación de estrategia
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Se requieren datos de señales'}), 400
        
        # Extraer señales
        signals = []
        
        if 'svm_prediction' in data:
            svm_data = data['svm_prediction']
            signal_type = 'BUY' if svm_data.get('signal') == 'BUY' else 'HOLD'
            signals.append(Signal(
                source='svm',
                signal_type=signal_type,
                confidence=svm_data.get('confidence', 0.5),
                timestamp=datetime.now().isoformat(),
                details=svm_data
            ))
        
        if 'lstm_prediction' in data:
            lstm_data = data['lstm_prediction']
            trend = lstm_data.get('trend', 'NEUTRAL')
            signal_type = 'BUY' if trend == 'UPWARD' else 'SELL' if trend == 'DOWNWARD' else 'HOLD'
            confidence = min(abs(lstm_data.get('price_change_percent', 0)) / 10, 1.0)
            signals.append(Signal(
                source='lstm',
                signal_type=signal_type,
                confidence=confidence,
                timestamp=datetime.now().isoformat(),
                details=lstm_data
            ))
        
        if 'news_sentiment' in data:
            news_data = data['news_sentiment']
            sentiment = news_data.get('overall_sentiment', 'neutral')
            signal_type = 'BUY' if sentiment == 'bullish' else 'SELL' if sentiment == 'bearish' else 'HOLD'
            confidence = news_data.get('confidence', 0.5)
            signals.append(Signal(
                source='nlp',
                signal_type=signal_type,
                confidence=confidence,
                timestamp=datetime.now().isoformat(),
                details=news_data
            ))
        
        # Combinar señales
        combined_signal = strategy_engine.combine_signals(signals)
        
        # Generar recomendaciones para cada tipo de estrategia
        recommendations = {}
        for strategy_type in strategy_engine.strategies.keys():
            recommendations[strategy_type] = strategy_engine.generate_strategy_recommendation(
                combined_signal, strategy_type
            )
        
        return jsonify({
            'success': True,
            'symbol': data.get('symbol', 'N/A'),
            'combined_signal': combined_signal,
            'strategy_recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint analyze_signals: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/strategies/backtest', methods=['POST'])
def run_backtest():
    """
    Endpoint para ejecutar backtesting de estrategias
    """
    try:
        data = request.get_json()
        
        if not data or 'historical_data' not in data or 'signals_history' not in data:
            return jsonify({'error': 'Se requieren datos históricos y señales para backtesting'}), 400
        
        historical_data = data['historical_data']
        signals_history = data['signals_history']
        initial_capital = data.get('initial_capital', 10000)
        strategy_type = data.get('strategy_type', 'moderate')
        
        # Ejecutar backtesting
        results = backtest_engine.run_backtest(
            historical_data, signals_history, initial_capital, strategy_type
        )
        
        if 'error' in results:
            return jsonify(results), 400
        
        return jsonify({
            'success': True,
            'backtest_results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint run_backtest: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/strategies/types', methods=['GET'])
def get_strategy_types():
    """
    Endpoint para obtener los tipos de estrategias disponibles
    """
    return jsonify({
        'success': True,
        'strategies': strategy_engine.strategies,
        'signal_weights': strategy_engine.signal_weights
    })

@strategies_bp.route('/strategies/recommend/<symbol>', methods=['POST'])
def recommend_strategy(symbol):
    """
    Endpoint para obtener recomendación de estrategia para un símbolo específico
    """
    try:
        data = request.get_json()
        strategy_type = request.args.get('strategy_type', 'moderate')
        
        if not data:
            return jsonify({'error': 'Se requieren datos de análisis'}), 400
        
        # Simular señales basadas en los datos proporcionados
        signals = []
        
        # Agregar lógica para convertir datos en señales
        # (esto se integraría con los módulos de predicción y noticias)
        
        combined_signal = strategy_engine.combine_signals(signals)
        recommendation = strategy_engine.generate_strategy_recommendation(combined_signal, strategy_type)
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'strategy_type': strategy_type,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint recommend_strategy para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/strategies/compare', methods=['POST'])
def compare_strategies():
    """
    Endpoint para comparar diferentes estrategias
    """
    try:
        data = request.get_json()
        
        if not data or 'historical_data' not in data or 'signals_history' not in data:
            return jsonify({'error': 'Se requieren datos para comparación'}), 400
        
        historical_data = data['historical_data']
        signals_history = data['signals_history']
        initial_capital = data.get('initial_capital', 10000)
        
        # Ejecutar backtesting para cada estrategia
        comparison_results = {}
        
        for strategy_type in strategy_engine.strategies.keys():
            results = backtest_engine.run_backtest(
                historical_data, signals_history, initial_capital, strategy_type
            )
            
            if 'error' not in results:
                comparison_results[strategy_type] = {
                    'final_value': results['final_value'],
                    'total_return': results['total_return'],
                    'sharpe_ratio': results['sharpe_ratio'],
                    'max_drawdown': results['max_drawdown'],
                    'total_trades': results['total_trades'],
                    'winning_trades': results['winning_trades']
                }
        
        # Determinar mejor estrategia
        best_strategy = None
        best_score = -float('inf')
        
        for strategy, metrics in comparison_results.items():
            # Score simple basado en retorno y Sharpe ratio
            score = metrics['total_return'] + (metrics['sharpe_ratio'] * 10)
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return jsonify({
            'success': True,
            'comparison_results': comparison_results,
            'best_strategy': best_strategy,
            'best_score': round(best_score, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint compare_strategies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/strategies/health', methods=['GET'])
def strategies_health_check():
    """
    Endpoint para verificar el estado del módulo de estrategias
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'available_strategies': len(strategy_engine.strategies),
        'signal_sources': list(strategy_engine.signal_weights.keys()),
        'timestamp': datetime.now().isoformat()
    })

