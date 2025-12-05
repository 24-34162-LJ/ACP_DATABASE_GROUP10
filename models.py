from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import text


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum('player', 'operator', 'viewer', 'admin', name='user_roles'),
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

    # relations (with cascade)

    favorite_pk = db.relationship(
        "Userfavorite",
        foreign_keys='Userfavorite.user_id',
        back_populates='favorite_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    notification_pk = db.relationship(
        "Notification",
        foreign_keys='Notification.user_id',
        back_populates='notification_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    audit_user_pk = db.relationship(
        "Auditlog",
        foreign_keys='Auditlog.user_id',
        back_populates='audit_user_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name}>"


class Terminal(db.Model):

    __tablename__ = "terminals"

    terminal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    terminal_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    status = db.Column(
        db.Enum('active', 'inactive', name='terminal_status'),
        nullable=False,
        default='active'
    )
    
    is_main = db.Column(db.Boolean, default=False, nullable=False)

    # to relationship

    origin_route = db.relationship(
        "Route",
        foreign_keys='Route.start_terminal_id',
        back_populates="start_terminal"
    )

    destination_route = db.relationship(
        "Route",
        foreign_keys='Route.end_terminal_id',
        back_populates="end_terminal"
    )

    origin_trip_pk = db.relationship(
        "Trip",
        foreign_keys='Trip.origin_terminal_id',
        back_populates="origin_fk"
    )

    destination_trip_pk = db.relationship(
        "Trip",
        foreign_keys='Trip.destination_terminal_id',
        back_populates="destination_fk"
    )

    terminal_jeep_pk = db.relationship(
        "TerminalJeepneys",
        foreign_keys='TerminalJeepneys.terminal_id',
        back_populates='terminal_jeep_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    favorite_terminal_pk = db.relationship(
        "Userfavorite",
        foreign_keys='Userfavorite.terminal_id',
        back_populates='favorite_terminal_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
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
        foreign_keys=[start_terminal_id],
        back_populates="origin_route"
    )

    end_terminal = db.relationship(
        "Terminal",
        foreign_keys=[end_terminal_id],
        back_populates="destination_route"
    )

    trip_pk = db.relationship(
        "Trip",
        foreign_keys='Trip.route_id',
        back_populates="route_fk",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    favorite_route_pk = db.relationship(
        "Userfavorite",
        foreign_keys='Userfavorite.route_id',
        back_populates='favorite_route_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# jeepneys

class Jeepney(db.Model):
    __tablename__ = "jeepneys"

    jeepney_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum('Available', 'En Route', 'Maintenance', 'Inactive', name='jeep_status'),
        nullable=False,
        default='Available'
    )

    trip_pk = db.relationship(
        "Trip",
        foreign_keys="Trip.jeepney_id",
        back_populates="jeepney_fk",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    jeep_jeep_pk = db.relationship(
        "TerminalJeepneys",
        foreign_keys="TerminalJeepneys.jeepney_id",
        back_populates='jeep_jeep_fk',
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Trip(db.Model):
    __tablename__ = "trips"

    trip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    jeepney_id = db.Column(
        db.Integer,
        db.ForeignKey('jeepneys.jeepney_id', ondelete="CASCADE"),
        nullable=False
    )

    route_id = db.Column(
        db.Integer,
        db.ForeignKey('routes.route_id', ondelete="CASCADE"),
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
    arrival_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(
        db.Enum('Scheduled', 'Waiting', 'En Route', 'Arrived', 'Completed', 'Cancelled', name='trip_status'),
        nullable=False,
        default='Scheduled'
    )

    # relationship
    jeepney_fk = db.relationship(
        "Jeepney",
        foreign_keys=[jeepney_id],
        back_populates='trip_pk'
    )

    route_fk = db.relationship(
        "Route",
        foreign_keys=[route_id],
        back_populates='trip_pk'
    )

    origin_fk = db.relationship(
        "Terminal",
        foreign_keys=[origin_terminal_id],
        back_populates='origin_trip_pk'
    )

    destination_fk = db.relationship(
        "Terminal",
        foreign_keys=[destination_terminal_id],
        back_populates='destination_trip_pk'
    )

    seats_pk = db.relationship(
        "Seat",
        back_populates="trip_fk",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    notification_trip_pk = db.relationship(
        "Notification",
        foreign_keys='Notification.trip_id',
        back_populates="notification_trip_fk",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# trip seats

class Seat(db.Model):

    __tablename__ = "seats"

    trip_seat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    trip_id = db.Column(
        db.Integer,
        db.ForeignKey('trips.trip_id', ondelete="CASCADE"),
        nullable=False
    )

    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    occupied_seats = db.Column(db.Integer, nullable=False)

    last_updated = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    trip_fk = db.relationship(
        "Trip",
        foreign_keys=[trip_id],
        back_populates="seats_pk"
    )


# terminal jeepneys

class TerminalJeepneys(db.Model):
    __tablename__ = "terminaljeeps"

    terminal_jeep_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id', ondelete="CASCADE"),
        nullable=False
    )
    jeepney_id = db.Column(
        db.Integer,
        db.ForeignKey('jeepneys.jeepney_id', ondelete="CASCADE"),
        nullable=False
    )

    arrival_time = db.Column(db.DateTime, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(
        db.Enum('Waiting', 'Boarding', 'Departed', 'Arrived', name='terminal_jeep_status'),
        nullable=False,
        default='Waiting'
    )
    current_passengers = db.Column(db.Integer, nullable=False, default=0)

    # to relationship

    terminal_jeep_fk = db.relationship(
        "Terminal",
        foreign_keys=[terminal_id],
        back_populates='terminal_jeep_pk'
    )

    jeep_jeep_fk = db.relationship(
        "Jeepney",
        foreign_keys=[jeepney_id],
        back_populates='jeep_jeep_pk'
    )


# user_favorites

class Userfavorite(db.Model):

    __tablename__ = "userfavorites"

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete="CASCADE"),
        nullable=False
    )

    terminal_id = db.Column(
        db.Integer,
        db.ForeignKey('terminals.terminal_id', ondelete="CASCADE"),
        nullable=False
    )

    route_id = db.Column(
        db.Integer,
        db.ForeignKey('routes.route_id', ondelete="CASCADE"),
        nullable=False
    )

    label = db.Column(db.String(100), nullable=False)

    date_created = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now()
    )

    # to relationship

    favorite_fk = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates='favorite_pk'
    )

    favorite_terminal_fk = db.relationship(
        "Terminal",
        foreign_keys=[terminal_id],
        back_populates='favorite_terminal_pk'
    )

    favorite_route_fk = db.relationship(
        "Route",
        foreign_keys=[route_id],
        back_populates='favorite_route_pk'
    )


# notifications

class Notification(db.Model):

    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete="CASCADE"),
        nullable=False
    )

    trip_id = db.Column(
        db.Integer,
        db.ForeignKey('trips.trip_id', ondelete="CASCADE"),
        nullable=False
    )

    type_nof = db.Column(
        db.Enum('Arrival', 'Departure', 'FullCapacity', 'System', name='type_of'),
        nullable=False
    )

    message = db.Column(db.String(200), nullable=False)
    is_read = db.Column(
        db.Boolean,
        nullable=False,
        server_default=text('FALSE')
    )
    date_sent = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now()
    )

    # to relationship

    notification_fk = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates='notification_pk'
    )

    notification_trip_fk = db.relationship(
        "Trip",
        foreign_keys=[trip_id],
        back_populates="notification_trip_pk"
    )


# audt_log

class Auditlog(db.Model):

    __tablename__ = "auditlogs"

    audit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.user_id', ondelete="CASCADE"),
        nullable=False
    )

    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(
        db.Enum('INSERT', 'UPDATE', 'DELETE', name='actions')
    )
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now()
    )
    description = db.Column(db.String(255), nullable=True)

    audit_user_fk = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates='audit_user_pk'
    )
