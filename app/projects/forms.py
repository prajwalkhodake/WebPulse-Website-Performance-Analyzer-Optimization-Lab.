"""
Project and Version Upload Forms
Handles project creation and ZIP archive uploads.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ProjectCreateForm(FlaskForm):
    """Project creation form."""
    name = StringField(
        'Project Name',
        validators=[
            DataRequired(message='Project name is required.'),
            Length(min=2, max=100, message='Project name must be between 2 and 100 characters.')
        ],
        render_kw={'placeholder': 'e.g., Portfolio Website, E-Commerce Store'}
    )
    description = TextAreaField(
        'Project Description',
        validators=[Optional(), Length(max=1000)],
        render_kw={'placeholder': 'Optional brief overview of this web application...', 'rows': 3}
    )
    entry_point = StringField(
        'HTML Entry Point',
        validators=[Optional(), Length(max=255)],
        default='index.html',
        render_kw={'placeholder': 'index.html'}
    )
    submit = SubmitField('Create Project')


class ProjectVersionUploadForm(FlaskForm):
    """ZIP archive upload form for project versions."""
    archive = FileField(
        'Project ZIP Archive',
        validators=[
            FileRequired(message='Please choose a ZIP archive to upload.'),
            FileAllowed(['zip'], 'Only .zip archives are supported for security.')
        ]
    )
    version_label = StringField(
        'Version Label',
        validators=[Optional(), Length(max=80)],
        render_kw={'placeholder': 'e.g., v1.0 — Initial Baseline or v1.1 — Optimized Assets'}
    )
    notes = TextAreaField(
        'Version Notes / Changelog',
        validators=[Optional(), Length(max=1000)],
        render_kw={'placeholder': 'Optional notes describing code modifications or test goals...', 'rows': 2}
    )
    submit = SubmitField('Upload and Ingest Version')
