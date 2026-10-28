from flask import Blueprint

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')

from app.performance import routes  # noqa: F401, E402
