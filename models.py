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
    user_password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # For commuters: which terminal they belong to
    terminal_id = db.Column(db.Integer,
                            db.ForeignKey("terminals.terminal_id"),
                            nullable=True)

    # This relationship MUST use terminal_id only
    terminal = db.relationship(
        "Terminals",
        foreign_keys=[terminal_id],
        back_populates="users"
    )

    # For operators: terminal they manage (optional, one-to-one)
    operated_terminal = db.relationship(
        "Terminals",
        foreign_keys="Terminals.operator_id",
        back_populates="operator",
        uselist=False
    )


class Terminals(db.Model):
    __tablename__ = "terminals"

    terminal_id = db.Column(db.Integer, primary_key=True)
    terminal_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # Operator that manages this terminal
    operator_id = db.Column(db.Integer,
                            db.ForeignKey("users.user_id"),
                            nullable=True)

    # Relationship to operator (User)
    operator = db.relationship(
        "User",
        foreign_keys=[operator_id],
        back_populates="operated_terminal"
    )

    # All users (commuters) assigned to this terminal.
    # IMPORTANT: tell SQLAlchemy that this relationship uses User.terminal_id
    users = db.relationship(
        "User",
        foreign_keys="User.terminal_id",
        back_populates="terminal"
    )


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


