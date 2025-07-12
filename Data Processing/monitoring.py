"""
Módulo de Monitoreo y Escalabilidad del Sistema
Implementa monitoreo de latencia, estado de APIs, consumo de recursos y alertas
"""

from flask import Blueprint, jsonify, request
import psutil
import time
import requests
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import threading
import json
from collections import deque
import yfinance as yf

monitoring_bp = Blueprint('monitoring', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Clase para métricas del sistema"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available: float
    disk_usage: float
    network_sent: int
    network_recv: int
    active_connections: int

@dataclass
class APIHealthCheck:
    """Clase para verificación de salud de APIs"""
    api_name: str
    endpoint: str
    status: str  # 'healthy', 'degraded', 'down'
    response_time: float
    status_code: int
    last_check: str
    error_message: str

@dataclass
class Alert:
    """Clase para alertas del sistema"""
    alert_id: str
    alert_type: str  # 'performance', 'api', 'resource', 'security'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: str
    resolved: bool
    resolution_time: str

class MonitoringEngine:
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Últimas 1000 métricas
        self.api_health_status = {}
        self.alerts = deque(maxlen=500)  # Últimas 500 alertas
        self.alert_thresholds = {
            'cpu_threshold': 80.0,
            'memory_threshold': 85.0,
            'disk_threshold': 90.0,
            'response_time_threshold': 5.0,
            'error_rate_threshold': 10.0
        }
        
        # APIs a monitorear
        self.monitored_apis = {
            'yahoo_finance': {
                'name': 'Yahoo Finance',
                'test_endpoint': 'https://query1.finance.yahoo.com/v8/finance/chart/AAPL',
                'timeout': 10
            },
            'internal_data': {
                'name': 'Data Ingestion',
                'test_endpoint': '/api/data/health',
                'timeout': 5
            },
            'internal_predictions': {
                'name': 'Predictions',
                'test_endpoint': '/api/predictions/health',
                'timeout': 5
            },
            'internal_auth': {
                'name': 'Authentication',
                'test_endpoint': '/api/auth/health',
                'timeout': 5
            }
        }
        
        # Iniciar monitoreo en background
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitoring)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def collect_system_metrics(self) -> SystemMetrics:
        """
        Recolecta métricas del sistema
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Red
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent
            network_recv = network.bytes_recv
            
            # Conexiones
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_percent, 2),
                memory_available=round(memory_available, 2),
                disk_usage=round(disk_usage, 2),
                network_sent=network_sent,
                network_recv=network_recv,
                active_connections=connections
            )
            
            # Almacenar en historial
            self.metrics_history.append(metrics)
            
            # Verificar umbrales y generar alertas
            self._check_resource_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error recolectando métricas del sistema: {str(e)}")
            return None
    
    def check_api_health(self, api_key: str = None) -> Dict[str, APIHealthCheck]:
        """
        Verifica la salud de las APIs
        """
        health_results = {}
        
        for api_key, api_config in self.monitored_apis.items():
            if api_key and api_key != api_key:
                continue
                
            try:
                start_time = time.time()
                
                if api_config['test_endpoint'].startswith('http'):
                    # API externa
                    response = requests.get(
                        api_config['test_endpoint'],
                        timeout=api_config['timeout']
                    )
                    status_code = response.status_code
                    error_message = ""
                else:
                    # API interna (simulada)
                    status_code = 200
                    error_message = ""
                
                response_time = (time.time() - start_time) * 1000  # ms
                
                # Determinar estado
                if status_code == 200 and response_time < self.alert_thresholds['response_time_threshold'] * 1000:
                    status = 'healthy'
                elif status_code == 200:
                    status = 'degraded'
                else:
                    status = 'down'
                    error_message = f"HTTP {status_code}"
                
                health_check = APIHealthCheck(
                    api_name=api_config['name'],
                    endpoint=api_config['test_endpoint'],
                    status=status,
                    response_time=round(response_time, 2),
                    status_code=status_code,
                    last_check=datetime.now().isoformat(),
                    error_message=error_message
                )
                
                health_results[api_key] = health_check
                self.api_health_status[api_key] = health_check
                
                # Verificar alertas de API
                self._check_api_alerts(api_key, health_check)
                
            except requests.exceptions.Timeout:
                health_check = APIHealthCheck(
                    api_name=api_config['name'],
                    endpoint=api_config['test_endpoint'],
                    status='down',
                    response_time=api_config['timeout'] * 1000,
                    status_code=0,
                    last_check=datetime.now().isoformat(),
                    error_message="Timeout"
                )
                health_results[api_key] = health_check
                self.api_health_status[api_key] = health_check
                
            except Exception as e:
                health_check = APIHealthCheck(
                    api_name=api_config['name'],
                    endpoint=api_config['test_endpoint'],
                    status='down',
                    response_time=0,
                    status_code=0,
                    last_check=datetime.now().isoformat(),
                    error_message=str(e)
                )
                health_results[api_key] = health_check
                self.api_health_status[api_key] = health_check
        
        return health_results
    
    def _check_resource_alerts(self, metrics: SystemMetrics):
        """
        Verifica umbrales de recursos y genera alertas
        """
        try:
            # Alerta de CPU
            if metrics.cpu_percent > self.alert_thresholds['cpu_threshold']:
                self._create_alert(
                    alert_type='performance',
                    severity='high' if metrics.cpu_percent > 90 else 'medium',
                    message=f"Alto uso de CPU: {metrics.cpu_percent}%"
                )
            
            # Alerta de memoria
            if metrics.memory_percent > self.alert_thresholds['memory_threshold']:
                self._create_alert(
                    alert_type='performance',
                    severity='high' if metrics.memory_percent > 95 else 'medium',
                    message=f"Alto uso de memoria: {metrics.memory_percent}%"
                )
            
            # Alerta de disco
            if metrics.disk_usage > self.alert_thresholds['disk_threshold']:
                self._create_alert(
                    alert_type='resource',
                    severity='critical' if metrics.disk_usage > 95 else 'high',
                    message=f"Poco espacio en disco: {metrics.disk_usage}%"
                )
                
        except Exception as e:
            logger.error(f"Error verificando alertas de recursos: {str(e)}")
    
    def _check_api_alerts(self, api_key: str, health_check: APIHealthCheck):
        """
        Verifica alertas de APIs
        """
        try:
            if health_check.status == 'down':
                self._create_alert(
                    alert_type='api',
                    severity='critical',
                    message=f"API {health_check.api_name} no disponible: {health_check.error_message}"
                )
            elif health_check.status == 'degraded':
                self._create_alert(
                    alert_type='api',
                    severity='medium',
                    message=f"API {health_check.api_name} con rendimiento degradado: {health_check.response_time}ms"
                )
                
        except Exception as e:
            logger.error(f"Error verificando alertas de API: {str(e)}")
    
    def _create_alert(self, alert_type: str, severity: str, message: str):
        """
        Crea una nueva alerta
        """
        try:
            # Verificar si ya existe una alerta similar reciente
            recent_alerts = [alert for alert in self.alerts 
                           if alert.message == message and not alert.resolved
                           and (datetime.now() - datetime.fromisoformat(alert.timestamp)).seconds < 300]
            
            if recent_alerts:
                return  # No duplicar alertas recientes
            
            alert = Alert(
                alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
                alert_type=alert_type,
                severity=severity,
                message=message,
                timestamp=datetime.now().isoformat(),
                resolved=False,
                resolution_time=""
            )
            
            self.alerts.append(alert)
            logger.warning(f"Nueva alerta [{severity}]: {message}")
            
        except Exception as e:
            logger.error(f"Error creando alerta: {str(e)}")
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Marca una alerta como resuelta
        """
        try:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolution_time = datetime.now().isoformat()
                    logger.info(f"Alerta resuelta: {alert_id}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error resolviendo alerta: {str(e)}")
            return False
    
    def get_system_status(self) -> Dict:
        """
        Obtiene el estado general del sistema
        """
        try:
            current_metrics = self.collect_system_metrics()
            api_health = self.check_api_health()
            
            # Contar alertas activas por severidad
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            alert_counts = {
                'critical': len([a for a in active_alerts if a.severity == 'critical']),
                'high': len([a for a in active_alerts if a.severity == 'high']),
                'medium': len([a for a in active_alerts if a.severity == 'medium']),
                'low': len([a for a in active_alerts if a.severity == 'low'])
            }
            
            # Determinar estado general
            overall_status = 'healthy'
            if alert_counts['critical'] > 0:
                overall_status = 'critical'
            elif alert_counts['high'] > 0:
                overall_status = 'degraded'
            elif alert_counts['medium'] > 0:
                overall_status = 'warning'
            
            # APIs saludables
            healthy_apis = len([api for api in api_health.values() if api.status == 'healthy'])
            total_apis = len(api_health)
            
            return {
                'overall_status': overall_status,
                'timestamp': datetime.now().isoformat(),
                'system_metrics': asdict(current_metrics) if current_metrics else None,
                'api_health': {key: asdict(value) for key, value in api_health.items()},
                'api_summary': {
                    'healthy': healthy_apis,
                    'total': total_apis,
                    'health_percentage': round((healthy_apis / total_apis) * 100, 2) if total_apis > 0 else 0
                },
                'alerts': {
                    'active_count': len(active_alerts),
                    'by_severity': alert_counts,
                    'recent_alerts': [asdict(alert) for alert in list(active_alerts)[-5:]]
                },
                'uptime': self._get_uptime(),
                'performance_summary': self._get_performance_summary()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {str(e)}")
            return {'error': str(e)}
    
    def _get_uptime(self) -> Dict:
        """
        Calcula el tiempo de actividad del sistema
        """
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return {
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'total_seconds': int(uptime_seconds)
            }
            
        except Exception as e:
            logger.error(f"Error calculando uptime: {str(e)}")
            return {'days': 0, 'hours': 0, 'minutes': 0, 'total_seconds': 0}
    
    def _get_performance_summary(self) -> Dict:
        """
        Calcula resumen de rendimiento basado en métricas históricas
        """
        try:
            if len(self.metrics_history) < 2:
                return {'avg_cpu': 0, 'avg_memory': 0, 'avg_response_time': 0}
            
            recent_metrics = list(self.metrics_history)[-60:]  # Últimos 60 registros
            
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            
            # Tiempo de respuesta promedio de APIs
            api_response_times = []
            for api_health in self.api_health_status.values():
                if api_health.response_time > 0:
                    api_response_times.append(api_health.response_time)
            
            avg_response_time = sum(api_response_times) / len(api_response_times) if api_response_times else 0
            
            return {
                'avg_cpu': round(avg_cpu, 2),
                'avg_memory': round(avg_memory, 2),
                'avg_response_time': round(avg_response_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculando resumen de rendimiento: {str(e)}")
            return {'avg_cpu': 0, 'avg_memory': 0, 'avg_response_time': 0}
    
    def _background_monitoring(self):
        """
        Monitoreo en background
        """
        while self.monitoring_active:
            try:
                # Recolectar métricas cada 30 segundos
                self.collect_system_metrics()
                
                # Verificar APIs cada 60 segundos
                if int(time.time()) % 60 == 0:
                    self.check_api_health()
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error en monitoreo background: {str(e)}")
                time.sleep(60)
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict]:
        """
        Obtiene historial de métricas
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_metrics = []
            for metric in self.metrics_history:
                metric_time = datetime.fromisoformat(metric.timestamp)
                if metric_time >= cutoff_time:
                    filtered_metrics.append(asdict(metric))
            
            return filtered_metrics
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de métricas: {str(e)}")
            return []
    
    def get_alerts_history(self, hours: int = 24, severity: str = None) -> List[Dict]:
        """
        Obtiene historial de alertas
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_alerts = []
            for alert in self.alerts:
                alert_time = datetime.fromisoformat(alert.timestamp)
                if alert_time >= cutoff_time:
                    if severity is None or alert.severity == severity:
                        filtered_alerts.append(asdict(alert))
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de alertas: {str(e)}")
            return []

# Instancia global del motor de monitoreo
monitoring_engine = MonitoringEngine()

@monitoring_bp.route('/monitoring/status', methods=['GET'])
def get_system_status():
    """
    Endpoint para obtener el estado general del sistema
    """
    try:
        status = monitoring_engine.get_system_status()
        
        if 'error' in status:
            return jsonify(status), 500
        
        return jsonify({
            'success': True,
            'system_status': status
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_system_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/metrics', methods=['GET'])
def get_current_metrics():
    """
    Endpoint para obtener métricas actuales del sistema
    """
    try:
        metrics = monitoring_engine.collect_system_metrics()
        
        if not metrics:
            return jsonify({'error': 'No se pudieron obtener las métricas'}), 500
        
        return jsonify({
            'success': True,
            'metrics': asdict(metrics)
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_current_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/metrics/history', methods=['GET'])
def get_metrics_history():
    """
    Endpoint para obtener historial de métricas
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if hours > 168:  # Máximo 1 semana
            hours = 168
        
        history = monitoring_engine.get_metrics_history(hours)
        
        return jsonify({
            'success': True,
            'metrics_history': history,
            'period_hours': hours,
            'total_records': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_metrics_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/api-health', methods=['GET'])
def get_api_health():
    """
    Endpoint para verificar la salud de las APIs
    """
    try:
        api_key = request.args.get('api')
        health_results = monitoring_engine.check_api_health(api_key)
        
        return jsonify({
            'success': True,
            'api_health': {key: asdict(value) for key, value in health_results.items()},
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_api_health: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/alerts', methods=['GET'])
def get_alerts():
    """
    Endpoint para obtener alertas
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        severity = request.args.get('severity')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        if active_only:
            alerts = [asdict(alert) for alert in monitoring_engine.alerts if not alert.resolved]
        else:
            alerts = monitoring_engine.get_alerts_history(hours, severity)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'filters': {
                'hours': hours if not active_only else None,
                'severity': severity,
                'active_only': active_only
            }
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """
    Endpoint para resolver una alerta
    """
    try:
        success = monitoring_engine.resolve_alert(alert_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Alerta {alert_id} resuelta exitosamente'
            })
        else:
            return jsonify({
                'error': f'No se pudo resolver la alerta {alert_id}'
            }), 404
        
    except Exception as e:
        logger.error(f"Error en endpoint resolve_alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/thresholds', methods=['GET'])
def get_alert_thresholds():
    """
    Endpoint para obtener umbrales de alertas
    """
    return jsonify({
        'success': True,
        'thresholds': monitoring_engine.alert_thresholds
    })

@monitoring_bp.route('/monitoring/thresholds', methods=['PUT'])
def update_alert_thresholds():
    """
    Endpoint para actualizar umbrales de alertas
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Se requieren datos para actualizar'}), 400
        
        # Validar y actualizar umbrales
        valid_thresholds = ['cpu_threshold', 'memory_threshold', 'disk_threshold', 
                          'response_time_threshold', 'error_rate_threshold']
        
        updated = {}
        for key, value in data.items():
            if key in valid_thresholds and isinstance(value, (int, float)) and value > 0:
                monitoring_engine.alert_thresholds[key] = float(value)
                updated[key] = value
        
        if updated:
            logger.info(f"Umbrales de alertas actualizados: {updated}")
            return jsonify({
                'success': True,
                'message': 'Umbrales actualizados exitosamente',
                'updated_thresholds': updated
            })
        else:
            return jsonify({'error': 'No se actualizaron umbrales válidos'}), 400
        
    except Exception as e:
        logger.error(f"Error en endpoint update_alert_thresholds: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/monitoring/health', methods=['GET'])
def monitoring_health_check():
    """
    Endpoint para verificar el estado del módulo de monitoreo
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'monitoring_active': monitoring_engine.monitoring_active,
        'metrics_collected': len(monitoring_engine.metrics_history),
        'apis_monitored': len(monitoring_engine.monitored_apis),
        'active_alerts': len([a for a in monitoring_engine.alerts if not a.resolved]),
        'timestamp': datetime.now().isoformat()
    })

