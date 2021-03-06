"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid

imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER']  + '/'

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        id=id,
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/post/<int:id>/delete_image')
@login_required
def delete_image(id):
    post = Post.query.get(int(id))
    post.delete_image()
    return redirect(url_for('post', id=id))

@app.route('/post/<int:id>/delete')
@login_required
def delete_post(id):
    post = Post.query.get(int(id))
    post.delete_post()
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        app.logger.info(f'User {current_user} was already authenticated.')
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if form.submit_sign_up.data:
            if user is not None:
                flash('Username already in use')
                app.logger.info(f'Failed sign-up attempt with username "{str(form.username.data)}".')
                return redirect(url_for('login'))
            else:
                user = User(username=form.username.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                app.logger.info(f'Created user "{str(form.username.data)}".')
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            app.logger.info(f'Failed login attempt with username "{str(form.username.data)}".')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        app.logger.info(f'User "{str(form.username.data)}" logged in.')
        return redirect(next_page)
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)

@app.route(Config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("home"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'], scopes=Config.SCOPE, redirect_uri=url_for('authorized', _external=True, _scheme='https')
        )
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        username = session['user']['preferred_username']
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f'User {username} unknown.')
            return redirect(url_for('login'))
        login_user(user)
        _save_cache(cache)
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    if session.get("user"): # Used MS Login
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True, _scheme='https'))

    return redirect(url_for('login'))

def _load_cache():
    cache = msal.SerializableTokenCache()
    try:
        cache.deserialize(session['token_cache'])
    except KeyError:
        pass
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session['token_cache'] = cache.serialize()

def _build_msal_app(cache=None):
    confidential_client_application = msal.ConfidentialClientApplication(
        Config.CLIENT_ID, authority=Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET, token_cache=cache
        )
    return confidential_client_application

def _build_auth_url(scopes=None, state=None):
    return _build_msal_app().get_authorization_request_url(
        scopes=scopes, state=state, redirect_uri=url_for('authorized', _external=True, _scheme='https')
    )
