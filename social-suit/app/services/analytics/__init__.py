# Analytics package initialization

# Import main classes for easier access
from social_suit.app.services.analytics.data_collector import AnalyticsCollector
from social_suit.app.services.analytics.data_analyzer import AnalyticsAnalyzer
from social_suit.app.services.analytics.chart_generator import ChartGenerator

# Import services subpackage
from social_suit.app.services.analytics.services import collect_all_platform_data, AnalyticsCollectorService, AnalyticsAnalyzerService, ChartGeneratorService