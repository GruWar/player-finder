from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# TABLES IN DB
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean)

    # relationships
    created_groups = relationship("Group", back_populates="author")


class Game(db.Model):

    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)


class Group(db.Model):

    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    tittle = db.Column(db.String(100))
    game_name = db.Column(db.String(100))
    status = db.Column(db.String(50))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    act_capacity = db.Column(db.Integer)
    max_capacity = db.Column(db.Integer)
    description = db.Column(db.String(500))

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # relationships
    author = relationship("User", back_populates="created_groups")
