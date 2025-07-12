"""
Módulo de Análisis de Noticias con NLP
Implementa extracción de noticias financieras, análisis de sentimiento y detección de eventos clave
"""

from flask import Blueprint, jsonify, request
import feedparser
import requests
from datetime import datetime, timedelta
import logging
from textblob import TextBlob
import nltk
import re
from collections import Counter
import json

news_bp = Blueprint('news', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Descargar recursos de NLTK necesarios
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

class NewsAnalyzer:
    def __init__(self):
        self.news_sources = {
            'marketwatch': 'https://feeds.marketwatch.com/marketwatch/topstories/',
            'cnbc': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
            'reuters_business': 'https://feeds.reuters.com/reuters/businessNews',
            'yahoo_finance': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'seeking_alpha': 'https://seekingalpha.com/feed.xml'
        }
        
        self.financial_keywords = {
            'bullish': ['rally', 'surge', 'gain', 'rise', 'up', 'bull', 'positive', 'growth', 'increase', 'strong'],
            'bearish': ['fall', 'drop', 'decline', 'down', 'bear', 'negative', 'loss', 'decrease', 'weak', 'crash'],
            'neutral': ['stable', 'flat', 'unchanged', 'sideways', 'consolidate', 'range'],
            'volatility': ['volatile', 'swing', 'fluctuate', 'uncertain', 'turbulent'],
            'events': ['earnings', 'merger', 'acquisition', 'ipo', 'dividend', 'split', 'buyback', 'guidance']
        }
        
        self.news_cache = {}
        self.cache_duration = 300  # 5 minutos
        
    def fetch_rss_news(self, source_name, max_articles=50):
        """
        Obtiene noticias de una fuente RSS específica
        """
        try:
            if source_name not in self.news_sources:
                logger.warning(f"Fuente de noticias no soportada: {source_name}")
                return []
            
            url = self.news_sources[source_name]
            
            # Verificar cache
            cache_key = f"{source_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.news_cache:
                return self.news_cache[cache_key]
            
            # Obtener feed RSS
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Error parsing RSS feed from {source_name}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:max_articles]:
                try:
                    article = {
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': source_name,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Limpiar HTML del resumen
                    article['summary'] = self.clean_html(article['summary'])
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error procesando artículo de {source_name}: {str(e)}")
                    continue
            
            # Guardar en cache
            self.news_cache[cache_key] = articles
            
            logger.info(f"Obtenidos {len(articles)} artículos de {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo noticias de {source_name}: {str(e)}")
            return []
    
    def clean_html(self, text):
        """
        Limpia etiquetas HTML del texto
        """
        if not text:
            return ""
        
        # Remover etiquetas HTML
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        
        # Decodificar entidades HTML comunes
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        return text.strip()
    
    def analyze_sentiment(self, text):
        """
        Analiza el sentimiento de un texto usando TextBlob
        """
        try:
            if not text:
                return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Clasificar sentimiento
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'polarity': round(polarity, 3),
                'subjectivity': round(subjectivity, 3),
                'sentiment': sentiment
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
    
    def detect_financial_keywords(self, text):
        """
        Detecta palabras clave financieras en el texto
        """
        if not text:
            return {}
        
        text_lower = text.lower()
        detected = {}
        
        for category, keywords in self.financial_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                detected[category] = found_keywords
        
        return detected
    
    def extract_stock_symbols(self, text):
        """
        Extrae símbolos de acciones del texto (formato $SYMBOL o SYMBOL:)
        """
        if not text:
            return []
        
        # Patrones para símbolos de acciones
        patterns = [
            r'\$([A-Z]{1,5})',  # $AAPL
            r'\b([A-Z]{1,5}):\b',  # AAPL:
            r'\b([A-Z]{2,5})\s+(?:stock|shares|equity)',  # AAPL stock
        ]
        
        symbols = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            symbols.update([match.upper() for match in matches])
        
        # Filtrar símbolos comunes que no son acciones
        exclude = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HAS'}
        symbols = [s for s in symbols if s not in exclude and len(s) >= 2]
        
        return list(symbols)
    
    def analyze_article(self, article):
        """
        Analiza un artículo completo
        """
        try:
            full_text = f"{article.get('title', '')} {article.get('summary', '')}"
            
            # Análisis de sentimiento
            sentiment = self.analyze_sentiment(full_text)
            
            # Detección de palabras clave
            keywords = self.detect_financial_keywords(full_text)
            
            # Extracción de símbolos
            symbols = self.extract_stock_symbols(full_text)
            
            # Calcular score de relevancia
            relevance_score = self.calculate_relevance_score(keywords, symbols, sentiment)
            
            analysis = {
                'sentiment': sentiment,
                'keywords': keywords,
                'symbols': symbols,
                'relevance_score': relevance_score,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando artículo: {str(e)}")
            return {}
    
    def calculate_relevance_score(self, keywords, symbols, sentiment):
        """
        Calcula un score de relevancia para el artículo
        """
        score = 0
        
        # Puntos por palabras clave
        for category, kw_list in keywords.items():
            if category in ['bullish', 'bearish']:
                score += len(kw_list) * 2
            elif category == 'events':
                score += len(kw_list) * 3
            else:
                score += len(kw_list)
        
        # Puntos por símbolos encontrados
        score += len(symbols) * 2
        
        # Puntos por intensidad del sentimiento
        score += abs(sentiment.get('polarity', 0)) * 5
        
        return min(score, 10)  # Máximo 10
    
    def get_aggregated_news(self, sources=None, max_articles_per_source=20):
        """
        Obtiene noticias agregadas de múltiples fuentes
        """
        if sources is None:
            sources = list(self.news_sources.keys())
        
        all_articles = []
        
        for source in sources:
            articles = self.fetch_rss_news(source, max_articles_per_source)
            
            # Analizar cada artículo
            for article in articles:
                analysis = self.analyze_article(article)
                article['analysis'] = analysis
                all_articles.append(article)
        
        # Ordenar por relevancia y fecha
        all_articles.sort(key=lambda x: (
            x.get('analysis', {}).get('relevance_score', 0),
            x.get('published', '')
        ), reverse=True)
        
        return all_articles
    
    def get_sentiment_summary(self, articles):
        """
        Genera un resumen del sentimiento general
        """
        if not articles:
            return {}
        
        sentiments = [article.get('analysis', {}).get('sentiment', {}).get('sentiment', 'neutral') for article in articles]
        sentiment_counts = Counter(sentiments)
        
        total = len(sentiments)
        summary = {
            'total_articles': total,
            'sentiment_distribution': {
                'positive': sentiment_counts.get('positive', 0),
                'negative': sentiment_counts.get('negative', 0),
                'neutral': sentiment_counts.get('neutral', 0)
            },
            'sentiment_percentages': {
                'positive': round((sentiment_counts.get('positive', 0) / total) * 100, 1),
                'negative': round((sentiment_counts.get('negative', 0) / total) * 100, 1),
                'neutral': round((sentiment_counts.get('neutral', 0) / total) * 100, 1)
            }
        }
        
        # Determinar sentimiento general
        if summary['sentiment_percentages']['positive'] > 50:
            summary['overall_sentiment'] = 'bullish'
        elif summary['sentiment_percentages']['negative'] > 50:
            summary['overall_sentiment'] = 'bearish'
        else:
            summary['overall_sentiment'] = 'neutral'
        
        return summary

# Instancia global del analizador
news_analyzer = NewsAnalyzer()

@news_bp.route('/news/latest', methods=['GET'])
def get_latest_news():
    """
    Endpoint para obtener las últimas noticias financieras
    """
    try:
        sources = request.args.get('sources', '').split(',') if request.args.get('sources') else None
        max_articles = request.args.get('max_articles', 50, type=int)
        
        if sources:
            sources = [s.strip() for s in sources if s.strip() in news_analyzer.news_sources]
        
        articles = news_analyzer.get_aggregated_news(sources, max_articles // len(sources or news_analyzer.news_sources))
        
        return jsonify({
            'success': True,
            'articles': articles[:max_articles],
            'total_articles': len(articles),
            'sources_used': sources or list(news_analyzer.news_sources.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_latest_news: {str(e)}")
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/sentiment', methods=['GET'])
def get_sentiment_analysis():
    """
    Endpoint para obtener análisis de sentimiento general
    """
    try:
        sources = request.args.get('sources', '').split(',') if request.args.get('sources') else None
        max_articles = request.args.get('max_articles', 100, type=int)
        
        articles = news_analyzer.get_aggregated_news(sources, max_articles // len(sources or news_analyzer.news_sources))
        sentiment_summary = news_analyzer.get_sentiment_summary(articles)
        
        return jsonify({
            'success': True,
            'sentiment_summary': sentiment_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_sentiment_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/symbol/<symbol>', methods=['GET'])
def get_news_for_symbol(symbol):
    """
    Endpoint para obtener noticias específicas de un símbolo
    """
    try:
        symbol = symbol.upper()
        max_articles = request.args.get('max_articles', 50, type=int)
        
        # Obtener todas las noticias
        all_articles = news_analyzer.get_aggregated_news()
        
        # Filtrar por símbolo
        symbol_articles = []
        for article in all_articles:
            symbols = article.get('analysis', {}).get('symbols', [])
            title_text = f"{article.get('title', '')} {article.get('summary', '')}"
            
            if symbol in symbols or symbol in title_text.upper():
                symbol_articles.append(article)
        
        # Limitar resultados
        symbol_articles = symbol_articles[:max_articles]
        
        # Generar resumen de sentimiento para el símbolo
        sentiment_summary = news_analyzer.get_sentiment_summary(symbol_articles)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'articles': symbol_articles,
            'sentiment_summary': sentiment_summary,
            'total_articles': len(symbol_articles),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_news_for_symbol para {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/analyze', methods=['POST'])
def analyze_custom_text():
    """
    Endpoint para analizar texto personalizado
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Se requiere texto para analizar'}), 400
        
        text = data['text']
        
        # Crear artículo temporal
        article = {
            'title': data.get('title', ''),
            'summary': text
        }
        
        analysis = news_analyzer.analyze_article(article)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint analyze_custom_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/sources', methods=['GET'])
def get_news_sources():
    """
    Endpoint para obtener las fuentes de noticias disponibles
    """
    return jsonify({
        'success': True,
        'sources': news_analyzer.news_sources,
        'total_sources': len(news_analyzer.news_sources)
    })

@news_bp.route('/news/keywords', methods=['GET'])
def get_financial_keywords():
    """
    Endpoint para obtener las palabras clave financieras utilizadas
    """
    return jsonify({
        'success': True,
        'keywords': news_analyzer.financial_keywords,
        'categories': list(news_analyzer.financial_keywords.keys())
    })

@news_bp.route('/news/alerts', methods=['GET'])
def get_news_alerts():
    """
    Endpoint para obtener alertas basadas en noticias importantes
    """
    try:
        threshold = request.args.get('threshold', 7, type=int)
        max_alerts = request.args.get('max_alerts', 10, type=int)
        
        # Obtener noticias recientes
        articles = news_analyzer.get_aggregated_news()
        
        # Filtrar artículos con alta relevancia
        alerts = []
        for article in articles:
            relevance = article.get('analysis', {}).get('relevance_score', 0)
            if relevance >= threshold:
                alert = {
                    'title': article.get('title', ''),
                    'summary': article.get('summary', '')[:200] + '...',
                    'source': article.get('source', ''),
                    'link': article.get('link', ''),
                    'relevance_score': relevance,
                    'sentiment': article.get('analysis', {}).get('sentiment', {}),
                    'symbols': article.get('analysis', {}).get('symbols', []),
                    'timestamp': article.get('timestamp', '')
                }
                alerts.append(alert)
        
        # Ordenar por relevancia
        alerts.sort(key=lambda x: x['relevance_score'], reverse=True)
        alerts = alerts[:max_alerts]
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'threshold_used': threshold,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint get_news_alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/health', methods=['GET'])
def news_health_check():
    """
    Endpoint para verificar el estado del módulo de noticias
    """
    try:
        # Probar una fuente de noticias
        test_articles = news_analyzer.fetch_rss_news('marketwatch', 5)
        
        status = 'healthy' if test_articles else 'degraded'
        
        return jsonify({
            'success': True,
            'status': status,
            'sources_available': len(news_analyzer.news_sources),
            'test_articles_fetched': len(test_articles),
            'cache_size': len(news_analyzer.news_cache),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en news health check: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

