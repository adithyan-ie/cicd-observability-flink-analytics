from flask import Flask, render_template
from flask_login import login_required, current_user
from sqlalchemy import inspect, text
from config import Config
from extensions import db, login_manager

app=Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view='auth.login'

from models.user import User
from models.incident import Incident
from models.pipeline_event import PipelineEvent
from routes.auth import auth_bp
from routes.incidents import incident_bp
from routes.dora import dora_bp
from backend.api.observability import observability_bp

app.register_blueprint(auth_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(dora_bp)
app.register_blueprint(observability_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def dashboard():
    recent_incidents = Incident.query.order_by(Incident.created_at.desc()).limit(5).all()
    return render_template('dashboard.html',
        total=Incident.query.count(),
        open_count=Incident.query.filter_by(status='Open').count(),
        critical=Incident.query.filter_by(severity='Critical').count(),
        recent_incidents=recent_incidents,
        user=current_user)

def ensure_pipeline_event_columns():
    inspector = inspect(db.engine)
    if 'pipeline_event' not in inspector.get_table_names():
        return
    existing = {column['name'] for column in inspector.get_columns('pipeline_event')}
    column_sql = {
        'event_id': 'VARCHAR(64)',
        'repository_id': 'VARCHAR(100)',
        'status': "VARCHAR(30) DEFAULT 'SUCCESS'",
    }
    for column, definition in column_sql.items():
        if column not in existing:
            db.session.execute(text(f'ALTER TABLE pipeline_event ADD COLUMN {column} {definition}'))
    db.session.commit()

with app.app_context():
    db.create_all()
    ensure_pipeline_event_columns()

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
