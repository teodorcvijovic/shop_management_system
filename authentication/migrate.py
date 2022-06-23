import shutil

from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import db, Role, HasRole, User
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

    adminRole = Role(name='admin')
    salesmenRole = Role(name='salesmen')
    customerRole = Role(name='customer')

    db.session.add(adminRole)
    db.session.add(salesmenRole)
    db.session.add(customerRole)
    db.session.commit()

    # admin is created in initial migration
    admin = User(
        email='admin@admin.com',
        password='1',
        forename='admin',
        surname='admin'
    )

    db.session.add(admin)
    db.session.commit()

    userRole = HasRole(
        userId=admin.id,
        roleId=adminRole.id
    )

    db.session.add(userRole)
    db.session.commit()

