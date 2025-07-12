"""
Módulo de Visualización de Resultados y Reportes
Implementa dashboards integrales, métricas financieras y reportes automatizados
"""

from flask import Blueprint, jsonify, request, send_file
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

reports_bp = Blueprint('reports', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Clase para métricas de rendimiento"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float
    beta: float
    alpha: float
    information_ratio: float

@dataclass
class BenchmarkComparison:
    """Clase para comparación con benchmark"""
    benchmark_name: str
    portfolio_return: float
    benchmark_return: float
    excess_return: float
    tracking_error: float
    correlation: float

class ReportsEngine:
    def __init__(self):
        self.benchmark_data = {
            'SPY': {'name': 'S&P 500', 'symbol': 'SPY'},
            'QQQ': {'name': 'NASDAQ 100', 'symbol': 'QQQ'},
            'VTI': {'name': 'Total Stock Market', 'symbol': 'VTI'},
            'BTC-USD': {'name': 'Bitcoin', 'symbol': 'BTC-USD'}
        }
        
        self.risk_free_rate = 0.02  # 2% anual
    
    def calculate_performance_metrics(self, portfolio_returns: List[float], 
                                    benchmark_returns: List[float] = None) -> PerformanceMetrics:
        """
        Calcula métricas de rendimiento completas
        """
        try:
            if not portfolio_returns:
                return None
            
            returns = np.array(portfolio_returns)
            
            # Retorno total y anualizado
            total_return = np.prod(1 + returns) - 1
            periods_per_year = 252  # días de trading
            annualized_return = (1 + total_return) ** (periods_per_year / len(returns)) - 1
            
            # Volatilidad (desviación estándar anualizada)
            volatility = np.std(returns) * np.sqrt(periods_per_year)
            
            # Sharpe Ratio
            excess_returns = returns - (self.risk_free_rate / periods_per_year)
            sharpe_ratio = np.mean(excess_returns) / np.std(returns) * np.sqrt(periods_per_year) if np.std(returns) > 0 else 0
            
            # Maximum Drawdown
            cumulative_returns = np.cumprod(1 + returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = np.min(drawdown)
            
            # Calmar Ratio
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Sortino Ratio (solo considera volatilidad negativa)
            negative_returns = returns[returns < 0]
            downside_deviation = np.std(negative_returns) * np.sqrt(periods_per_year) if len(negative_returns) > 0 else 0
            sortino_ratio = (annualized_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Beta y Alpha (si hay benchmark)
            beta = 0
            alpha = 0
            information_ratio = 0
            
            if benchmark_returns and len(benchmark_returns) == len(portfolio_returns):
                bench_returns = np.array(benchmark_returns)
                
                # Beta
                covariance = np.cov(returns, bench_returns)[0, 1]
                benchmark_variance = np.var(bench_returns)
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                
                # Alpha
                benchmark_annualized = (1 + np.prod(1 + bench_returns) - 1) ** (periods_per_year / len(bench_returns)) - 1
                alpha = annualized_return - (self.risk_free_rate + beta * (benchmark_annualized - self.risk_free_rate))
                
                # Information Ratio
                excess_returns_vs_benchmark = returns - bench_returns
                tracking_error = np.std(excess_returns_vs_benchmark) * np.sqrt(periods_per_year)
                information_ratio = np.mean(excess_returns_vs_benchmark) * periods_per_year / tracking_error if tracking_error > 0 else 0
            
            return PerformanceMetrics(
                total_return=round(total_return * 100, 2),
                annualized_return=round(annualized_return * 100, 2),
                volatility=round(volatility * 100, 2),
                sharpe_ratio=round(sharpe_ratio, 3),
                max_drawdown=round(max_drawdown * 100, 2),
                calmar_ratio=round(calmar_ratio, 3),
                sortino_ratio=round(sortino_ratio, 3),
                beta=round(beta, 3),
                alpha=round(alpha * 100, 2),
                information_ratio=round(information_ratio, 3)
            )
            
        except Exception as e:
            logger.error(f"Error calculando métricas de rendimiento: {str(e)}")
            return None
    
    def generate_dashboard_data(self, user_id: str, portfolio_data: Dict, 
                              historical_data: List[Dict] = None) -> Dict:
        """
        Genera datos para el dashboard integral
        """
        try:
            dashboard = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'portfolio_summary': {},
                'performance_metrics': {},
                'risk_analysis': {},
                'allocation_analysis': {},
                'recent_activity': {},
                'alerts': []
            }
            
            # Resumen del portafolio
            dashboard['portfolio_summary'] = {
                'total_value': portfolio_data.get('total_value', 0),
                'cash': portfolio_data.get('cash', 0),
                'market_value': portfolio_data.get('market_value', 0),
                'total_return': portfolio_data.get('total_return', 0),
                'total_return_percent': portfolio_data.get('total_return_percent', 0),
                'unrealized_pnl': portfolio_data.get('unrealized_pnl', 0),
                'realized_pnl': portfolio_data.get('realized_pnl', 0),
                'positions_count': portfolio_data.get('total_positions', 0)
            }
            
            # Análisis de asignación
            positions = portfolio_data.get('positions', [])
            if positions:
                # Top holdings
                top_holdings = sorted(positions, key=lambda x: x['weight'], reverse=True)[:5]
                
                # Concentración
                top_3_weight = sum(pos['weight'] for pos in top_holdings[:3])
                
                dashboard['allocation_analysis'] = {
                    'top_holdings': top_holdings,
                    'concentration_top3': round(top_3_weight, 2),
                    'cash_weight': portfolio_data.get('cash_weight', 0),
                    'equity_weight': 100 - portfolio_data.get('cash_weight', 0),
                    'diversification_score': len(positions)
                }
            
            # Análisis de riesgo
            if historical_data:
                returns = [d.get('daily_return', 0) for d in historical_data if 'daily_return' in d]
                if returns:
                    metrics = self.calculate_performance_metrics(returns)
                    if metrics:
                        dashboard['performance_metrics'] = asdict(metrics)
                        
                        # Clasificación de riesgo
                        risk_level = 'Bajo'
                        if metrics.volatility > 20:
                            risk_level = 'Alto'
                        elif metrics.volatility > 10:
                            risk_level = 'Medio'
                        
                        dashboard['risk_analysis'] = {
                            'risk_level': risk_level,
                            'volatility': metrics.volatility,
                            'max_drawdown': metrics.max_drawdown,
                            'sharpe_ratio': metrics.sharpe_ratio,
                            'var_95': self.calculate_var(returns, 0.95) if returns else 0
                        }
            
            # Actividad reciente (simulada)
            dashboard['recent_activity'] = {
                'trades_last_week': 0,
                'largest_gain': {'symbol': 'N/A', 'gain': 0},
                'largest_loss': {'symbol': 'N/A', 'loss': 0},
                'most_active_symbol': 'N/A'
            }
            
            # Alertas
            alerts = []
            
            # Alerta de concentración
            if dashboard['allocation_analysis'].get('concentration_top3', 0) > 60:
                alerts.append({
                    'type': 'warning',
                    'message': 'Alta concentración en top 3 posiciones',
                    'severity': 'medium'
                })
            
            # Alerta de efectivo
            if dashboard['allocation_analysis'].get('cash_weight', 0) > 30:
                alerts.append({
                    'type': 'info',
                    'message': 'Alto porcentaje en efectivo - considerar inversión',
                    'severity': 'low'
                })
            
            # Alerta de rendimiento
            if dashboard['portfolio_summary'].get('total_return_percent', 0) < -10:
                alerts.append({
                    'type': 'danger',
                    'message': 'Pérdidas significativas en el portafolio',
                    'severity': 'high'
                })
            
            dashboard['alerts'] = alerts
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generando datos del dashboard: {str(e)}")
            return {'error': str(e)}
    
    def calculate_var(self, returns: List[float], confidence_level: float) -> float:
        """
        Calcula Value at Risk (VaR)
        """
        try:
            if not returns:
                return 0
            
            returns_array = np.array(returns)
            var = np.percentile(returns_array, (1 - confidence_level) * 100)
            return round(var * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculando VaR: {str(e)}")
            return 0
    
    def compare_with_benchmark(self, portfolio_returns: List[float], 
                             benchmark_returns: List[float], 
                             benchmark_name: str) -> BenchmarkComparison:
        """
        Compara el portafolio con un benchmark
        """
        try:
            if not portfolio_returns or not benchmark_returns:
                return None
            
            port_returns = np.array(portfolio_returns)
            bench_returns = np.array(benchmark_returns)
            
            # Asegurar misma longitud
            min_length = min(len(port_returns), len(bench_returns))
            port_returns = port_returns[:min_length]
            bench_returns = bench_returns[:min_length]
            
            # Retornos totales
            portfolio_return = (np.prod(1 + port_returns) - 1) * 100
            benchmark_return = (np.prod(1 + bench_returns) - 1) * 100
            
            # Exceso de retorno
            excess_return = portfolio_return - benchmark_return
            
            # Tracking error
            excess_returns = port_returns - bench_returns
            tracking_error = np.std(excess_returns) * np.sqrt(252) * 100
            
            # Correlación
            correlation = np.corrcoef(port_returns, bench_returns)[0, 1]
            
            return BenchmarkComparison(
                benchmark_name=benchmark_name,
                portfolio_return=round(portfolio_return, 2),
                benchmark_return=round(benchmark_return, 2),
                excess_return=round(excess_return, 2),
                tracking_error=round(tracking_error, 2),
                correlation=round(correlation, 3)
            )
            
        except Exception as e:
            logger.error(f"Error comparando con benchmark: {str(e)}")
            return None
    
    def generate_pdf_report(self, dashboard_data: Dict, user_id: str) -> io.BytesIO:
        """
        Genera un reporte PDF
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            story.append(Paragraph("Reporte de Inversión", title_style))
            story.append(Spacer(1, 20))
            
            # Información del usuario
            story.append(Paragraph(f"Usuario: {user_id}", styles['Heading2']))
            story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Resumen del portafolio
            story.append(Paragraph("Resumen del Portafolio", styles['Heading2']))
            
            portfolio_summary = dashboard_data.get('portfolio_summary', {})
            summary_data = [
                ['Métrica', 'Valor'],
                ['Valor Total', f"${portfolio_summary.get('total_value', 0):,.2f}"],
                ['Efectivo', f"${portfolio_summary.get('cash', 0):,.2f}"],
                ['Valor de Mercado', f"${portfolio_summary.get('market_value', 0):,.2f}"],
                ['Retorno Total', f"{portfolio_summary.get('total_return_percent', 0):.2f}%"],
                ['P&L No Realizado', f"${portfolio_summary.get('unrealized_pnl', 0):,.2f}"],
                ['P&L Realizado', f"${portfolio_summary.get('realized_pnl', 0):,.2f}"],
                ['Número de Posiciones', str(portfolio_summary.get('positions_count', 0))]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Métricas de rendimiento
            performance_metrics = dashboard_data.get('performance_metrics', {})
            if performance_metrics:
                story.append(Paragraph("Métricas de Rendimiento", styles['Heading2']))
                
                metrics_data = [
                    ['Métrica', 'Valor'],
                    ['Retorno Anualizado', f"{performance_metrics.get('annualized_return', 0):.2f}%"],
                    ['Volatilidad', f"{performance_metrics.get('volatility', 0):.2f}%"],
                    ['Sharpe Ratio', f"{performance_metrics.get('sharpe_ratio', 0):.3f}"],
                    ['Máximo Drawdown', f"{performance_metrics.get('max_drawdown', 0):.2f}%"],
                    ['Calmar Ratio', f"{performance_metrics.get('calmar_ratio', 0):.3f}"],
                    ['Sortino Ratio', f"{performance_metrics.get('sortino_ratio', 0):.3f}"],
                    ['Beta', f"{performance_metrics.get('beta', 0):.3f}"],
                    ['Alpha', f"{performance_metrics.get('alpha', 0):.2f}%"]
                ]
                
                metrics_table = Table(metrics_data)
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(metrics_table)
                story.append(Spacer(1, 20))
            
            # Análisis de riesgo
            risk_analysis = dashboard_data.get('risk_analysis', {})
            if risk_analysis:
                story.append(Paragraph("Análisis de Riesgo", styles['Heading2']))
                
                risk_text = f"""
                Nivel de Riesgo: {risk_analysis.get('risk_level', 'N/A')}
                
                El portafolio presenta una volatilidad del {risk_analysis.get('volatility', 0):.2f}%, 
                con un máximo drawdown del {risk_analysis.get('max_drawdown', 0):.2f}%. 
                El Sharpe Ratio de {risk_analysis.get('sharpe_ratio', 0):.3f} indica 
                {'un buen' if risk_analysis.get('sharpe_ratio', 0) > 1 else 'un' if risk_analysis.get('sharpe_ratio', 0) > 0 else 'un pobre'} 
                rendimiento ajustado por riesgo.
                """
                
                story.append(Paragraph(risk_text, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Alertas
            alerts = dashboard_data.get('alerts', [])
            if alerts:
                story.append(Paragraph("Alertas y Recomendaciones", styles['Heading2']))
                
                for alert in alerts:
                    alert_text = f"• {alert.get('message', 'N/A')} (Severidad: {alert.get('severity', 'N/A')})"
                    story.append(Paragraph(alert_text, styles['Normal']))
                
                story.append(Spacer(1, 20))
            
            # Pie de página
            story.append(Spacer(1, 40))
            story.append(Paragraph("Este reporte fue generado automáticamente por el Sistema de Apoyo a la Toma de Decisiones de Inversión.", styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generando reporte PDF: {str(e)}")
            return None

# Instancia global del motor de reportes
reports_engine = ReportsEngine()

@reports_bp.route('/reports/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    """
    Endpoint para obtener datos del dashboard integral
    """
    try:
        # Aquí se integraría con el módulo de portafolio para obtener datos reales
        # Por ahora, usamos datos simulados
        portfolio_data = {
            'total_value': 12500.00,
            'cash': 2500.00,
            'market_value': 10000.00,
            'total_return': 2500.00,
            'total_return_percent': 25.0,
            'unrealized_pnl': 1500.00,
            'realized_pnl': 1000.00,
            'total_positions': 5,
            'cash_weight': 20.0,
            'positions': [
                {'symbol': 'AAPL', 'weight': 30.0, 'unrealized_pnl': 500.0},
                {'symbol': 'GOOGL', 'weight': 25.0, 'unrealized_pnl': 400.0},
                {'symbol': 'MSFT', 'weight': 20.0, 'unrealized_pnl': 300.0},
                {'symbol': 'TSLA', 'weight': 15.0, 'unrealized_pnl': 200.0},
                {'symbol': 'AMZN', 'weight': 10.0, 'unrealized_pnl': 100.0}
            ]
        }
        
        # Datos históricos simulados
        historical_data = [
            {'date': '2023-01-01', 'daily_return': 0.01},
            {'date': '2023-01-02', 'daily_return': -0.005},
            {'date': '2023-01-03', 'daily_return': 0.015},
            # ... más datos
        ]
        
        dashboard = reports_engine.generate_dashboard_data(user_id, portfolio_data, historical_data)
        
        if 'error' in dashboard:
            return jsonify(dashboard), 500
        
        return jsonify({
            'success': True,
            'dashboard': dashboard
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_dashboard_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/performance/<user_id>', methods=['GET'])
def get_performance_metrics(user_id):
    """
    Endpoint para obtener métricas de rendimiento detalladas
    """
    try:
        # Datos simulados de retornos
        portfolio_returns = [0.01, -0.005, 0.015, 0.008, -0.012, 0.020, 0.005, -0.008, 0.018, 0.003]
        benchmark_returns = [0.008, -0.003, 0.012, 0.006, -0.010, 0.015, 0.004, -0.006, 0.014, 0.002]
        
        metrics = reports_engine.calculate_performance_metrics(portfolio_returns, benchmark_returns)
        
        if not metrics:
            return jsonify({'error': 'No se pudieron calcular las métricas'}), 500
        
        # Comparación con benchmark
        benchmark_comparison = reports_engine.compare_with_benchmark(
            portfolio_returns, benchmark_returns, 'S&P 500'
        )
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'performance_metrics': asdict(metrics),
            'benchmark_comparison': asdict(benchmark_comparison) if benchmark_comparison else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_performance_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/benchmark-comparison/<user_id>', methods=['POST'])
def compare_with_benchmark(user_id):
    """
    Endpoint para comparar con diferentes benchmarks
    """
    try:
        data = request.get_json()
        benchmark_symbol = data.get('benchmark_symbol', 'SPY')
        
        if benchmark_symbol not in reports_engine.benchmark_data:
            return jsonify({'error': 'Benchmark no soportado'}), 400
        
        # Datos simulados
        portfolio_returns = [0.01, -0.005, 0.015, 0.008, -0.012, 0.020, 0.005, -0.008, 0.018, 0.003]
        benchmark_returns = [0.008, -0.003, 0.012, 0.006, -0.010, 0.015, 0.004, -0.006, 0.014, 0.002]
        
        benchmark_info = reports_engine.benchmark_data[benchmark_symbol]
        comparison = reports_engine.compare_with_benchmark(
            portfolio_returns, benchmark_returns, benchmark_info['name']
        )
        
        if not comparison:
            return jsonify({'error': 'No se pudo realizar la comparación'}), 500
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'benchmark_comparison': asdict(comparison),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint compare_with_benchmark: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/pdf/<user_id>', methods=['GET'])
def generate_pdf_report(user_id):
    """
    Endpoint para generar reporte PDF
    """
    try:
        # Obtener datos del dashboard
        portfolio_data = {
            'total_value': 12500.00,
            'cash': 2500.00,
            'market_value': 10000.00,
            'total_return': 2500.00,
            'total_return_percent': 25.0,
            'unrealized_pnl': 1500.00,
            'realized_pnl': 1000.00,
            'total_positions': 5,
            'cash_weight': 20.0,
            'positions': [
                {'symbol': 'AAPL', 'weight': 30.0, 'unrealized_pnl': 500.0},
                {'symbol': 'GOOGL', 'weight': 25.0, 'unrealized_pnl': 400.0}
            ]
        }
        
        dashboard = reports_engine.generate_dashboard_data(user_id, portfolio_data)
        
        if 'error' in dashboard:
            return jsonify(dashboard), 500
        
        # Generar PDF
        pdf_buffer = reports_engine.generate_pdf_report(dashboard, user_id)
        
        if not pdf_buffer:
            return jsonify({'error': 'No se pudo generar el reporte PDF'}), 500
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'reporte_inversion_{user_id}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error en endpoint generate_pdf_report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/reports/available-benchmarks', methods=['GET'])
def get_available_benchmarks():
    """
    Endpoint para obtener benchmarks disponibles
    """
    return jsonify({
        'success': True,
        'benchmarks': reports_engine.benchmark_data
    })

@reports_bp.route('/reports/health', methods=['GET'])
def reports_health_check():
    """
    Endpoint para verificar el estado del módulo de reportes
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'available_benchmarks': len(reports_engine.benchmark_data),
        'risk_free_rate': reports_engine.risk_free_rate,
        'timestamp': datetime.now().isoformat()
    })

