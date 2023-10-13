from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from forms import (LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm, GroupForm, AdminForm,
                   GroupFiltersForm, ForgotPasswordForm)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import LoginManager, logout_user, login_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
import uuid as uuid
import os
import secrets
from emailSMTP import send_verify_email

# Create a Flask Instance
app = Flask(__name__)
# Secret key
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=5)
# Add database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
# Database init
engine = create_engine(os.environ.get("SQLALCHEMY_DATABASE_URI"))
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# Flask Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
# Import models
from models import User, Game, Group, Comment
# Create db and models
with app.app_context():
    db.create_all()


# Functions
def status_check():
    with app.app_context():
        all_groups = Group.query.all()
        dt_now = datetime.now()
        dt_now = dt_now.strftime("%d-%m-%Y %H:%M")
        for group in all_groups:
            start_date = group.start_date + ' ' + group.start_time
            end_date = group.end_date + ' ' + group.end_time
            if start_date > dt_now:
                print("WAIT")
                group.status = "wait"
            elif start_date <= dt_now:
                if dt_now < end_date:
                    print("RUNNING")
                    group.status = "run"
                else:
                    print("END")
                    group.status = "end"
        db.session.commit()


# scheduler init
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(status_check, 'interval', minutes=15)
scheduler.start()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Routes
@app.route("/")
def index():
    count_players = db.session.query(User).count()
    count_games = db.session.query(Game).count()
    count_groups = db.session.query(Group).filter(Group.status != "end").count()
    return render_template("index.html", current_user=current_user, cpl=count_players, cga=count_games, cgr=count_groups)


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("This email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            if form.remember_me.data:
                login_user(user, remember=True)
            else:
                login_user(user, remember=False)
            return redirect(url_for('groups'))
    return render_template("auth/login.html", form=form, current_user=current_user)


# Registration
@app.route("/registration", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        if User.query.filter_by(username=form.username.data).first():
            # Username is used
            flash("This username is used, please choice another")
            return redirect(url_for('registration'))
        # icon
        user_icon = request.files["user_icon"]
        if not user_icon:
            user_icon_name = "default_user.jpeg"
        else:
            # Game icon name
            user_icon_name = secure_filename(user_icon.filename)
            # set UUID
            user_icon_name = str(uuid.uuid1()) + "_" + user_icon_name
            # Save icon
            user_icon.save(os.path.join("static/img/user_icons", user_icon_name))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length=8,
        )
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hash_and_salted_password,
            icon=user_icon_name,
        )
        db.session.add(new_user)
        db.session.commit()
        form.username.data = ""
        form.email.data = ""
        login_user(new_user)
        flash("Registration successfully!")
        return redirect(url_for("groups"))
    return render_template("auth/registration.html", form=form, current_user=current_user)


# forgot password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if request.method == "POST":
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a verification code and store it in the user's record
            code = secrets.token_hex(4).upper()
            user.verification_code = code
            db.session.commit()

            # Send the verification code to the user's email address
            send_verify_email(email, code)

            # Redirect to the code verification page, passing the email as a parameter
            return redirect(url_for("verify_code", id=user.id))
        else:
            flash("User with this email doesn't exist!")

    return render_template("auth/forgot_password.html", form=form, current_user=current_user)


@app.route("/verify_code/<int:id>", methods=["GET", "POST"])
def verify_code(id):
    form = ForgotPasswordForm()
    user = User.query.filter_by(id=id).first()
    if not user:
        flash("User with this email doesn't exist!")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        code = form.code.data
        if code == user.verification_code:
            # Redirect to the new password page, passing the email as a parameter
            return redirect(url_for("new_password", id=id))
        else:
            flash("Wrong verify code!")

    return render_template("auth/verify_code.html", form=form, current_user=current_user)


@app.route("/new_password/<int:id>", methods=["GET", "POST"])
def new_password(id):
    form = ForgotPasswordForm()
    if request.method == "POST":
        user = User.query.filter_by(id=id).first()
        new_password = form.new_password.data
        repeat_new_password = form.repeat_new_password.data
        # change password
        if new_password == repeat_new_password:
            hash_and_salted_password = generate_password_hash(
                new_password,
                method="pbkdf2",
                salt_length=8,
            )
            user.password = hash_and_salted_password
            user.verification_code = ""
            db.session.commit()
            return redirect(url_for("login"))
        else:
            flash("Password doesn't match")
    return render_template("auth/new_password.html", form=form, current_user=current_user)


# Profile update
@app.route("/profile", methods=["GET", "POST"])
@login_required
def update():
    form_edit = EditProfileForm()
    form_passwd = ChangePasswordForm()
    if form_edit.validate_on_submit():
        username = form_edit.username.data
        email = form_edit.email.data
        user = User.query.filter_by(username=current_user.username).first()
        # edit profile
        if db.session.query(db.exists().where(User.username == username)).scalar() and user.username != username:
            flash("This username is used, please choice another")
            return redirect(url_for('edit_profile'))
        else:
            user.username = username

        if db.session.query(db.exists().where(User.email == email)).scalar() and user.email != email:
            flash("This email is used, please choice another")
            return redirect(url_for('edit_profile'))
        else:
            user.email = email
        db.session.commit()
    if form_passwd.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        old_password = form_passwd.old_password.data
        new_password = form_passwd.new_password.data
        # change password
        if check_password_hash(user.password, old_password):
            hash_and_salted_password = generate_password_hash(
                new_password,
                method="pbkdf2",
                salt_length=8,
            )
            user.password = hash_and_salted_password
            db.session.commit()
    return render_template("auth/profile.html", form_edit=form_edit, form_passwd=form_passwd, current_user=current_user)


@app.route("/admin_edit", methods=["GET", "POST"])
@login_required
def admin_edit():
    form = AdminForm()
    if request.method == "POST":
        game_name = request.form["game_name"]
        game_icon = request.files["game_icon"]
        if not game_icon:
            game_icon_name = "default.jpeg"
        else:
            # Game icon name
            game_icon_name = secure_filename(game_icon.filename)
            # set UUID
            game_icon_name = str(uuid.uuid1()) + "_" + game_icon_name
            # Save icon
            game_icon.save(os.path.join("static/img/game_icons", game_icon_name))

        new_game = Game(
            name=game_name,
            icon=game_icon_name,
        )
        db.session.add(new_game)
        db.session.commit()
    return render_template("auth/admin.html", current_user=current_user, form=form)


@app.route("/groups", methods=["GET", "POST"])
@login_required
def groups():
    form = GroupFiltersForm()
    games = Game.query.all()
    game_list = [game.name for game in games]
    sorted_game_list = sorted(game_list)
    form.game_name.choices = [("-", "-")] + [(name, name) for name in sorted_game_list]
    all_groups = Group.query.all()
    if form.validate_on_submit():
            game_name = form.game_name.data
            status = form.status.data

            # filters
            # by game
            if game_name != "-":
                all_groups = [group for group in all_groups if group.game.name == game_name]
            # by status
            if status != "-":
                all_groups = [group for group in all_groups if group.status == status]
    return render_template("groups/groups.html", current_user=current_user, groups=all_groups, form=form)


@app.route("/my_groups", methods=["GET", "POST"])
@login_required
def my_groups():
    first_group_created = Group.query.filter_by(author=current_user).filter(
        (Group.status == "wait") | (Group.status == "run")
    ).first()
    if first_group_created:
        group_id = first_group_created.id
        return redirect(url_for("group", group_id=group_id))
    else:
        first_group_joined = Group.query.join(Group.users).filter(
        User.id == current_user.id,
        (Group.status == "wait") | (Group.status == "run")
        ).first()
        if first_group_joined:
            group_id = first_group_joined.id
            return redirect(url_for("group", group_id=group_id))
        else:
            return render_template("groups/my_groups.html", current_user=current_user)


@app.route('/join_group/<int:group_id>', methods=["GET", "POST"])
@login_required
def join_group(group_id):
    group = Group.query.get(group_id)
    group.users.append(current_user)
    group.act_capacity = group.act_capacity + 1
    db.session.commit()
    return redirect(url_for("group", group_id=group_id))


@app.route('/search')
@login_required
def search():
    q = request.args.get("q")

    if q:
        results = Group.query.filter(Group.tittle.icontains(q)).order_by(Group.id).limit(100).all()
    else:
        results = Group.query.all()
    return render_template("search_results.html", groups=results)


@app.route("/group/<int:group_id>")
@login_required
def group(group_id):
    requested_group = Group.query.get(group_id)
    return render_template("groups/group.html", current_user=current_user, group=requested_group)


@app.route("/group_create", methods=["GET", "POST"])
@login_required
def group_create():
    form = GroupForm()
    game_id = None
    games = Game.query.all()
    game_list = [game.name for game in games]
    sorted_game_list = sorted(game_list)
    form.game_name.choices = [(name, name) for name in sorted_game_list]

    if form.validate_on_submit():
        for game in games:
            if form.game_name.data == game.name:
                game_id = game.id


        new_group = Group(
            tittle=form.title.data,
            game_id=game_id,
            start_date=form.start_date.data.strftime('%d-%m-%Y'),
            start_time=f"{form.start_time_hours.data}:{form.start_time_minutes.data}",
            end_date=form.end_date.data.strftime('%d-%m-%Y'),
            end_time=f"{form.end_time_hours.data}:{form.end_time_minutes.data}",
            status="",
            act_capacity=1,
            max_capacity=form.max_players.data,
            description=form.description.data,
            author_id=current_user.id,
        )
        if datetime.strptime(new_group.start_date, '%d-%m-%Y') > datetime.strptime(new_group.end_date, '%d-%m-%Y'):
            flash("The end date cannot be earlier than the start date.")
        else:
            # status check
            status = ""
            dt_now = datetime.now()
            dt_now = dt_now.strftime("%d-%m-%Y %H:%M")
            start_date = form.start_date.data.strftime(
                '%d-%m-%Y') + ' ' + f"{form.start_time_hours.data}:{form.start_time_minutes.data}"
            end_date = form.end_date.data.strftime(
                '%d-%m-%Y') + ' ' + f"{form.end_time_hours.data}:{form.end_time_minutes.data}"
            if start_date > dt_now:
                status = "wait"
            elif start_date <= dt_now:
                if dt_now < end_date:
                    status = "run"
                else:
                    status = "end"
            new_group.status = status
            db.session.add(new_group)
            db.session.commit()
            return redirect(url_for("groups"))
    return render_template("groups/create.html", current_user=current_user, form=form)


@app.route('/create_comment/<int:group_id>', methods=["GET", "POST"])
@login_required
def create_comment(group_id):
    if request.method == "POST":
        text = request.form["text"]
        new_comment = Comment(
            text=text,
            author_id=current_user.id,
            group_id=group_id,
        )
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('group', group_id=group_id))


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Create error pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500
