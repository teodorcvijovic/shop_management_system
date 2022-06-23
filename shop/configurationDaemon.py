from datetime import timedelta

import os

class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{os.environ['DATABASE_URL']}/shop"  # deployment
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost:3307/shop"  # development

    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    REDIS_HOST = os.environ['REDIS_HOST']  # deployment
    # REDIS_HOST = 'localhost' # development
    REDIS_PRODUCT_LIST = 'products'