import os
import sys
# DON'T CHANGE: Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
import logging

# Importar todos los blueprints
from routes.data_ingestion import data_bp
from routes.predictions import predictions_bp
from routes.news_analysis import news_bp
from routes.strategies import strategies_bp
from routes.portfolio import portfolio_bp
from routes.visualization import visualization_bp
from routes.reports import reports_bp
from routes.auth import auth_bp
from routes.monitoring import monitoring_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    
    # Configuración
    app.config['SECRET_KEY'] = 'sistema-inversion-secret-key-2024'
    app.config['DEBUG'] = True
    
    # Habilitar CORS para todas las rutas
    CORS(app, origins="*")
    
    # Registrar blueprints
    app.register_blueprint(data_bp, url_prefix='/api')
    app.register_blueprint(predictions_bp, url_prefix='/api')
    app.register_blueprint(news_bp, url_prefix='/api')
    app.register_blueprint(strategies_bp, url_prefix='/api')
    app.register_blueprint(portfolio_bp, url_prefix='/api')
    app.register_blueprint(visualization_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api')
    
    # Ruta de información general
    @app.route('/api/info')
    def api_info():
        """Información general del API"""
        return jsonify({
            'success': True,
            'name': 'Sistema de Apoyo a la Toma de Decisiones de Inversión',
            'version': '1.0.0',
            'description': 'API completa para análisis de inversiones con IA',
            'modules': [
                'Autenticación de Usuario',
                'Ingesta y Validación de Datos',
                'Predicciones con SVM y LSTM',
                'Análisis de Noticias con NLP',
                'Estrategias de Inversión y Backtesting',
                'Gestión de Portafolio',
                'Visualización de Datos',
                'Reportes y Métricas',
                'Monitoreo del Sistema'
            ],
            'endpoints': {
                'auth': '/api/auth/*',
                'data': '/api/data/*',
                'predictions': '/api/predictions/*',
                'news': '/api/news/*',
                'strategies': '/api/strategies/*',
                'portfolio': '/api/portfolio/*',
                'visualization': '/api/visualization/*',
                'reports': '/api/reports/*',
                'monitoring': '/api/monitoring/*'
            },
            'documentation': '/api/docs',
            'health_checks': {
                'auth': '/api/auth/health',
                'data': '/api/data/health',
                'predictions': '/api/predictions/health',
                'news': '/api/news/health',
                'strategies': '/api/strategies/health',
                'portfolio': '/api/portfolio/health',
                'visualization': '/api/visualization/health',
                'reports': '/api/reports/health',
                'monitoring': '/api/monitoring/health'
            }
        })
    
    @app.route('/api/docs')
    def api_documentation():
        """Documentación de la API"""
        return jsonify({
            'success': True,
            'documentation': {
                'title': 'Sistema de Apoyo a la Toma de Decisiones de Inversión - API Documentation',
                'version': '1.0.0',
                'description': 'API REST completa para análisis de inversiones utilizando inteligencia artificial',
                'modules': {
                    'auth': {
                        'description': 'Autenticación y gestión de usuarios',
                        'endpoints': {
                            'POST /api/auth/register': 'Registro de nuevos usuarios',
                            'POST /api/auth/login': 'Autenticación de usuarios',
                            'POST /api/auth/logout': 'Cierre de sesión',
                            'POST /api/auth/validate-session': 'Validación de sesiones',
                            'POST /api/auth/request-password-reset': 'Solicitud de restablecimiento',
                            'POST /api/auth/reset-password': 'Restablecimiento de contraseña',
                            'GET /api/auth/profile/<user_id>': 'Obtener perfil de usuario',
                            'PUT /api/auth/profile/<user_id>': 'Actualizar perfil de usuario'
                        }
                    },
                    'data': {
                        'description': 'Ingesta y validación de datos de mercado',
                        'endpoints': {
                            'GET /api/data/stocks': 'Datos de acciones',
                            'GET /api/data/crypto': 'Datos de criptomonedas',
                            'GET /api/data/symbol/<symbol>': 'Datos específicos de símbolo',
                            'POST /api/data/batch': 'Datos múltiples símbolos'
                        }
                    },
                    'predictions': {
                        'description': 'Predicciones con modelos SVM y LSTM',
                        'endpoints': {
                            'GET /api/predictions/svm/<symbol>': 'Predicción SVM',
                            'GET /api/predictions/lstm/<symbol>': 'Predicción LSTM',
                            'GET /api/predictions/combined/<symbol>': 'Predicción combinada',
                            'POST /api/predictions/batch': 'Predicciones múltiples'
                        }
                    },
                    'news': {
                        'description': 'Análisis de noticias con NLP',
                        'endpoints': {
                            'GET /api/news/latest': 'Últimas noticias',
                            'GET /api/news/sentiment': 'Análisis de sentimiento',
                            'GET /api/news/symbol/<symbol>': 'Noticias por símbolo',
                            'GET /api/news/alerts': 'Alertas de noticias'
                        }
                    },
                    'strategies': {
                        'description': 'Estrategias de inversión y backtesting',
                        'endpoints': {
                            'POST /api/strategies/analyze': 'Análisis de estrategia',
                            'POST /api/strategies/backtest': 'Backtesting',
                            'POST /api/strategies/compare': 'Comparación de estrategias',
                            'GET /api/strategies/recommend/<symbol>': 'Recomendaciones'
                        }
                    },
                    'portfolio': {
                        'description': 'Gestión de portafolio',
                        'endpoints': {
                            'POST /api/portfolio/create': 'Crear portafolio',
                            'GET /api/portfolio/<portfolio_id>': 'Estado del portafolio',
                            'POST /api/portfolio/buy': 'Comprar activo',
                            'POST /api/portfolio/sell': 'Vender activo',
                            'POST /api/portfolio/rebalance': 'Rebalancear portafolio'
                        }
                    },
                    'visualization': {
                        'description': 'Visualización de datos',
                        'endpoints': {
                            'POST /api/visualization/price-chart': 'Gráficos de precios',
                            'POST /api/visualization/technical-chart': 'Indicadores técnicos',
                            'POST /api/visualization/comparison-chart': 'Comparación',
                            'POST /api/visualization/portfolio-chart': 'Gráficos de portafolio'
                        }
                    },
                    'reports': {
                        'description': 'Reportes y métricas',
                        'endpoints': {
                            'GET /api/reports/dashboard/<user_id>': 'Dashboard integral',
                            'GET /api/reports/performance/<user_id>': 'Métricas de rendimiento',
                            'POST /api/reports/benchmark-comparison/<user_id>': 'Comparación con benchmark',
                            'GET /api/reports/pdf/<user_id>': 'Reporte PDF'
                        }
                    },
                    'monitoring': {
                        'description': 'Monitoreo del sistema',
                        'endpoints': {
                            'GET /api/monitoring/status': 'Estado del sistema',
                            'GET /api/monitoring/metrics': 'Métricas actuales',
                            'GET /api/monitoring/api-health': 'Salud de APIs',
                            'GET /api/monitoring/alerts': 'Alertas del sistema'
                        }
                    }
                },
                'authentication': {
                    'type': 'Session-based',
                    'description': 'Utiliza session_id obtenido del login para autenticar requests'
                },
                'response_format': {
                    'success': {
                        'success': True,
                        'data': '...'
                    },
                    'error': {
                        'success': False,
                        'error': 'Mensaje de error'
                    }
                }
            }
        })
    
    @app.route('/api/health')
    def health_check():
        """Health check general del sistema"""
        try:
            # Verificar todos los módulos
            modules_status = {}
            
            # Lista de módulos para verificar
            modules = [
                ('auth', auth_bp),
                ('data', data_bp),
                ('predictions', predictions_bp),
                ('news', news_bp),
                ('strategies', strategies_bp),
                ('portfolio', portfolio_bp),
                ('visualization', visualization_bp),
                ('reports', reports_bp),
                ('monitoring', monitoring_bp)
            ]
            
            all_healthy = True
            
            for module_name, blueprint in modules:
                try:
                    # Simular verificación de salud
                    modules_status[module_name] = {
                        'status': 'healthy',
                        'registered': True
                    }
                except Exception as e:
                    modules_status[module_name] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'registered': False
                    }
                    all_healthy = False
            
            return jsonify({
                'success': True,
                'overall_status': 'healthy' if all_healthy else 'degraded',
                'modules': modules_status,
                'timestamp': '2024-01-01T00:00:00Z'
            })
            
        except Exception as e:
            logger.error(f"Error en health check: {str(e)}")
            return jsonify({
                'success': False,
                'overall_status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Manejo de errores 404"""
        return jsonify({
            'success': False,
            'error': 'Endpoint no encontrado',
            'available_endpoints': '/api/info'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejo de errores 500"""
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500
    
    logger.info("Aplicación Flask creada exitosamente")
    logger.info("Módulos registrados: auth, data, predictions, news, strategies, portfolio, visualization, reports, monitoring")
    
    return app

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    logger.info("Iniciando Sistema de Apoyo a la Toma de Decisiones de Inversión")
    logger.info("Servidor disponible en: http://0.0.0.0:5000")
    logger.info("Documentación API: http://0.0.0.0:5000/api/docs")
    logger.info("Health Check: http://0.0.0.0:5000/api/health")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )

