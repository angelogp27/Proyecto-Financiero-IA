"""
Pruebas de Integración Completas del Sistema de Inversión
Verifica la funcionalidad end-to-end de todos los módulos
"""

import unittest
import requests
import json
import time
from datetime import datetime
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSystemIntegration(unittest.TestCase):
    """
    Pruebas de integración para todo el sistema
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.base_url = "http://localhost:5000/api"
        cls.test_user_data = {
            "username": "test_user_integration",
            "email": "test_integration@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Integration",
            "risk_profile": "moderate",
            "investment_experience": "intermediate",
            "initial_capital": 15000.0
        }
        cls.session_id = None
        cls.user_id = None
        
        # Esperar a que el servidor esté disponible
        cls._wait_for_server()
    
    @classmethod
    def _wait_for_server(cls, max_attempts=30):
        """Espera a que el servidor esté disponible"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.base_url}/auth/health", timeout=5)
                if response.status_code == 200:
                    print(f"Servidor disponible después de {attempt + 1} intentos")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        raise Exception("El servidor no está disponible para las pruebas")
    
    def test_01_auth_flow_complete(self):
        """Prueba el flujo completo de autenticación"""
        print("\n=== Prueba 1: Flujo de Autenticación Completo ===")
        
        # 1. Registro de usuario
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=self.test_user_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('user_id', data)
        
        TestSystemIntegration.user_id = data['user_id']
        print(f"✓ Usuario registrado: {self.user_id}")
        
        # 2. Login
        login_data = {
            "username": self.test_user_data['username'],
            "password": self.test_user_data['password']
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=login_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('session_id', data)
        
        TestSystemIntegration.session_id = data['session_id']
        print(f"✓ Login exitoso: {self.session_id}")
        
        # 3. Validar sesión
        response = requests.post(
            f"{self.base_url}/auth/validate-session",
            json={"session_id": self.session_id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('valid'))
        print("✓ Sesión validada")
    
    def test_02_data_ingestion_flow(self):
        """Prueba el flujo de ingesta de datos"""
        print("\n=== Prueba 2: Flujo de Ingesta de Datos ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/data/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de datos saludable")
        
        # 2. Obtener datos de acciones
        response = requests.get(f"{self.base_url}/data/stocks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('stocks_data', data)
        print(f"✓ Datos de acciones obtenidos: {len(data['stocks_data'])} símbolos")
        
        # 3. Obtener datos específicos de un símbolo
        response = requests.get(f"{self.base_url}/data/symbol/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('symbol_data', data)
        print("✓ Datos específicos de AAPL obtenidos")
        
        # 4. Obtener datos de criptomonedas
        response = requests.get(f"{self.base_url}/data/crypto")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Datos de criptomonedas obtenidos")
    
    def test_03_predictions_flow(self):
        """Prueba el flujo de predicciones"""
        print("\n=== Prueba 3: Flujo de Predicciones ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/predictions/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de predicciones saludable")
        
        # 2. Predicción SVM
        response = requests.get(f"{self.base_url}/predictions/svm/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('svm_prediction', data)
        print("✓ Predicción SVM para AAPL obtenida")
        
        # 3. Predicción LSTM
        response = requests.get(f"{self.base_url}/predictions/lstm/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('lstm_prediction', data)
        print("✓ Predicción LSTM para AAPL obtenida")
        
        # 4. Predicción combinada
        response = requests.get(f"{self.base_url}/predictions/combined/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('combined_prediction', data)
        print("✓ Predicción combinada para AAPL obtenida")
    
    def test_04_news_analysis_flow(self):
        """Prueba el flujo de análisis de noticias"""
        print("\n=== Prueba 4: Flujo de Análisis de Noticias ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/news/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de noticias saludable")
        
        # 2. Obtener últimas noticias
        response = requests.get(f"{self.base_url}/news/latest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('news', data)
        print(f"✓ Últimas noticias obtenidas: {len(data['news'])} artículos")
        
        # 3. Análisis de sentimiento
        response = requests.get(f"{self.base_url}/news/sentiment")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Análisis de sentimiento obtenido")
        
        # 4. Noticias específicas de símbolo
        response = requests.get(f"{self.base_url}/news/symbol/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Noticias específicas de AAPL obtenidas")
    
    def test_05_strategies_flow(self):
        """Prueba el flujo de estrategias"""
        print("\n=== Prueba 5: Flujo de Estrategias ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/strategies/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de estrategias saludable")
        
        # 2. Análisis de estrategia
        strategy_data = {
            "symbol": "AAPL",
            "strategy_type": "moderate",
            "investment_amount": 1000
        }
        
        response = requests.post(
            f"{self.base_url}/strategies/analyze",
            json=strategy_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Análisis de estrategia completado")
        
        # 3. Backtesting
        backtest_data = {
            "symbol": "AAPL",
            "strategy_type": "moderate",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10000
        }
        
        response = requests.post(
            f"{self.base_url}/strategies/backtest",
            json=backtest_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Backtesting completado")
    
    def test_06_portfolio_flow(self):
        """Prueba el flujo de gestión de portafolio"""
        print("\n=== Prueba 6: Flujo de Gestión de Portafolio ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/portfolio/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de portafolio saludable")
        
        # 2. Crear portafolio
        portfolio_data = {
            "user_id": self.user_id,
            "name": "Test Portfolio",
            "initial_cash": 10000
        }
        
        response = requests.post(
            f"{self.base_url}/portfolio/create",
            json=portfolio_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        portfolio_id = data.get('portfolio_id')
        print(f"✓ Portafolio creado: {portfolio_id}")
        
        # 3. Comprar activo
        buy_data = {
            "portfolio_id": portfolio_id,
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "market"
        }
        
        response = requests.post(
            f"{self.base_url}/portfolio/buy",
            json=buy_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Compra de AAPL ejecutada")
        
        # 4. Obtener estado del portafolio
        response = requests.get(f"{self.base_url}/portfolio/{portfolio_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Estado del portafolio obtenido")
    
    def test_07_visualization_flow(self):
        """Prueba el flujo de visualización"""
        print("\n=== Prueba 7: Flujo de Visualización ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/visualization/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de visualización saludable")
        
        # 2. Gráfico de precios
        chart_data = {
            "symbol": "AAPL",
            "chart_type": "candlestick",
            "period": "1mo"
        }
        
        response = requests.post(
            f"{self.base_url}/visualization/price-chart",
            json=chart_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Gráfico de precios generado")
        
        # 3. Gráfico de indicadores técnicos
        response = requests.post(
            f"{self.base_url}/visualization/technical-chart",
            json=chart_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Gráfico de indicadores técnicos generado")
    
    def test_08_reports_flow(self):
        """Prueba el flujo de reportes"""
        print("\n=== Prueba 8: Flujo de Reportes ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/reports/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de reportes saludable")
        
        # 2. Dashboard
        response = requests.get(f"{self.base_url}/reports/dashboard/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('dashboard', data)
        print("✓ Dashboard generado")
        
        # 3. Métricas de rendimiento
        response = requests.get(f"{self.base_url}/reports/performance/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Métricas de rendimiento obtenidas")
        
        # 4. Comparación con benchmark
        benchmark_data = {"benchmark_symbol": "SPY"}
        response = requests.post(
            f"{self.base_url}/reports/benchmark-comparison/{self.user_id}",
            json=benchmark_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Comparación con benchmark completada")
    
    def test_09_monitoring_flow(self):
        """Prueba el flujo de monitoreo"""
        print("\n=== Prueba 9: Flujo de Monitoreo ===")
        
        # 1. Verificar salud del módulo
        response = requests.get(f"{self.base_url}/monitoring/health")
        self.assertEqual(response.status_code, 200)
        print("✓ Módulo de monitoreo saludable")
        
        # 2. Estado del sistema
        response = requests.get(f"{self.base_url}/monitoring/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('system_status', data)
        print("✓ Estado del sistema obtenido")
        
        # 3. Métricas actuales
        response = requests.get(f"{self.base_url}/monitoring/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Métricas actuales obtenidas")
        
        # 4. Salud de APIs
        response = requests.get(f"{self.base_url}/monitoring/api-health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        print("✓ Salud de APIs verificada")
    
    def test_10_end_to_end_workflow(self):
        """Prueba el flujo completo end-to-end"""
        print("\n=== Prueba 10: Flujo End-to-End Completo ===")
        
        # 1. Obtener datos de mercado
        response = requests.get(f"{self.base_url}/data/symbol/TSLA")
        self.assertEqual(response.status_code, 200)
        market_data = response.json()
        print("✓ Datos de mercado obtenidos")
        
        # 2. Generar predicciones
        response = requests.get(f"{self.base_url}/predictions/combined/TSLA")
        self.assertEqual(response.status_code, 200)
        predictions = response.json()
        print("✓ Predicciones generadas")
        
        # 3. Analizar noticias
        response = requests.get(f"{self.base_url}/news/symbol/TSLA")
        self.assertEqual(response.status_code, 200)
        news_analysis = response.json()
        print("✓ Análisis de noticias completado")
        
        # 4. Generar estrategia
        strategy_data = {
            "symbol": "TSLA",
            "strategy_type": "aggressive",
            "investment_amount": 5000
        }
        
        response = requests.post(
            f"{self.base_url}/strategies/analyze",
            json=strategy_data
        )
        self.assertEqual(response.status_code, 200)
        strategy = response.json()
        print("✓ Estrategia generada")
        
        # 5. Generar visualización
        chart_data = {
            "symbol": "TSLA",
            "chart_type": "candlestick",
            "period": "3mo"
        }
        
        response = requests.post(
            f"{self.base_url}/visualization/price-chart",
            json=chart_data
        )
        self.assertEqual(response.status_code, 200)
        visualization = response.json()
        print("✓ Visualización generada")
        
        # 6. Generar reporte
        response = requests.get(f"{self.base_url}/reports/dashboard/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        report = response.json()
        print("✓ Reporte generado")
        
        print("\n🎉 Flujo end-to-end completado exitosamente")
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        if cls.session_id:
            try:
                requests.post(
                    f"{cls.base_url}/auth/logout",
                    json={"session_id": cls.session_id}
                )
                print(f"\n✓ Sesión cerrada: {cls.session_id}")
            except:
                pass

class TestSystemConsistency(unittest.TestCase):
    """
    Pruebas de consistencia del sistema con los diagramas UML
    """
    
    def test_api_endpoints_consistency(self):
        """Verifica que todos los endpoints estén disponibles"""
        print("\n=== Prueba de Consistencia: Endpoints API ===")
        
        base_url = "http://localhost:5000/api"
        
        # Endpoints esperados según el diseño
        expected_endpoints = [
            "/auth/health",
            "/data/health", 
            "/predictions/health",
            "/news/health",
            "/strategies/health",
            "/portfolio/health",
            "/visualization/health",
            "/reports/health",
            "/monitoring/health"
        ]
        
        for endpoint in expected_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                self.assertEqual(response.status_code, 200)
                print(f"✓ {endpoint}")
            except Exception as e:
                self.fail(f"Endpoint {endpoint} no disponible: {str(e)}")
    
    def test_data_structure_consistency(self):
        """Verifica la consistencia de las estructuras de datos"""
        print("\n=== Prueba de Consistencia: Estructuras de Datos ===")
        
        base_url = "http://localhost:5000/api"
        
        # Verificar estructura de respuesta de datos
        response = requests.get(f"{base_url}/data/symbol/AAPL")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verificar campos requeridos
        required_fields = ['success', 'symbol_data']
        for field in required_fields:
            self.assertIn(field, data)
        
        print("✓ Estructura de datos consistente")
    
    def test_error_handling_consistency(self):
        """Verifica el manejo consistente de errores"""
        print("\n=== Prueba de Consistencia: Manejo de Errores ===")
        
        base_url = "http://localhost:5000/api"
        
        # Probar endpoint inexistente
        response = requests.get(f"{base_url}/nonexistent/endpoint")
        self.assertEqual(response.status_code, 404)
        
        # Probar datos inválidos
        response = requests.post(
            f"{base_url}/auth/login",
            json={"invalid": "data"}
        )
        self.assertIn(response.status_code, [400, 401])
        
        print("✓ Manejo de errores consistente")

def run_integration_tests():
    """Ejecuta todas las pruebas de integración"""
    print("=" * 60)
    print("INICIANDO PRUEBAS DE INTEGRACIÓN DEL SISTEMA")
    print("=" * 60)
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar pruebas de integración
    suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemConsistency))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    success_rate = ((result.testsRun - len(result.errors) - len(result.failures)) / result.testsRun) * 100
    print(f"\nTasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 SISTEMA APROBADO - Listo para producción")
    elif success_rate >= 70:
        print("⚠️  SISTEMA PARCIALMENTE APROBADO - Requiere mejoras menores")
    else:
        print("❌ SISTEMA NO APROBADO - Requiere correcciones importantes")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)

