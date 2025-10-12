from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa  # “sa” = SQLAlchemy Core helpers (select, func, etc.)
import sqlalchemy.orm as so  # “so” = ORM helpers (Mapped, mapped_column, relationship)
from flask import current_app
from app import db, login
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from flask_babel import _, lazy_gettext as _l
from app.search import add_to_index, remove_from_index, query_index


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary = followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin = (followers.c.follower_id == id),
        back_populates = 'following')
    
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    # if a given user is already include
    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        # gives each row its own name
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True) # Shows posts in either condition
            .where(sa.or_(
                Follower.id == self.id, # I follow the Author 
                Author.id == self.id, # I am the Author
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc()) #sorting
        )
    
    def get_reset_password_token(self, expires_in=600): # token valid for 10 mins
        return jwt.encode(
            {_l('reset_password'): self.id, 'exp': time() + expires_in}, # expiration claim
            current_app.config['SECRET_KEY'], algorithm='HS256') # sign token with Flask

    # don't know which user it belongs to
    @staticmethod
    def verify_reset_password_token(token):
        try:
            # pull the user id out
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return # any thing goes wrong, returns to None
        return db.session.get(User, id)

    def __repr__(self):
        return '<User {}>'.format(self.username)  

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        # fast exist
        if total == 0:
            return [], 0
        when = []
        # rank the DB result in same order as ES
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    # event handler, snapshots the changes
    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    # save changes to mirror the same operations to ES
    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    # rebuild the ES index from changed database
    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)

# before/after every commit, the mixin syncs ES automatically.
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

class Post(SearchableMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5), index=True)
    __searchable__ = ['body'] # lists the field that need to be include in index

    def __repr__(self):
        return '<Post {}>'.format(self.body)   

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

