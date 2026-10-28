"""
WebPulse Local Development Server Entry Point
Run directly with: python run.py or flask --app run.py run
"""
import os
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Provides automatic shell imports for flask shell."""
    return {
        'db': db,
        'User': User
    }


if __name__ == '__main__':
    # Ensure database tables exist if running locally before migration execution
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 5001))
    print(f" * WebPulse Development Server starting on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
