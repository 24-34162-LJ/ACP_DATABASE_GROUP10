from flask_wtf import FlaskForm # this for security and the secret key
from wtforms import StringField, PasswordField, SubmitField, SelectField# for the function each of this have their own action
from wtforms.validators import DataRequired, Email, Length, EqualTo # like role to make sure that data is valid


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
        choices=[("Commuter", "Commuter"), ("Vehicle Operator", "Vehicle Operator"), ("Admin", "Admin")],
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
    )
    submit = SubmitField("Login")



