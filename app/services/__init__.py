"""
WebPulse Services Package
Exposes core analysis, validation, browser testing, and reporting modules.
"""

from app.services.archive_validator import ArchiveValidator, ValidationError
from app.services.project_detector import ProjectDetector, get_file_category
from app.services.static_analyzer import StaticAnalyzer
from app.services.dependency_mapper import DependencyMapper
from app.services.browser_runner import BrowserRunner
from app.services.recommendation_engine import RecommendationEngine
from app.services.report_generator import ReportGenerator, VersionComparator
from app.services.sample_project_seeder import create_sample_project_v1_zip, create_sample_project_v2_zip

__all__ = [
    'ArchiveValidator',
    'ValidationError',
    'ProjectDetector',
    'get_file_category',
    'StaticAnalyzer',
    'DependencyMapper',
    'BrowserRunner',
    'RecommendationEngine',
    'ReportGenerator',
    'VersionComparator',
    'create_sample_project_v1_zip',
    'create_sample_project_v2_zip'
]
