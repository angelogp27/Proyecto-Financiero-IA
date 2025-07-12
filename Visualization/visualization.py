"""
Módulo de Visualización de Datos del Mercado
Implementa la generación de gráficos interactivos con Plotly para análisis de mercado
"""

from flask import Blueprint, jsonify, request, send_file
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime, timedelta
import logging
import io
import base64
import json

visualization_bp = Blueprint('visualization', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketVisualizationEngine:
    def __init__(self):
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        self.chart_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'responsive': True
        }
    
    def create_price_chart(self, data: list, symbol: str, chart_type: str = 'candlestick') -> dict:
        """
        Crea un gráfico de precios (candlestick o línea)
        """
        try:
            df = pd.DataFrame(data)
            
            if df.empty:
                return {'error': 'No hay datos para generar el gráfico'}
            
            # Asegurar que tenemos una columna de fecha
            if 'Date' not in df.columns and df.index.name != 'Date':
                df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
            elif 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            
            fig = go.Figure()
            
            if chart_type == 'candlestick' and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                fig.add_trace(go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=symbol,
                    increasing_line_color=self.color_palette['success'],
                    decreasing_line_color=self.color_palette['danger']
                ))
            else:
                # Gráfico de línea
                price_col = 'Close' if 'Close' in df.columns else df.select_dtypes(include=[np.number]).columns[0]
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df[price_col],
                    mode='lines',
                    name=f'{symbol} Price',
                    line=dict(color=self.color_palette['primary'], width=2)
                ))
            
            # Configurar layout
            fig.update_layout(
                title=f'{symbol} - Gráfico de Precios',
                xaxis_title='Fecha',
                yaxis_title='Precio ($)',
                template='plotly_white',
                height=500,
                showlegend=True,
                hovermode='x unified'
            )
            
            # Configurar ejes
            fig.update_xaxes(
                rangeslider_visible=False,
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
            
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            )
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de precios: {str(e)}")
            return {'error': str(e)}
    
    def create_technical_indicators_chart(self, data: list, symbol: str) -> dict:
        """
        Crea un gráfico con indicadores técnicos
        """
        try:
            df = pd.DataFrame(data)
            
            if df.empty:
                return {'error': 'No hay datos para generar el gráfico'}
            
            # Preparar datos
            if 'Date' not in df.columns:
                df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
            else:
                df['Date'] = pd.to_datetime(df['Date'])
            
            # Crear subplots
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=(f'{symbol} - Precio y Medias Móviles', 'RSI', 'MACD'),
                row_heights=[0.6, 0.2, 0.2]
            )
            
            # Gráfico principal - Precio y medias móviles
            if 'Close' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['Close'],
                    mode='lines', name='Precio',
                    line=dict(color=self.color_palette['primary'], width=2)
                ), row=1, col=1)
            
            if 'SMA_20' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['SMA_20'],
                    mode='lines', name='SMA 20',
                    line=dict(color=self.color_palette['secondary'], width=1)
                ), row=1, col=1)
            
            if 'SMA_50' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['SMA_50'],
                    mode='lines', name='SMA 50',
                    line=dict(color=self.color_palette['warning'], width=1)
                ), row=1, col=1)
            
            # Bollinger Bands
            if all(col in df.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['BB_Upper'],
                    mode='lines', name='BB Superior',
                    line=dict(color='rgba(128,128,128,0.3)', width=1),
                    showlegend=False
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['BB_Lower'],
                    mode='lines', name='BB Inferior',
                    line=dict(color='rgba(128,128,128,0.3)', width=1),
                    fill='tonexty', fillcolor='rgba(128,128,128,0.1)',
                    showlegend=False
                ), row=1, col=1)
            
            # RSI
            if 'RSI' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['RSI'],
                    mode='lines', name='RSI',
                    line=dict(color=self.color_palette['info'], width=2)
                ), row=2, col=1)
                
                # Líneas de sobrecompra y sobreventa
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            if 'MACD' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['MACD'],
                    mode='lines', name='MACD',
                    line=dict(color=self.color_palette['primary'], width=2)
                ), row=3, col=1)
                
                if 'MACD_Signal' in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['Date'], y=df['MACD_Signal'],
                        mode='lines', name='MACD Signal',
                        line=dict(color=self.color_palette['danger'], width=1)
                    ), row=3, col=1)
                
                # Línea cero
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=3, col=1)
            
            # Configurar layout
            fig.update_layout(
                title=f'{symbol} - Análisis Técnico Completo',
                template='plotly_white',
                height=800,
                showlegend=True,
                hovermode='x unified'
            )
            
            # Configurar ejes Y
            fig.update_yaxes(title_text="Precio ($)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
            fig.update_yaxes(title_text="MACD", row=3, col=1)
            fig.update_xaxes(title_text="Fecha", row=3, col=1)
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de indicadores técnicos: {str(e)}")
            return {'error': str(e)}
    
    def create_volume_chart(self, data: list, symbol: str) -> dict:
        """
        Crea un gráfico de volumen
        """
        try:
            df = pd.DataFrame(data)
            
            if df.empty or 'Volume' not in df.columns:
                return {'error': 'No hay datos de volumen disponibles'}
            
            if 'Date' not in df.columns:
                df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
            else:
                df['Date'] = pd.to_datetime(df['Date'])
            
            # Determinar colores basados en el cambio de precio
            colors = []
            if 'Close' in df.columns and 'Open' in df.columns:
                for i in range(len(df)):
                    if df['Close'].iloc[i] >= df['Open'].iloc[i]:
                        colors.append(self.color_palette['success'])
                    else:
                        colors.append(self.color_palette['danger'])
            else:
                colors = [self.color_palette['primary']] * len(df)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['Date'],
                y=df['Volume'],
                name='Volumen',
                marker_color=colors,
                opacity=0.7
            ))
            
            # Agregar media móvil del volumen
            if len(df) >= 20:
                df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['Volume_MA'],
                    mode='lines',
                    name='Volumen MA(20)',
                    line=dict(color=self.color_palette['warning'], width=2)
                ))
            
            fig.update_layout(
                title=f'{symbol} - Análisis de Volumen',
                xaxis_title='Fecha',
                yaxis_title='Volumen',
                template='plotly_white',
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de volumen: {str(e)}")
            return {'error': str(e)}
    
    def create_comparison_chart(self, symbols_data: dict) -> dict:
        """
        Crea un gráfico de comparación entre múltiples símbolos
        """
        try:
            if not symbols_data:
                return {'error': 'No hay datos para comparar'}
            
            fig = go.Figure()
            
            for symbol, data in symbols_data.items():
                df = pd.DataFrame(data)
                
                if df.empty:
                    continue
                
                if 'Date' not in df.columns:
                    df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')
                else:
                    df['Date'] = pd.to_datetime(df['Date'])
                
                # Normalizar precios (precio inicial = 100)
                price_col = 'Close' if 'Close' in df.columns else df.select_dtypes(include=[np.number]).columns[0]
                if len(df) > 0:
                    normalized_prices = (df[price_col] / df[price_col].iloc[0]) * 100
                    
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=normalized_prices,
                        mode='lines',
                        name=symbol,
                        line=dict(width=2)
                    ))
            
            fig.update_layout(
                title='Comparación de Rendimiento (Base 100)',
                xaxis_title='Fecha',
                yaxis_title='Rendimiento Normalizado',
                template='plotly_white',
                height=500,
                showlegend=True,
                hovermode='x unified'
            )
            
            # Línea de referencia en 100
            fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de comparación: {str(e)}")
            return {'error': str(e)}
    
    def create_portfolio_allocation_chart(self, portfolio_data: dict) -> dict:
        """
        Crea un gráfico de distribución del portafolio
        """
        try:
            positions = portfolio_data.get('positions', [])
            cash_weight = portfolio_data.get('cash_weight', 0)
            
            if not positions and cash_weight == 0:
                return {'error': 'No hay datos de portafolio para visualizar'}
            
            # Preparar datos
            labels = [pos['symbol'] for pos in positions]
            values = [pos['weight'] for pos in positions]
            
            if cash_weight > 0:
                labels.append('Efectivo')
                values.append(cash_weight)
            
            # Crear gráfico de pastel
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                textinfo='label+percent',
                textposition='outside',
                marker=dict(
                    colors=px.colors.qualitative.Set3[:len(labels)]
                )
            )])
            
            fig.update_layout(
                title='Distribución del Portafolio',
                template='plotly_white',
                height=500,
                showlegend=True
            )
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de distribución de portafolio: {str(e)}")
            return {'error': str(e)}
    
    def create_performance_chart(self, performance_data: list) -> dict:
        """
        Crea un gráfico de evolución del rendimiento
        """
        try:
            if not performance_data:
                return {'error': 'No hay datos de rendimiento para visualizar'}
            
            df = pd.DataFrame(performance_data)
            
            if 'date' not in df.columns or 'value' not in df.columns:
                return {'error': 'Datos de rendimiento incompletos'}
            
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            
            # Línea de valor del portafolio
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['value'],
                mode='lines',
                name='Valor del Portafolio',
                line=dict(color=self.color_palette['primary'], width=3),
                fill='tonexty'
            ))
            
            # Línea de valor inicial (referencia)
            if len(df) > 0:
                initial_value = df['value'].iloc[0]
                fig.add_hline(
                    y=initial_value,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"Valor Inicial: ${initial_value:,.2f}"
                )
            
            fig.update_layout(
                title='Evolución del Valor del Portafolio',
                xaxis_title='Fecha',
                yaxis_title='Valor ($)',
                template='plotly_white',
                height=400,
                showlegend=True,
                hovermode='x unified'
            )
            
            return {
                'success': True,
                'chart_json': fig.to_json(),
                'chart_html': fig.to_html(include_plotlyjs='cdn', config=self.chart_config)
            }
            
        except Exception as e:
            logger.error(f"Error creando gráfico de rendimiento: {str(e)}")
            return {'error': str(e)}

# Instancia global del motor de visualización
viz_engine = MarketVisualizationEngine()

@visualization_bp.route('/visualization/price-chart', methods=['POST'])
def create_price_chart():
    """
    Endpoint para crear gráfico de precios
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data or 'symbol' not in data:
            return jsonify({'error': 'Se requieren data y symbol'}), 400
        
        chart_type = data.get('chart_type', 'candlestick')
        result = viz_engine.create_price_chart(data['data'], data['symbol'], chart_type)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_price_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/technical-chart', methods=['POST'])
def create_technical_chart():
    """
    Endpoint para crear gráfico de indicadores técnicos
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data or 'symbol' not in data:
            return jsonify({'error': 'Se requieren data y symbol'}), 400
        
        result = viz_engine.create_technical_indicators_chart(data['data'], data['symbol'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_technical_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/volume-chart', methods=['POST'])
def create_volume_chart():
    """
    Endpoint para crear gráfico de volumen
    """
    try:
        data = request.get_json()
        
        if not data or 'data' not in data or 'symbol' not in data:
            return jsonify({'error': 'Se requieren data y symbol'}), 400
        
        result = viz_engine.create_volume_chart(data['data'], data['symbol'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_volume_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/comparison-chart', methods=['POST'])
def create_comparison_chart():
    """
    Endpoint para crear gráfico de comparación
    """
    try:
        data = request.get_json()
        
        if not data or 'symbols_data' not in data:
            return jsonify({'error': 'Se requiere symbols_data'}), 400
        
        result = viz_engine.create_comparison_chart(data['symbols_data'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_comparison_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/portfolio-chart', methods=['POST'])
def create_portfolio_chart():
    """
    Endpoint para crear gráfico de distribución de portafolio
    """
    try:
        data = request.get_json()
        
        if not data or 'portfolio_data' not in data:
            return jsonify({'error': 'Se requiere portfolio_data'}), 400
        
        result = viz_engine.create_portfolio_allocation_chart(data['portfolio_data'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_portfolio_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/performance-chart', methods=['POST'])
def create_performance_chart():
    """
    Endpoint para crear gráfico de rendimiento
    """
    try:
        data = request.get_json()
        
        if not data or 'performance_data' not in data:
            return jsonify({'error': 'Se requiere performance_data'}), 400
        
        result = viz_engine.create_performance_chart(data['performance_data'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'chart': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint create_performance_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/visualization/chart-types', methods=['GET'])
def get_chart_types():
    """
    Endpoint para obtener los tipos de gráficos disponibles
    """
    chart_types = {
        'price_charts': ['candlestick', 'line'],
        'technical_charts': ['full_technical', 'rsi_only', 'macd_only'],
        'comparison_charts': ['normalized', 'absolute'],
        'portfolio_charts': ['pie', 'donut', 'bar'],
        'performance_charts': ['line', 'area']
    }
    
    return jsonify({
        'success': True,
        'available_chart_types': chart_types,
        'color_palette': viz_engine.color_palette
    })

@visualization_bp.route('/visualization/health', methods=['GET'])
def visualization_health_check():
    """
    Endpoint para verificar el estado del módulo de visualización
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'plotly_version': pio.__version__,
        'available_renderers': list(pio.renderers),
        'timestamp': datetime.now().isoformat()
    })

