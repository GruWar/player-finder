from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from db_tables import db, User, Game, Group
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


def status_check():
    with app.app_context():
        groups = Group.query.all()
        dt = datetime.now()
        dt = dt.strftime("%Y-%m-%d %H:%M")
        dt_hour = datetime.now() + timedelta(hours=1)
        dt_hour = dt_hour.strftime("%Y-%m-%d %H:%M")
        print(dt_hour)
        for group in groups:
            start_date = group.start_date + ' ' + group.start_time
            end_date = group.end_date + ' ' + group.end_time
            if start_date > dt:
                print("WAIT")
                group.status = "wait"
            elif start_date <= dt:
                if dt < end_date:
                    print("RUNNING")
                    group.status = "run"
            else:
                print("DELETE")
                Group.query.filter_by(id=group.id).delete()
        db.session.commit()


# app init
app = Flask(__name__)
app.config['SECRET_KEY'] = 'h5ds2864t61fb46h4r61gb13n5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PlayerFinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(status_check, 'interval', minutes=1)
scheduler.start()

# create tables
# with app.app_context():
#     db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# routing
@app.route("/")
def index():
    return render_template("index.html", current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

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
            login_user(user)
            return redirect(url_for('groups'))

    return render_template("login.html", current_user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        if User.query.filter_by(username=request.form.get('username')).first():
            flash("This username is used, please choice another")
            return redirect(url_for('register'))
        hash_and_salted_password = generate_password_hash(
            request.form.get("password"),
            method="pbkdf2",
            salt_length=8,
        )

        new_user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=hash_and_salted_password,
            is_admin=False,
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("groups"))
    return render_template("register.html", current_user=current_user)


@app.route("/groups", methods=["GET", "POST"])
@login_required
def groups():
    groups = Group.query.all()
    return render_template("groups.html", current_user=current_user, groups=groups)


@app.route("/my_groups", methods=["GET", "POST"])
@login_required
def my_groups():
    return render_template("my_groups.html", current_user=current_user)


@app.route("/create_group", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        new_group = Group(
            tittle=request.form.get("tittle"),
            game_name=request.form.get("game_name"),
            start_date=request.form.get("start_date"),
            start_time=request.form.get("start_time"),
            end_date=request.form.get("end_date"),
            end_time=request.form.get("end_time"),
            status="",
            act_capacity=1,
            max_capacity=request.form.get("max_players"),
            description=request.form.get("description"),
            author_id=current_user.id,
        )

        db.session.add(new_group)
        db.session.commit()
        status_check()
        return redirect(url_for("groups"))
    return render_template("create_group.html", current_user=current_user)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        user = User.query.filter_by(username=current_user.username).first()
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        username = request.form.get("username")
        email = request.form.get("email")
        if request.form['action'] == "save":
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
        elif request.form['action'] == "change password":
            # change password
            if check_password_hash(user.password, old_password):
                hash_and_salted_password = generate_password_hash(
                    new_password,
                    method="pbkdf2",
                    salt_length=8,
                )
                user.password = hash_and_salted_password
            db.session.commit()
    return render_template("profile.html", current_user=current_user)


@app.route("/admin_edit", methods=["GET", "POST"])
@login_required
def admin_edit():
    if current_user.is_admin == 1:
        if request.method == "POST":
            if request.form['action'] == "add_game":
                game_name = request.form.get("game_name")
                new_game = Game(
                    name=game_name,
                )
                db.session.add(new_game)
                db.session.commit()
                return redirect(url_for("admin_edit"))
            if request.form['action'] == "delete_game":
                game_id = request.form.get("game_id")
                Game.query.filter_by(id=game_id).delete()
                db.session.commit()
            if request.form['action'] == "delete_user":
                user_id = request.form.get("user_id")
                User.query.filter_by(id=user_id).delete()
                db.session.commit()
        return render_template("admin.html", current_user=current_user)
    else:
        return render_template("groups.html", current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# run app
if __name__ == "__main__":
    app.run(debug=True)
