from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), unique=True)
    email=db.Column(db.String(120), unique=True)
    password_hash=db.Column(db.String(255))

    def set_password(self,p):
        self.password_hash=generate_password_hash(p)

    def check_password(self,p):
        return check_password_hash(self.password_hash,p)
