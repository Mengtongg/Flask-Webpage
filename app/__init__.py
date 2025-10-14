from flask import Flask, request, current_app, has_request_context
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel #look at user request, pick the best language 
from flask_babel import lazy_gettext as _l
#from elasticsearch import Elasticsearch

def get_locale():
    if has_request_context():
        return request.accept_languages.best_match(current_app.config['LANGUAGES'])
    
    #return 'zh_Hans'
    return current_app.config['LANGUAGES'][0]

db = SQLAlchemy()
migrate = Migrate()

login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')

mail = Mail()
moment = Moment() # takes date and time in JavaScript library

#babel = Babel(app, locale_selector=get_locale)
babel = Babel()

# define factory function that builds a new app
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    if not app.config.get("EMAIL_ENABLED", True):
        app.config["MAIL_SUPPRESS_SEND"] = True

    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    #app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        #if app.config['ELASTICSEARCH_URL'] else None
    
    app.elasticsearch = None
    host = app.config.get('ELASTICSEARCH_URL') or os.environ.get('ELASTIC_HOST')

    if host:
        try:
            from elasticsearch import Elasticsearch
            # simple unauth dev (localhost) or managed host without auth
            app.elasticsearch = Elasticsearch(hosts=[host], request_timeout=5)
            # sanity check; if it fails we just disable ES
            app.elasticsearch.info()
            app.logger.info("Elasticsearch enabled at %s", host)
        except Exception as e:
            app.logger.warning("Elasticsearch disabled: %s", e)
            app.elasticsearch = None

    # register blueprint with the application
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    if not app.debug and not app.testing:
        if app.config.get("EMAIL_ENABLED", True) and app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    return app

from app import models
