import bdb
import shutil

from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import *
from sqlalchemy_utils import database_exists, create_database

app = Flask(__name__)
app.config.from_object(Configuration)

migrateObject = Migrate(app, db)

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    create_database(app.config['SQLALCHEMY_DATABASE_URI'])

db.init_app(app)

with app.app_context() as context:
    try:
        shutil.rmtree('migrations')
    except Exception:
        pass

    init()
    migrate(message='Production migration')
    upgrade()

    # for testing
    # cat1 = Category(id=1, name='mobile')
    # db.session.add(cat1)
    # db.session.commit()
    # cat2 = Category(id=2, name='apple')
    # db.session.add(cat2)
    # db.session.commit()
    #
    # prod = Product(id=1, name='iphone', quantity=2, price=500.0)
    # db.session.add(prod)
    # db.session.commit()
    #
    # db.session.add(HasCategory(id=1, productId=prod.id, categoryId=cat1.id))
    # db.session.commit()
    # db.session.add(HasCategory(id=2, productId=prod.id, categoryId=cat2.id))
    # db.session.commit()
    #

