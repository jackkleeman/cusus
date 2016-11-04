#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, redirect, session, Response
from flask_login import UserMixin, LoginManager, \
    login_user, logout_user
from functools import wraps
from flask_blogging import SQLAStorage, BloggingEngine
from sqlalchemy import create_engine, MetaData
import logging
from logging import Formatter, FileHandler
import os

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
engine = create_engine('sqlite:////tmp/blog.db')
meta = MetaData()
sql_storage = SQLAStorage(engine, metadata=meta)
blog_engine = BloggingEngine(app, sql_storage)
login_manager = LoginManager(app)
meta.create_all(bind=engine)
bengine = app.extensions["blogging"]

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'cusus'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# user class for providing authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    def get_name(self):
        return "Jack Kleeman"  # typically the user's name

@login_manager.user_loader
@blog_engine.user_loader
def load_user(user_id):
    return User(user_id)

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    lastpost = sql_storage.get_posts(count=1)
    session['title'] = lastpost[0]['title']
    session['post_id'] = lastpost[0]['post_id']
    return render_template('pages/index.html', session=session)

@app.route('/about/')
def about():
    return render_template('pages/about.html')

@app.route('/contact/')
def contact():
    return render_template('pages/contact.html')


@app.route("/login/")
@requires_auth
def login():
    user = User("admin")
    login_user(user)
    return redirect("/events")

@app.route("/logout/")
def logout():
    logout_user()
    return redirect("/")


# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('pages/404.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('pages/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''