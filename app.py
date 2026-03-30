import os
import logging
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Load environment variables (supports .env and instance/.env)
load_dotenv()
try:
    instance_env = os.path.join(os.path.dirname(__file__), 'instance', '.env')
    if os.path.exists(instance_env):
        load_dotenv(instance_env, override=True)
except Exception:
    pass

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///contacts.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Import routes after app initialization
import routes  # noqa: F401

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    # Create all tables
    db.create_all()

    # Ensure admin user exists with correct password on every boot
    try:
        admin_password = os.environ.get("ADMIN_PASSWORD", "Iloveyou123!")
        admin_user = models.User.query.filter_by(username='admin', role='admin').first()
        if admin_user:
            admin_user.set_password(admin_password)
            db.session.commit()
            logging.info("Admin password updated successfully")
        else:
            admin_user = models.User(username='admin', email='admin@connectyou.pro', role='admin')
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Admin user created successfully")
    except Exception as e:
        logging.error(f"Failed to set admin password: {e}")
        db.session.rollback()

@app.route('/health')
def health_check():
    return {'status': 'ok', 'version': '2026.03.27'}

from flask_migrate import Migrate
from facebook_messenger import messenger_bp

app.register_blueprint(messenger_bp)

migrate = Migrate(app, db)
