from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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


# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))


# with app.app_context():
#     db.create_all()


# routing
@app.route("/")
def index():
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get("password"),
            method="pbkdf2",
            salt_length=8,
        )

        new_user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=hash_and_salted_password,
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route("/home")
@login_required
def home():
    return render_template("home.html", logged_in=current_user.is_authenticated)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        # edit profile
        user = User.query.filter_by(username=current_user.username).first()
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        username = request.form.get("username")
        email = request.form.get("email")
        if not db.session.query(db.exists().where(User.username == username)).scalar():
            user.username = username
        if not db.session.query(db.exists().where(User.email == email)).scalar():
            user.email = email
        # change password
        if check_password_hash(user.password, old_password):
            hash_and_salted_password = generate_password_hash(
            new_password,
            method="pbkdf2",
            salt_length=8,
            )
            user.password = hash_and_salted_password
        db.session.commit()
    user = current_user
    return render_template("profile.html", logged_in=current_user.is_authenticated, user=user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# run app
if __name__ == "__main__":
    app.run(debug=True)
