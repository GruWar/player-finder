from flask_login import UserMixin
from server import db, datetime
from sqlalchemy.orm import relationship


# Models
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.now())
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(50))
    verification_code = db.Column(db.String(8), default="")
    # relationships
    created_groups = relationship("Group", back_populates="author")
    joined_groups = relationship('Group', secondary='user_group', back_populates='users')
    comments = relationship('Comment', back_populates='user')
    # create a string

    def __repl__(self):
        return "<username %r>" % self.username


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    icon = db.Column(db.String(), nullable=True)
    # relationships
    used_in_groups = relationship("Group", back_populates="game")


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=datetime.now())
    tittle = db.Column(db.String(100))
    status = db.Column(db.String(50))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    act_capacity = db.Column(db.Integer)
    max_capacity = db.Column(db.Integer)
    description = db.Column(db.String(500))

    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # relationships
    users = relationship('User', secondary='user_group', back_populates='joined_groups')
    author = relationship("User", back_populates="created_groups")
    game = relationship("Game", back_populates="used_in_groups")
    comments = relationship('Comment', back_populates='group')


# connect tables
user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True, nullable=True)
)


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.String(50), default=datetime.now().strftime("%d.%m.%Y %H:%M"))
    text = db.Column(db.String(500))
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # relationships
    user = relationship('User', back_populates='comments')
    group = relationship('Group', back_populates='comments')
