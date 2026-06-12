from datetime import datetime
from extensions import db

class Incident(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(200))
    description=db.Column(db.Text)
    severity=db.Column(db.String(20))
    status=db.Column(db.String(20), default='Open')
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
