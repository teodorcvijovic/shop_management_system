import json
from functools import wraps

from flask import Flask, request, Response, jsonify
from redis import Redis

from configuration import Configuration
from models import *
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_
import re

app = Flask(__name__)
app.config.from_object(Configuration)

db.init_app(app)

with app.app_context() as context:
    with Redis(host=Configuration.REDIS_HOST) as redis:
        while True:
            print('Wait for redis request...')
            productsBytes = redis.blpop(Configuration.REDIS_PRODUCT_LIST)[1]
            productsJSON = productsBytes.decode('utf-8')
            productStrings = json.loads(productsJSON)

            for line in productStrings:
                categoryNames = line[0].split('|')
                productName = line[1]
                quantity = int(line[2])
                price = float(line[3])

                categories = []
                for catName in categoryNames:
                    category = Category.query.filter(Category.name == catName).all()
                    if len(category) == 0:
                        # category doesn't exist
                        category = Category(name=catName)
                        db.session.add(category)
                        db.session.commit()
                    else:
                        category = category[0]
                    categories.append(category)

                product = Product.query.filter(Product.name == productName).all()
                if len(product) == 0:
                    # product doesn't exists
                    product = Product(name=productName, price=price, quantity=quantity)
                    db.session.add(product)
                    db.session.commit()
                    for cat in categories:
                        hasCat = HasCategory(categoryId=cat.id, productId=product.id)
                        db.session.add(hasCat)
                        db.session.commit()
                else:
                    product = product[0]

                    isValid = True

                    for cat in categories:
                        hasCat = HasCategory.query.filter(and_(HasCategory.categoryId == cat.id,
                                                               HasCategory.productId == product.id)).all()
                        if len(hasCat) == 0:
                            # product is not valid
                            isValid = False
                            break

                    for cat in product.categories:
                        if cat not in categories:
                            # product is not valid
                            isValid = False
                            break

                    if isValid:
                        # product is valid
                        product.price = (product.quantity * product.price + quantity * price) / (product.quantity + quantity)
                        product.quantity += quantity
                        db.session.commit()

                        # TODO: check orders that are ON WAITING








