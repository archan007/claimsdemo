import snowflake.connector

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

conn = snowflake.connector.connect(
    user='KEYRUS_USER',
    password='Keyrus_demo2022',
    account='wu00578.west-europe.azure',
    warehouse='KEYRUS_WH',
    database='CLAIMS',
    schema='PUBLIC',
    role='KEYRUS_ROLE'
)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'snowflake://KEYRUS_USER:Keyrus_demo2022@wu00578.west-europe.azure/CLAIMS/PUBLIC?warehouse=KEYRUS_WH&role=KEYRUS_ROLE'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
