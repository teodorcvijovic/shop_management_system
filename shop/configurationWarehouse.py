import os
from datetime import timedelta

class Configuration:
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    REDIS_HOST = os.environ['REDIS_HOST']  # deployment
    # REDIS_HOST = 'localhost' # development
    REDIS_PRODUCT_LIST = 'products'

