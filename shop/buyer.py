import json
from functools import wraps

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_

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


@app.route("/search", methods=["GET"])
@roleCheck(role='customer')
def search():
    productName = request.args.get('name', '')
    categoryName = request.args.get('category', '')

    result = {
        'categories': [],
        'products': []
    }

    if len(categoryName) == 0 and len(productName) == 0:
        result['categories'] = Category.query
        result['products'] = Product.query
    elif len(categoryName) == 0:
        result['products'] = Product.query.filter(Product.name.like(f"%{productName}%"))
        result['categories'] = Category.query.join(HasCategory).join(Product).filter(
            Product.name.like(f"%{productName}%"))
    elif len(productName) == 0:
        result['categories'] = Category.query.filter(Category.name.like(f"%{categoryName}%"))
        result['products'] = Product.query.join(HasCategory).join(Category).filter(
            Category.name.like(f"%{categoryName}%"))
    else:
        result['products'] = Product.query.filter(Product.name.like(f"%{productName}%"))
        result['categories'] = Category.query.filter(Category.name.like(f"%{categoryName}%")).join(HasCategory).join(Product) \
            .filter(Product.name.like(f"%{productName}%"))

    result['products'] = result['products'].all()
    result['categories'] = result['categories'].all()

    resultJSON = {
        'categories': [cat.name for cat in result['categories']],
        'products': [
            {
                'categories': [cat.name for cat in prod.categories],
                'id': prod.id,
                'name': prod.name,
                'price': prod.price,
                'quantity': prod.quantity
            }
            for prod in result['products']
        ]
    }

    return Response(json.dumps(resultJSON), status=200)


@app.route("/order", methods=["POST"])
@roleCheck(role='customer')
def order():
    requests = request.json.get("requests", "")

    if len(requests) == 0:
        return Response(json.dumps({'message': "Field requests is missing."}), status=400)

    # requests is a list of jsons: {
    #     'id': ...,
    #     'quantity': ...
    # }

    products = []
    requestedQuantities = []
    totalPrice = 0
    pending = False

    for i in range(len(requests)):
        productId = requests[i].get('id', '')
        quantity = requests[i].get('quantity', '')

        if productId == '':
            return Response(json.dumps({'message': "Product id is missing for request number " + str(i) + "."}), status=400)
        if quantity == '':
            return Response(json.dumps({'message': "Product quantity is missing for request number " + str(i) + "."}), status=400)

        try:
            productId = int(productId)
        except ValueError:
            return Response(json.dumps({'message': "Invalid product id for request number " + str(i) + "."}),status=400)
        try:
            quantity = int(quantity)
        except ValueError:
            return Response(json.dumps({'message': "Invalid product quantity for request number " + str(i) + "."}),status=400)

        if productId <= 0:
            return Response(json.dumps({'message': "Invalid product id for request number " + str(i) + "."}),status=400)
        if quantity <= 0:
            return Response(json.dumps({'message': "Invalid product quantity for request number " + str(i) + "."}),status=400)

        product = Product.query.filter(Product.id == productId).all()

        if len(product) == 0:
            return Response(json.dumps({'message': "Invalid product for request number " + str(i) + "."}), status=400)

        product = product[0]

        # request is valid
        products.append(product)
        requestedQuantities.append(quantity)
        totalPrice += product.price * quantity
        if product.quantity < quantity:
            pending = True

    # every request is valid, so now we can form the order
    verify_jwt_in_request()  # TODO: do we need this if we had a jwt decorator
    userClaims = get_jwt()
    email = userClaims['email']
    # email = 'admin@admin.com' # for testing

    myOrder = Order(price=totalPrice, customer_email=email, pending=pending)
    db.session.add(myOrder)
    db.session.commit()

    for product, requestedQuantity in zip(products, requestedQuantities):
        if product.quantity >= requestedQuantity:
            product.quantity -= requestedQuantity
            received = requestedQuantity
        else:
            received = product.quantity
            product.quantity = 0
        db.session.commit()

        isOrdered = IsOrdered(productId=product.id, orderId=myOrder.id, requested=requestedQuantity, received=received, productPrice=product.price)
        db.session.add(isOrdered)
        db.session.commit()

    return Response(json.dumps({'id': myOrder.id}), status=200)

@app.route("/status", methods=["GET"])
@roleCheck(role='customer')
def status():
    verify_jwt_in_request()  # TODO: do we need this if we had a jwt decorator
    userClaims = get_jwt()
    email = userClaims['email']
    # email = 'admin@admin.com'  # for testing

    orders = Order.query.filter(Order.customer_email == email)

    resultJSON = {
        'orders': [
            {
                'products': [
                    {
                        'categories': [cat.name for cat in product.categories],
                        'name': product.name,
                        'price': IsOrdered.query.filter(and_(IsOrdered.productId == product.id, IsOrdered.orderId == order.id)).first().productPrice,
                        'received': IsOrdered.query.filter(and_(IsOrdered.productId == product.id, IsOrdered.orderId == order.id)).first().received,
                        'requested': IsOrdered.query.filter(and_(IsOrdered.productId == product.id, IsOrdered.orderId == order.id)).first().requested,
                    }
                    for product in Product.query.join(IsOrdered).filter(IsOrdered.orderId == order.id).all()
                ],
                'price': order.price,
                'status': 'COMPLETE' if not order.pending else 'PENDING',
                'timestamp': order.date.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            for order in orders
        ]
    }

    return Response(json.dumps(resultJSON), status=200)

if __name__ == "__main__":
    db.init_app(app)
    app.run(debug=True, host="0.0.0.0", port=5003)
