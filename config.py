import os
class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','dev-secret-key')
    SQLALCHEMY_DATABASE_URI='sqlite:///incident.db'
    SQLALCHEMY_TRACK_MODIFICATIONS=False
