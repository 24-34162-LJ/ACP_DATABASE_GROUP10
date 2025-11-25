from email.policy import default
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum('player', 'operator', 'admin', name='user_roles'),
        nullable=False,
        default='player'
    )

    level = db.Column(db.Integer, nullable=False, default=1)
    xp_points = db.Column(db.Integer, nullable=False, default=0)

    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


    def __repr__(self):
        return f"<User {self.full_name}>"

class Terminal(db.Model):

    __tablename__ = "terminals"

    terminal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    terminal_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    status = db.Column (
        db.Enum('active', 'inactive', name='terminal_status'),
        nullable=False,
        default='active'
    )

    # to relationship

    origin_route = db.relationship(
        "Route",
        foreign_keys = 'Route.start_terminal_id',
        back_populates = "start_terminal"
    )
    destination_route = db.relationship(
        "Route",
        foreign_keys = 'Route.end_terminal_id',
        back_populates = "end_terminal"
    )

    origin_trip_pk = db.relationship(
        "Trip",
        foreign_keys = 'Trip.origin_terminal_id',
        back_populates = "origin_fk"
    )

    destination_trip_pk = db.relationship(
        "Trip",
        foreign_keys= 'Trip.destination_terminal_id',
        back_populates = "destination_fk"
    )


    def __repr__(self):
        return f"<terminal {self.terminal_name}>"

class Route(db.Model):

    __tablename__ = "routes"

    route_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    route_name = db.Column(db.String(100), nullable=False)

    start_terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id'),
        nullable=False
    )
    end_terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id'),
        nullable=False
    )
    estimated_time_minutes = db.Column(
        db.Integer,
        nullable=False
    )

    # to relation

    start_terminal = db.relationship(
        "Terminal",
        foreign_keys = [start_terminal_id],
        back_populates = "origin_route"
    )

    end_terminal = db.relationship(
        "Terminal",
        foreign_keys = [end_terminal_id],
        back_populates = "destination_route"
    )

    trip_pk = db.relationship(
        "Trip",
        foreign_keys = 'Trip.route_id',
        back_populates = "route_fk"
    )



# jeepneys

class Jeepney(db.Model):
    __tablename__ = "jeepneys"

    jeepney_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum('Available', 'En Route', 'Maintenance', 'Inactive'),
        nullable=False,
        default='Available'
    )

    trip_pk = db.relationship(
        "Trip",
        foreign_keys = "Trip.jeepney_id",
        back_populates = "jeepney_fk"
    )

class Trip(db.Model):
    __tablename__ = "trips"

    trip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    jeepney_id = db.Column(
        db.Integer,
        db.ForeignKey('jeepneys.jeepney_id'),
        nullable=False
    )

    route_id = db.Column(
        db.Integer,
        db.ForeignKey('routes.route_id'),
        nullable=False
    )

    origin_terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id'),
        nullable=False
    )
    destination_terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id'),
        nullable=False
    )
    departure_time = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    arrival_time = db.Column(db.DateTime, nullable=True)  # or False if required

    status = db.Column(
        db.Enum('Scheduled', 'Waiting', 'En Route', 'Arrived', 'Completed', 'Cancelled'),
        nullable=False,
        default='Scheduled'
    )

    # relationship
    jeepney_fk = db.relationship(
        "Jeepney",
        foreign_keys = [jeepney_id],
        back_populates = 'trip_pk'
    )

    route_fk = db.relationship(
        "Route",
        foreign_keys = [route_id],
        back_populates = 'trip_pk'
    )

    origin_fk = db.relationship(
        "Terminal",
        foreign_keys = [origin_terminal_id],
        back_populates = 'origin_trip_pk'
    )

    destination_fk = db.relationship(
        "Terminal",
        foreign_keys=[destination_terminal_id],
        back_populates='destination_trip_pk'
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


