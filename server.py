from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# variable init
app = Flask(__name__)
app.config['SECRET_KEY'] = 'h5ds2864t61fb46h4r61gb13n5'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PlayerFinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# TABLE IN DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100))
    status = db.Column(db.String(50))
    creator = db.Column(db.String(100))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    act_capacity = db.Column(db.Integer)
    max_capacity = db.Column(db.Integer)
    description = db.Column(db.String(500))


# create tables
# with app.app_context():
#    db.create_all()


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
            return redirect(url_for('home'))

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
        return redirect(url_for("home"))
    return render_template("register.html", current_user=current_user)


@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    posts = Group.query.all()
    return render_template("home.html", current_user=current_user, posts=posts)


@app.route("/create_group", methods=["GET", "POST"])
@login_required
def create_group():
    if request.method == "POST":
        new_group = Group(
            game_name=request.form.get("game_name"),
            creator=current_user.username,
            start_date=request.form.get("start_date"),
            start_time=request.form.get("start_time"),
            end_date=request.form.get("end_date"),
            end_time=request.form.get("end_time"),
            status="run",
            act_capacity=1,
            max_capacity=request.form.get("max_players"),
            description=request.form.get("description"),
        )

        db.session.add(new_group)
        db.session.commit()
        return redirect(url_for("home"))
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
        return render_template("home.html", current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# run app
if __name__ == "__main__":
    app.run(debug=True)
