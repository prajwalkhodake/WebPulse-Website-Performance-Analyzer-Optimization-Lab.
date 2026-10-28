"""
Main Public Routes
Serves marketing, documentation, and conceptual architecture pages.
"""
from flask import render_template
from app.main import main_bp


@main_bp.route('/')
def index():
    """WebPulse portfolio landing page."""
    return render_template('main/index.html', title='WebPulse — Website Performance Analyzer & Optimization Lab')


@main_bp.route('/features')
def features():
    """Features overview and architectural capabilities."""
    return render_template('main/features.html', title='Features & Capabilities')


@main_bp.route('/about')
def about():
    """Academic project background, problem statement, and engineering rationale."""
    return render_template('main/about.html', title='About WebPulse & Architecture')
