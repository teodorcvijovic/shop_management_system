from functools import wraps

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
import re

app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)


@app.route("/register", methods=["POST"])
def register():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    isCustomer = request.json.get("isCustomer", "")

    if len(email) == 0:
        return Response("Field email is missing.", status=400)
    if len(password) == 0:
        return Response("Field password is missing.", status=400)
    if len(forename) == 0:
        return Response("Field forename is missing.", status=400)
    if len(surname) == 0:
        return Response("Field surname is missing.", status=400)
    if isCustomer == "":
        return Response("Field isCustomer is missing.", status=400)

    # email check
    emailIsValid = parseaddr(email)
    if len(emailIsValid[1]) == 0:
        return Response("Invalid email.", status=400)

    # password check
    if len(password) < 8 or not re.search(r'\d', password) \
            or not re.search(r'[A-Z]', password) \
            or not re.search(r'[a-z]', password):
        return Response("Invalid password.", status=400)

    # check if user is already registered
    user = User.query.filter(User.email == email).first()
    if user:
        return Response("Email already exists.", status=400)

    user = User(email=email, password=password, forename=forename, surname=surname)
    db.session.add(user)
    db.session.commit()

    if isCustomer:
        userRole = HasRole(userId=user.id, roleId=CUSTOMER_ROLE_ID)
    else:
        userRole = HasRole(userId=user.id, roleId=SALESMAN_ROLE_ID)
    db.session.add(userRole)
    db.session.commit()

    return Response("User is successfully registered.", status=200)


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if len(email) == 0:
        return Response("Field email is missing.", status=400)
    if len(password) == 0:
        return Response("Field password is missing.", status=400)

    # email check
    emailIsValid = parseaddr(email)
    if len(emailIsValid[1]) == 0:
        return Response("Invalid email.", status=400)

    # is password valid
    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if not user:
        return Response("Invalid credentials.", status=400)

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]  # TODO: how to specify roles in jwt tokens?
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)  # 200 is default status code


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    return Response(create_access_token(identity=identity, additional_claims=additionalClaims), status=200)


# role check decorator
def roleCheck(role):
    def innerRoleCheck(myFunction):
        @wraps(myFunction)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if ("roles" in claims) and (role in claims["roles"]):
                return myFunction(*arguments, **keywordArguments)
            else:
                return jsonify({'msg': 'Missing Authorization Header'}), 401

        return decorator

    return innerRoleCheck

@app.route("/delete", methods=["POST"])
@roleCheck(role='admin')
def delete():
    email = request.json.get("email", "")

    if len(email) == 0:
        return Response("Field email is missing.", status=400)

    # email check
    emailIsValid = parseaddr(email)
    if len(emailIsValid[1]) == 0:
        return Response("Invalid email.", status=400)

    # check if user exists
    user = User.query.filter(User.email == email).first()
    if not user:
        return Response("Unknown user.", status=400)

    # delete the user
    db.session.delete(user)
    db.session.commit()

    return Response("User is successfully deleted.", status=200)


if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5002)
