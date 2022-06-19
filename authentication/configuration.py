from datetime import timedelta

import os

class Configuration:
    # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{os.environ['DATABASE_URL']}/authentication"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost:3306/authentication"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
