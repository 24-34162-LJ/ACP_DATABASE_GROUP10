from flask_wtf import FlaskForm # this for security and the secret key
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, DateTimeLocalField, BooleanField# for the function each of this have their own action
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional # like role to make sure that data is valid

"""
- Datarequired() = make sure it have data
- length(min, max) = add role like example it must compose of that number of letter

to create a form you need this

class nameof the form(FlaskForm) - always use the FlaskForm is very important
      variable_name / function name    =  wtforms  ( - are like example stringfield which depend 
                                                         on the data we want to get 
        "legend", - this is the like a caption
        Validators=[DataRequired()] - this are is for like to make sure it have data to past                        
      )
      submit = SubmitField("Register") = always part of the form
      
      
"""

""""--------------SIGN IN -------------"""
class RegisterForm(FlaskForm):
    first_name = StringField (
        "First Name",
        validators=[DataRequired(), Length(min=3, max=25)]
    ) # for first_name

    last_name = StringField (
        "Last Name",
        validators=[DataRequired(), Length(min=3, max=25)]
    ) # for last name

    role = SelectField (
        "Select Role",
        choices=[("player", "player"), ("operator", "operator")],
        default='player',
        validators=[DataRequired()]
    ) # to know the role of the user

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )# to get the email # this will be use to login

    password = PasswordField (
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )# to get the password

    confirm_password = PasswordField (
        "Confirm Password",
        validators=[DataRequired(), EqualTo('password')]
    )# to make sure the password is same

    submit = SubmitField("Register") # to submit the enter data

""""--------------TO LOGIN -------------"""
class LoginForm(FlaskForm):
    email = StringField (
        "Email",
        validators=[DataRequired(), Email()]
    ) # it use gmail to able to login

    password = PasswordField (
        "Password",
        validators=[DataRequired(), Length(min=6)]
    ) #
    submit = SubmitField("Login")

class AddTerminal(FlaskForm):
    terminal_name = StringField (
        "terminal name",
        validators=[DataRequired()]
    )
    location = StringField (
        "terminal location",
        validators=[DataRequired()]
    )
    status = SelectField(
        "Select status",
        choices=[("active","active"),("inactive","inactive")],
        default='active',
        validators=[DataRequired()]
    )
    submit = SubmitField("add terminal")
    

# -----------------UPDATE FIELD -----------------

# ---------- USER ----------

class UserForm(FlaskForm):
    first_name = StringField(
        "First Name", 
        validators=[DataRequired()]
    )
    last_name = StringField(
        "Last Name", 
        validators=[DataRequired()]
    )
    
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    
    password = PasswordField (
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )# to get the password

    confirm_password = PasswordField (
        "Confirm Password",
        validators=[DataRequired(), EqualTo('password')]
    )# to make sure the password is same


    role = SelectField(
        "Role",
        choices=[
            ("player", "player"),
            ("operator", "operator"),
            ("viewer", "viewer"),
            ("admin", "admin"),
        ],
        validators=[DataRequired()],
    )

    level = IntegerField(
        "Level", 
        validators=[DataRequired()]
    )
    xp_points = IntegerField(
        "XP Points", 
        validators=[DataRequired()]
    )
    submit = SubmitField("Save User")
    
# ---------- TERMINAL ----------

class TerminalForm(FlaskForm):
    terminal_name = StringField(
        "Terminal Name",
        validators=[DataRequired()]
    )
    location = StringField(
        "Location", 
        validators=[DataRequired()]
    )

    status = SelectField(
        "Status",
        choices=[("active", "active"), ("inactive", "inactive")],
        validators=[DataRequired()],
    )
    is_main = BooleanField("Is Main Terminal")
    submit = SubmitField("Save Terminal")
    
    submit = SubmitField("Save Terminal")


# ---------- ROUTE ----------
class RouteForm(FlaskForm):
    route_name = StringField(
        "Route Name", 
        validators=[DataRequired()]
    )
    # These will be SelectFields filled with terminal choices in the route
    start_terminal_id = SelectField(
        "Start Terminal",
        coerce=int, 
        validators=[DataRequired()]
    )
    end_terminal_id = SelectField(
        "End Terminal",
        coerce=int, 
        validators=[DataRequired()]
    )
    
    estimated_time_minutes = IntegerField(
        "Estimated Time (minutes)",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Route")

# ---------- JEEPNEY ----------
class JeepneyForm(FlaskForm):
    plate_number = StringField(
        "Plate Number", 
        validators=[DataRequired()]
    )
    capacity = IntegerField(
        "Capacity", 
        validators=[DataRequired()]
    )
    terminal_id = SelectField(
        "Assign to Terminal",
        coerce=int,
        validators=[DataRequired()]
    )
    status = SelectField(
        "Status",
        choices=[
            ("Available", "Available"),
            ("En Route", "En Route"),
            ("Maintenance", "Maintenance"),
            ("Inactive", "Inactive"),
        ],
        default="Available",
        validators=[DataRequired()],
        
    )
    submit = SubmitField("Save Jeepney")


# ---------- TRIP ----------

class TripForm(FlaskForm):
    jeepney_id = SelectField(
        "Jeepney", 
        coerce=int, 
        validators=[DataRequired()]
    )
    route_id = SelectField(
        "Route",
        coerce=int, 
        validators=[DataRequired()]
    )
    origin_terminal_id = SelectField(
        "Origin Terminal", 
        coerce=int, 
        validators=[DataRequired()]
    )
    destination_terminal_id = SelectField(
        "Destination Terminal", 
        coerce=int,
        validators=[DataRequired()]
    )

    departure_time = DateTimeLocalField(
        "Departure Time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    arrival_time = DateTimeLocalField(
        "Arrival Time",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[
            ("Scheduled", "Scheduled"),
            ("Waiting", "Waiting"),
            ("En Route", "En Route"),
            ("Arrived", "Arrived"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
        validators=[DataRequired()],
    )

    submit = SubmitField("Save Trip")


# ---------- SEAT ----------

class SeatForm(FlaskForm):
    trip_id = SelectField(
        "Trip", 
        coerce=int, 
        validators=[DataRequired()]
    )
    total_seats = IntegerField(
        "Total Seats", 
        validators=[DataRequired()]
    )
    available_seats = IntegerField(
        "Available Seats", 
        validators=[DataRequired()]
    )
    occupied_seats = IntegerField(
        "Occupied Seats", 
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Seat")
    

# ---------- TERMINAL JEEPS ----------

class TerminalJeepneysForm(FlaskForm):
    terminal_id = SelectField(
        "Terminal", 
        coerce=int, 
        validators=[DataRequired()]
    )
    jeepney_id = SelectField(
        "Jeepney", 
        coerce=int,
        validators=[DataRequired()]
    )

    arrival_time = DateTimeLocalField(
        "Arrival Time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    departure_time = DateTimeLocalField(
        "Departure Time",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
    )

    status = SelectField(
        "Status",
        choices=[
            ("Waiting", "Waiting"),
            ("Boarding", "Boarding"),
            ("Departed", "Departed"),
            ("Arrived", "Arrived"),
        ],
        validators=[DataRequired()],
    )

    current_passengers = IntegerField(
        "Current Passengers", 
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Terminal Jeep Entry")
    

# ---------- USER FAVORITE ----------

class UserfavoriteForm(FlaskForm):
    user_id = SelectField(
        "User", 
        coerce=int, 
        validators=[DataRequired()]
    )
    terminal_id = SelectField(
        "Terminal", 
        coerce=int, 
        validators=[DataRequired()]
    )
    route_id = SelectField(
        "Route", 
        coerce=int, 
        validators=[DataRequired()]
    )
    label = StringField(
        "Label", 
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Favorite")


# ---------- NOTIFICATION ----------
class NotificationForm(FlaskForm):
    user_id = SelectField(
        "User",
        coerce=int, 
        validators=[DataRequired()]
    )
    trip_id = SelectField(
        "Trip",
        coerce=int, 
        validators=[DataRequired()]
    )
    type_nof = SelectField(
        "Type",
        choices=[
            ("Arrival", "Arrival"),
            ("Departure", "Departure"),
            ("FullCapacity", "FullCapacity"),
            ("System", "System"),
        ],
        validators=[DataRequired()],
    )
    message = StringField(
        "Message", 
        validators=[DataRequired()]
    )
    is_read = BooleanField("Is Read")
    submit = SubmitField("Save Notification")

# ---------- AUDIT LOG ----------

class AuditlogForm(FlaskForm):
    user_id = SelectField(
        "User",
        coerce=int, 
        validators=[DataRequired()]
    )
    table_name = StringField(
        "Table Name", 
        validators=[DataRequired()]
    )
    record_id = IntegerField(
        "Record ID", 
        validators=[DataRequired()]
    )

    action = SelectField(
        "Action",
        choices=[
            ("INSERT", "INSERT"),
            ("UPDATE", "UPDATE"),
            ("DELETE", "DELETE"),
        ],
        validators=[DataRequired()],
    )

    description = StringField(
        "Description", 
        validators=[Optional()]
    )

    submit = SubmitField("Save Audit Log")


