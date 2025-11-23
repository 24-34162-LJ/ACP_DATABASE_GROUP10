from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_role = db.Column(db.String(50), nullable=False)
    user_email = db.Column(db.String(255), nullable=False, unique=True)
    user_password = db.Column(db.String(255), nullable=False)  # hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


"""
class Terminals(db.Model):
    terminal_id = db.Column(db.Integer, primary=True) #terminal id
    terminal_name = db.Column(db.String(100), nullable=True) # for terminal name
    terminal_location = db.Column(db.String(150), nullable=True) # terminal location
    #
    terminal_status = db.Column(db.String(50), nullable=True) # terminal status

class Routes(db.Model):
    route_id = db.Column(db.Integer, primary=True)
    route_name = db.Column(db.String(100), nullable=True)
    #
    #
    estimated_time = db.Column(db.String(50), nullable=True)
"""


