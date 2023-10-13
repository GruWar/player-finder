from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField, DateField, TimeField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, NumberRange
from flask_wtf.file import FileField
from datetime import date, datetime, timedelta


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    user_icon = FileField('User icon')
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class EditProfileForm(FlaskForm):
    username = StringField()
    email = StringField()
    submit = SubmitField('Save')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password')
    new_password = PasswordField('New Password')
    submit = SubmitField('Change Password')


class GroupForm(FlaskForm):
    hours_choices = [(str(i).zfill(2), str(i).zfill(2)) for i in range(24)]
    minutes_choices = [(str(i).zfill(2), str(i).zfill(2)) for i in range(0, 60, 15)]
    current_time = datetime.now()

    rounded_minutes = min(minutes_choices, key=lambda x: abs(int(x[0]) - datetime.now().minute))
    default_end_time = (current_time + timedelta(hours=2)).strftime('%H')

    title = StringField('Title', validators=[DataRequired()])
    game_name = SelectField('Game Name', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today(), render_kw={'min': date.today().strftime('%Y-%m-%d')})
    start_time_hours = SelectField('Start Hours', validators=[DataRequired()], choices=hours_choices, default=datetime.now().strftime('%H'))
    start_time_minutes = SelectField('Start Minutes', validators=[DataRequired()], choices=minutes_choices, default=rounded_minutes[0])
    end_date = DateField('End Date', validators=[DataRequired()], default=date.today(), render_kw={'min': date.today().strftime('%Y-%m-%d')})
    end_time_hours = SelectField('End Hours', validators=[DataRequired()], choices=hours_choices, default=default_end_time)
    end_time_minutes = SelectField('End Minutes', validators=[DataRequired()], choices=minutes_choices, default=rounded_minutes[0])
    max_players = IntegerField('Number of Players', validators=[DataRequired(), NumberRange(min=1)], default=1)
    description = TextAreaField('Description', render_kw={'rows': 3})
    submit = SubmitField('Create')


class AdminForm(FlaskForm):
    game_name = StringField('Game name', validators=[DataRequired()])
    game_icon = FileField('Game icon')
    create_game_submit = SubmitField('Add game')


class GroupFiltersForm(FlaskForm):
    game_name = SelectField('Game Name')
    status = SelectField('Status', choices=('-', 'wait', 'run'))
    submit = SubmitField('Filter')


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    code = StringField(validators=[DataRequired()])
    new_password = PasswordField('New Password')
    repeat_new_password = PasswordField('Repeat Password')
    submit = SubmitField('Change Password')
    send = SubmitField("Send code")
    verify_code = SubmitField("Verify")
    change = SubmitField('Change')

