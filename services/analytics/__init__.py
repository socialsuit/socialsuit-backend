# Analytics package initialization

# Import main classes for easier access
from services.analytics.data_collector import AnalyticsCollector
from services.analytics.data_analyzer import AnalyticsAnalyzer
from services.analytics.chart_generator import ChartGenerator

# Import services subpackage
from services.analytics.services import collect_all_platform_data, AnalyticsCollectorService, AnalyticsAnalyzerService, ChartGeneratorService