import json
from functools import wraps

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_, func
import re

app = Flask(__name__)
app.config.from_object(Configuration)

jwt = JWTManager(app)

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


@app.route("/productStatistics", methods=["GET"])
@roleCheck(role='admin')
def productStatistics():

    resultJSON = {
        'statistics': []
    }

    for product in Product.query.all():
        stat = {
            'name': product.name
        }

        sold = 0
        for order in IsOrdered.query.filter(IsOrdered.productId == product.id):
            sold += order.received
        stat['sold'] = sold

        requested = 0
        for order in IsOrdered.query.filter(IsOrdered.productId == product.id):
            requested += order.requested
        stat['waiting'] = requested - sold

        resultJSON['statistics'].append(stat)

    return Response(json.dumps(resultJSON), status=200)

@app.route("/categoryStatistics", methods=["GET"])
@roleCheck(role='admin')
def categoryStatistics():

    resultJSON = {
        'statistics': [
            cat.name for cat in Category.query.join(HasCategory)
                                              .join(Product)
                                              .join(IsOrdered)
                                              .group_by(Category.id)
                                              .order_by(func.sum(IsOrdered.received).desc())
                                              .order_by(Category.name)
                                              .all()
        ]
    }

    return Response(json.dumps(resultJSON), status=200)


if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5004)