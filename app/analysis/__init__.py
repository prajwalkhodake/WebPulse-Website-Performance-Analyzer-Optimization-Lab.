from flask import Blueprint

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

from app.analysis import routes  # noqa: F401, E402
