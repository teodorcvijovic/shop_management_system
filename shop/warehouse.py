import csv
import io
import json
from functools import wraps

from flask import Flask, request, Response, jsonify
from configurationWarehouse import Configuration
from models import *
from flask_jwt_extended import JWTManager, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
import re

from redis import Redis

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

@app.route("/update", methods=["POST"])
@roleCheck(role='salesmen')
def update():
    file = request.files.get('file', None)

    # file isn't passed
    if not file:
        return Response(json.dumps({'message': "Field file missing."}), status=400)

    content = file.stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    products = []
    rowCnt = 0

    for row in reader:
        if len(row) == 0:
            return Response(json.dumps({'message': "Incorrect number of values on line" + str(rowCnt) + "."}), status=400)

        categoryNames = row[0]
        productName = row[1]
        quantity = row[2]
        price = row[3]

        if len(categoryNames) == 0 or len(productName) == 0 or len(quantity) == 0 or len(price) == 0:
            return Response(json.dumps({'message': "Incorrect number of values on line" + str(rowCnt) + "."}), status=400)

        if int(quantity) <= 0:
            return Response(json.dumps({'message': "Incorrect quantity on line" + str(rowCnt) + "."}), status=400)

        if float(price) <= 0:
            return Response(json.dumps({'message': "Incorrect price on line" + str(rowCnt) + "."}), status=400)

        products.append(row)

        rowCnt += 1

    # passed all checks

    with Redis(host=Configuration.REDIS_HOST) as redis:
        redis.rpush(Configuration.REDIS_PRODUCT_LIST, json.dumps(products))

    return Response(status=200)


if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5002)