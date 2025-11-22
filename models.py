from flask_sqlalchemy import SQLAlchemy # this import the databse
from datetime import datetime

db = SQLAlchemy() # to get the database / schema

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True) # unique indentifier
    first_name = db.Column(db.String(50), nullable=True)  # username first_name
    last_name = db.Column(db.String(50), nullable=True) # username last_name
    user_role = db.Column(db.String(50), nullable=True) # user role
    user_email = db.Column(db.String(255), nullable=True) # user email
    user_password = db.Column(db.Integer(50), nullable=True) # user password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # excat time it created



