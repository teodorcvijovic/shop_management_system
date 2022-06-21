import json
from functools import wraps

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
import re

app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)

if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5002)