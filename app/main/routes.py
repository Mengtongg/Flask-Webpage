from flask import render_template, flash, redirect, url_for, request, g, current_app
from app import db

from flask_login import current_user, login_required
import sqlalchemy as sa

from datetime import datetime, timezone

from flask_babel import lazy_gettext as _l
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException #detect and store language
from app.models import User, Post
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from app.translate import translate
from app.main import bp

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        #  Flask invokes the view function that handles the requested URL
        g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST']) # GET shows the page, POST process the form
@bp.route('/index', methods=['GET', 'POST'])
@login_required # blocks access unless logged in
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''

        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_l('Your post is now live!'))
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    # shows limit posts at a time
    posts = db.paginate(current_user.following_posts(), page=page, 
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('index.html', title=_l('Home Page'), form=form, posts=posts.items, 
                           next_url=next_url, prev_url=prev_url)

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get(_l('page'), 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('index.html', title=_l('Explore'), posts=posts.items, 
                           next_url=next_url, prev_url=prev_url)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)

# dynamic path
@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get(_l('page'), 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for(_l('main.user'), username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for(_l('main.user'), username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, 
                           next_url=next_url, prev_url=prev_url, form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_l(f'User {username} not found.'))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_l('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_l(f'You are following {username}!'))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))
    

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_l(f'User {username} not found.'))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_l('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_l(f'You are not following {username}.'))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_l('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_l('Edit Profile'), form=form)

# doesn't return HTML page, but returns data in JSON format
@bp.route('/translate', methods=['POST']) # POST for actions that change data
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'],
                              data['source_language'],
                              data['dest_language'])}
