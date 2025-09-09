# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[("student", "Student"), ("teacher", "Teacher"), ("admin", "Admin")])
    submit = SubmitField("Register")

class QuizForm(FlaskForm):
    question = TextAreaField("Question", validators=[DataRequired()])
    options = TextAreaField("Options (JSON string)", validators=[DataRequired()])
    correct_answer = StringField("Correct Answer", validators=[DataRequired()])
    points = IntegerField("Points", default=10, validators=[NumberRange(min=1, max=100)])
    submit = SubmitField("Save Quiz")

class ChallengeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired()])
    points = IntegerField("Points", default=20, validators=[NumberRange(min=1, max=200)])
    submit = SubmitField("Save Challenge")

class ForumForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Post")
