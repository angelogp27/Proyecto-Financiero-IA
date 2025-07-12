"""
Módulo de Gestión de Portafolio
Implementa la gestión completa del portafolio del usuario, cálculo de P&L, rebalanceo y simulaciones
"""

from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json

portfolio_bp = Blueprint('portfolio', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Clase para representar una posición en el portafolio"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    weight: float

@dataclass
class Transaction:
    """Clase para representar una transacción"""
    id: str
    symbol: str
    action: str  # 'BUY', 'SELL'
    quantity: int
    price: float
    total_amount: float
    timestamp: str
    fees: float = 0.0

class PortfolioManager:
    def __init__(self):
        self.portfolios = {}  # {user_id: portfolio_data}
        self.transaction_fee = 0.001  # 0.1% fee
        
    def create_portfolio(self, user_id: str, initial_cash: float = 10000) -> Dict:
        """
        Crea un nuevo portafolio para un usuario
        """
        try:
            portfolio = {
                'user_id': user_id,
                'cash': initial_cash,
                'initial_value': initial_cash,
                'positions': {},  # {symbol: position_data}
                'transactions': [],
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            self.portfolios[user_id] = portfolio
            logger.info(f"Portafolio creado para usuario {user_id} con ${initial_cash}")
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error creando portafolio para {user_id}: {str(e)}")
            return {}
    
    def get_portfolio(self, user_id: str) -> Dict:
        """
        Obtiene el portafolio de un usuario
        """
        return self.portfolios.get(user_id, {})
    
    def execute_transaction(self, user_id: str, symbol: str, action: str, 
                          quantity: int, price: float) -> Dict:
        """
        Ejecuta una transacción de compra o venta
        """
        try:
            if user_id not in self.portfolios:
                return {'error': 'Portafolio no encontrado'}
            
            portfolio = self.portfolios[user_id]
            symbol = symbol.upper()
            
            # Calcular costos
            total_amount = quantity * price
            fees = total_amount * self.transaction_fee
            
            if action.upper() == 'BUY':
                # Verificar fondos suficientes
                total_cost = total_amount + fees
                if portfolio['cash'] < total_cost:
                    return {'error': 'Fondos insuficientes'}
                
                # Ejecutar compra
                portfolio['cash'] -= total_cost
                
                if symbol in portfolio['positions']:
                    # Actualizar posición existente
                    pos = portfolio['positions'][symbol]
                    total_quantity = pos['quantity'] + quantity
                    total_cost_basis = (pos['quantity'] * pos['avg_cost']) + total_amount
                    new_avg_cost = total_cost_basis / total_quantity
                    
                    portfolio['positions'][symbol] = {
                        'quantity': total_quantity,
                        'avg_cost': new_avg_cost,
                        'last_price': price
                    }
                else:
                    # Nueva posición
                    portfolio['positions'][symbol] = {
                        'quantity': quantity,
                        'avg_cost': price,
                        'last_price': price
                    }
                
                transaction_id = f"{user_id}_{len(portfolio['transactions']) + 1}"
                transaction = Transaction(
                    id=transaction_id,
                    symbol=symbol,
                    action='BUY',
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    timestamp=datetime.now().isoformat(),
                    fees=fees
                )
                
            elif action.upper() == 'SELL':
                # Verificar posición suficiente
                if symbol not in portfolio['positions'] or portfolio['positions'][symbol]['quantity'] < quantity:
                    return {'error': 'Posición insuficiente para venta'}
                
                # Ejecutar venta
                revenue = total_amount - fees
                portfolio['cash'] += revenue
                
                # Actualizar posición
                pos = portfolio['positions'][symbol]
                pos['quantity'] -= quantity
                
                if pos['quantity'] == 0:
                    del portfolio['positions'][symbol]
                else:
                    pos['last_price'] = price
                
                transaction_id = f"{user_id}_{len(portfolio['transactions']) + 1}"
                transaction = Transaction(
                    id=transaction_id,
                    symbol=symbol,
                    action='SELL',
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    timestamp=datetime.now().isoformat(),
                    fees=fees
                )
            
            else:
                return {'error': 'Acción no válida'}
            
            # Agregar transacción al historial
            portfolio['transactions'].append(asdict(transaction))
            portfolio['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Transacción ejecutada: {action} {quantity} {symbol} @ ${price}")
            
            return {
                'success': True,
                'transaction': asdict(transaction),
                'portfolio_summary': self.get_portfolio_summary(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando transacción: {str(e)}")
            return {'error': str(e)}
    
    def update_prices(self, user_id: str, price_data: Dict[str, float]) -> Dict:
        """
        Actualiza los precios actuales de las posiciones
        """
        try:
            if user_id not in self.portfolios:
                return {'error': 'Portafolio no encontrado'}
            
            portfolio = self.portfolios[user_id]
            
            for symbol, price in price_data.items():
                symbol = symbol.upper()
                if symbol in portfolio['positions']:
                    portfolio['positions'][symbol]['last_price'] = price
            
            portfolio['last_updated'] = datetime.now().isoformat()
            
            return {'success': True, 'updated_symbols': list(price_data.keys())}
            
        except Exception as e:
            logger.error(f"Error actualizando precios: {str(e)}")
            return {'error': str(e)}
    
    def get_portfolio_summary(self, user_id: str) -> Dict:
        """
        Genera un resumen completo del portafolio
        """
        try:
            if user_id not in self.portfolios:
                return {'error': 'Portafolio no encontrado'}
            
            portfolio = self.portfolios[user_id]
            positions = []
            total_market_value = 0
            total_unrealized_pnl = 0
            
            # Calcular métricas para cada posición
            for symbol, pos_data in portfolio['positions'].items():
                quantity = pos_data['quantity']
                avg_cost = pos_data['avg_cost']
                current_price = pos_data['last_price']
                
                market_value = quantity * current_price
                cost_basis = quantity * avg_cost
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_percent = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent,
                    weight=0  # Se calculará después
                )
                
                positions.append(position)
                total_market_value += market_value
                total_unrealized_pnl += unrealized_pnl
            
            # Calcular pesos de las posiciones
            for position in positions:
                if total_market_value > 0:
                    position.weight = (position.market_value / total_market_value) * 100
            
            # Métricas del portafolio
            total_value = portfolio['cash'] + total_market_value
            total_return = total_value - portfolio['initial_value']
            total_return_percent = (total_return / portfolio['initial_value']) * 100 if portfolio['initial_value'] > 0 else 0
            
            # Calcular realized P&L de transacciones
            realized_pnl = self.calculate_realized_pnl(portfolio['transactions'])
            
            summary = {
                'user_id': user_id,
                'total_value': round(total_value, 2),
                'cash': round(portfolio['cash'], 2),
                'market_value': round(total_market_value, 2),
                'initial_value': portfolio['initial_value'],
                'total_return': round(total_return, 2),
                'total_return_percent': round(total_return_percent, 2),
                'unrealized_pnl': round(total_unrealized_pnl, 2),
                'realized_pnl': round(realized_pnl, 2),
                'cash_weight': round((portfolio['cash'] / total_value) * 100, 2) if total_value > 0 else 100,
                'positions': [asdict(pos) for pos in positions],
                'total_positions': len(positions),
                'last_updated': portfolio['last_updated']
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generando resumen de portafolio: {str(e)}")
            return {'error': str(e)}
    
    def calculate_realized_pnl(self, transactions: List[Dict]) -> float:
        """
        Calcula el P&L realizado basado en las transacciones
        """
        try:
            realized_pnl = 0
            holdings = {}  # {symbol: [(quantity, price), ...]}
            
            for trans in transactions:
                symbol = trans['symbol']
                action = trans['action']
                quantity = trans['quantity']
                price = trans['price']
                
                if symbol not in holdings:
                    holdings[symbol] = []
                
                if action == 'BUY':
                    holdings[symbol].append((quantity, price))
                elif action == 'SELL':
                    # FIFO (First In, First Out)
                    remaining_to_sell = quantity
                    
                    while remaining_to_sell > 0 and holdings[symbol]:
                        buy_quantity, buy_price = holdings[symbol][0]
                        
                        if buy_quantity <= remaining_to_sell:
                            # Vender toda la posición comprada
                            pnl = buy_quantity * (price - buy_price)
                            realized_pnl += pnl
                            remaining_to_sell -= buy_quantity
                            holdings[symbol].pop(0)
                        else:
                            # Vender parte de la posición comprada
                            pnl = remaining_to_sell * (price - buy_price)
                            realized_pnl += pnl
                            holdings[symbol][0] = (buy_quantity - remaining_to_sell, buy_price)
                            remaining_to_sell = 0
            
            return realized_pnl
            
        except Exception as e:
            logger.error(f"Error calculando P&L realizado: {str(e)}")
            return 0
    
    def suggest_rebalancing(self, user_id: str, target_allocation: Dict[str, float]) -> Dict:
        """
        Sugiere rebalanceo del portafolio según una asignación objetivo
        """
        try:
            summary = self.get_portfolio_summary(user_id)
            if 'error' in summary:
                return summary
            
            current_positions = {pos['symbol']: pos for pos in summary['positions']}
            total_value = summary['total_value']
            
            suggestions = []
            
            for symbol, target_weight in target_allocation.items():
                symbol = symbol.upper()
                target_value = total_value * (target_weight / 100)
                
                if symbol in current_positions:
                    current_value = current_positions[symbol]['market_value']
                    current_price = current_positions[symbol]['current_price']
                else:
                    current_value = 0
                    current_price = None
                
                difference = target_value - current_value
                
                if abs(difference) > total_value * 0.01:  # Solo si la diferencia es > 1%
                    if difference > 0:
                        # Necesita comprar
                        if current_price:
                            quantity = int(difference / current_price)
                            suggestions.append({
                                'symbol': symbol,
                                'action': 'BUY',
                                'quantity': quantity,
                                'estimated_cost': quantity * current_price,
                                'reason': f'Aumentar peso de {current_positions.get(symbol, {}).get("weight", 0):.1f}% a {target_weight:.1f}%'
                            })
                    else:
                        # Necesita vender
                        if symbol in current_positions:
                            current_quantity = current_positions[symbol]['quantity']
                            quantity_to_sell = int(abs(difference) / current_price)
                            quantity_to_sell = min(quantity_to_sell, current_quantity)
                            
                            suggestions.append({
                                'symbol': symbol,
                                'action': 'SELL',
                                'quantity': quantity_to_sell,
                                'estimated_revenue': quantity_to_sell * current_price,
                                'reason': f'Reducir peso de {current_positions[symbol]["weight"]:.1f}% a {target_weight:.1f}%'
                            })
            
            return {
                'success': True,
                'rebalancing_suggestions': suggestions,
                'current_allocation': {pos['symbol']: pos['weight'] for pos in summary['positions']},
                'target_allocation': target_allocation,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error sugiriendo rebalanceo: {str(e)}")
            return {'error': str(e)}
    
    def simulate_scenario(self, user_id: str, price_changes: Dict[str, float]) -> Dict:
        """
        Simula un escenario de cambios de precios en el portafolio
        """
        try:
            summary = self.get_portfolio_summary(user_id)
            if 'error' in summary:
                return summary
            
            simulated_positions = []
            simulated_total_value = summary['cash']
            
            for pos in summary['positions']:
                symbol = pos['symbol']
                current_price = pos['current_price']
                quantity = pos['quantity']
                
                # Aplicar cambio de precio
                price_change = price_changes.get(symbol, 0)
                new_price = current_price * (1 + price_change / 100)
                new_market_value = quantity * new_price
                
                # Calcular nuevo P&L
                cost_basis = quantity * pos['avg_cost']
                new_unrealized_pnl = new_market_value - cost_basis
                new_unrealized_pnl_percent = (new_unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                simulated_pos = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_cost': pos['avg_cost'],
                    'current_price': pos['current_price'],
                    'simulated_price': new_price,
                    'current_market_value': pos['market_value'],
                    'simulated_market_value': new_market_value,
                    'price_change_percent': price_change,
                    'current_unrealized_pnl': pos['unrealized_pnl'],
                    'simulated_unrealized_pnl': new_unrealized_pnl,
                    'pnl_impact': new_unrealized_pnl - pos['unrealized_pnl']
                }
                
                simulated_positions.append(simulated_pos)
                simulated_total_value += new_market_value
            
            # Calcular impacto total
            current_total_value = summary['total_value']
            total_impact = simulated_total_value - current_total_value
            total_impact_percent = (total_impact / current_total_value) * 100 if current_total_value > 0 else 0
            
            return {
                'success': True,
                'scenario_analysis': {
                    'current_total_value': current_total_value,
                    'simulated_total_value': round(simulated_total_value, 2),
                    'total_impact': round(total_impact, 2),
                    'total_impact_percent': round(total_impact_percent, 2),
                    'positions': simulated_positions,
                    'price_changes_applied': price_changes
                }
            }
            
        except Exception as e:
            logger.error(f"Error simulando escenario: {str(e)}")
            return {'error': str(e)}

# Instancia global del gestor de portafolio
portfolio_manager = PortfolioManager()

@portfolio_bp.route('/portfolio/create', methods=['POST'])
def create_portfolio():
    """
    Endpoint para crear un nuevo portafolio
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        initial_cash = data.get('initial_cash', 10000)
        
        if not user_id:
            return jsonify({'error': 'Se requiere user_id'}), 400
        
        portfolio = portfolio_manager.create_portfolio(user_id, initial_cash)
        
        if not portfolio:
            return jsonify({'error': 'Error creando portafolio'}), 500
        
        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'message': f'Portafolio creado exitosamente para {user_id}'
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_portfolio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>', methods=['GET'])
def get_portfolio_summary(user_id):
    """
    Endpoint para obtener el resumen del portafolio
    """
    try:
        summary = portfolio_manager.get_portfolio_summary(user_id)
        
        if 'error' in summary:
            return jsonify(summary), 404
        
        return jsonify({
            'success': True,
            'portfolio_summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_portfolio_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/trade', methods=['POST'])
def execute_trade():
    """
    Endpoint para ejecutar una operación de compra/venta
    """
    try:
        user_id = request.view_args['user_id']
        data = request.get_json()
        
        symbol = data.get('symbol')
        action = data.get('action')
        quantity = data.get('quantity')
        price = data.get('price')
        
        if not all([symbol, action, quantity, price]):
            return jsonify({'error': 'Se requieren symbol, action, quantity y price'}), 400
        
        result = portfolio_manager.execute_transaction(user_id, symbol, action, quantity, price)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint execute_trade: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/update-prices', methods=['POST'])
def update_portfolio_prices(user_id):
    """
    Endpoint para actualizar precios del portafolio
    """
    try:
        data = request.get_json()
        price_data = data.get('prices', {})
        
        if not price_data:
            return jsonify({'error': 'Se requieren datos de precios'}), 400
        
        result = portfolio_manager.update_prices(user_id, price_data)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # Obtener resumen actualizado
        summary = portfolio_manager.get_portfolio_summary(user_id)
        
        return jsonify({
            'success': True,
            'update_result': result,
            'updated_portfolio': summary
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint update_portfolio_prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/rebalance', methods=['POST'])
def suggest_rebalancing(user_id):
    """
    Endpoint para obtener sugerencias de rebalanceo
    """
    try:
        data = request.get_json()
        target_allocation = data.get('target_allocation', {})
        
        if not target_allocation:
            return jsonify({'error': 'Se requiere target_allocation'}), 400
        
        suggestions = portfolio_manager.suggest_rebalancing(user_id, target_allocation)
        
        if 'error' in suggestions:
            return jsonify(suggestions), 404
        
        return jsonify({
            'success': True,
            'rebalancing_analysis': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint suggest_rebalancing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/simulate', methods=['POST'])
def simulate_scenario(user_id):
    """
    Endpoint para simular escenarios de cambios de precios
    """
    try:
        data = request.get_json()
        price_changes = data.get('price_changes', {})
        
        if not price_changes:
            return jsonify({'error': 'Se requieren price_changes'}), 400
        
        simulation = portfolio_manager.simulate_scenario(user_id, price_changes)
        
        if 'error' in simulation:
            return jsonify(simulation), 404
        
        return jsonify({
            'success': True,
            'simulation_results': simulation
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint simulate_scenario: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/transactions', methods=['GET'])
def get_transaction_history(user_id):
    """
    Endpoint para obtener el historial de transacciones
    """
    try:
        portfolio = portfolio_manager.get_portfolio(user_id)
        
        if not portfolio:
            return jsonify({'error': 'Portafolio no encontrado'}), 404
        
        transactions = portfolio.get('transactions', [])
        
        # Filtros opcionales
        limit = request.args.get('limit', type=int)
        symbol_filter = request.args.get('symbol')
        action_filter = request.args.get('action')
        
        filtered_transactions = transactions
        
        if symbol_filter:
            filtered_transactions = [t for t in filtered_transactions if t['symbol'].upper() == symbol_filter.upper()]
        
        if action_filter:
            filtered_transactions = [t for t in filtered_transactions if t['action'].upper() == action_filter.upper()]
        
        if limit:
            filtered_transactions = filtered_transactions[-limit:]
        
        return jsonify({
            'success': True,
            'transactions': filtered_transactions,
            'total_transactions': len(transactions),
            'filtered_count': len(filtered_transactions)
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_transaction_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/<user_id>/performance', methods=['GET'])
def get_portfolio_performance(user_id):
    """
    Endpoint para obtener métricas de rendimiento del portafolio
    """
    try:
        summary = portfolio_manager.get_portfolio_summary(user_id)
        
        if 'error' in summary:
            return jsonify(summary), 404
        
        portfolio = portfolio_manager.get_portfolio(user_id)
        transactions = portfolio.get('transactions', [])
        
        # Calcular métricas adicionales
        total_fees_paid = sum(t.get('fees', 0) for t in transactions)
        total_trades = len(transactions)
        buy_trades = len([t for t in transactions if t['action'] == 'BUY'])
        sell_trades = len([t for t in transactions if t['action'] == 'SELL'])
        
        # Calcular diversificación (número de posiciones)
        diversification_score = len(summary['positions'])
        
        performance_metrics = {
            'total_return': summary['total_return'],
            'total_return_percent': summary['total_return_percent'],
            'unrealized_pnl': summary['unrealized_pnl'],
            'realized_pnl': summary['realized_pnl'],
            'total_fees_paid': round(total_fees_paid, 2),
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'diversification_score': diversification_score,
            'cash_allocation': summary['cash_weight'],
            'equity_allocation': 100 - summary['cash_weight'],
            'largest_position': max([pos['weight'] for pos in summary['positions']], default=0),
            'portfolio_value_evolution': summary['total_value']
        }
        
        return jsonify({
            'success': True,
            'performance_metrics': performance_metrics,
            'portfolio_summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_portfolio_performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@portfolio_bp.route('/portfolio/health', methods=['GET'])
def portfolio_health_check():
    """
    Endpoint para verificar el estado del módulo de portafolio
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'active_portfolios': len(portfolio_manager.portfolios),
        'transaction_fee': portfolio_manager.transaction_fee,
        'timestamp': datetime.now().isoformat()
    })

