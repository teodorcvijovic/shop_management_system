import json

from flask import Flask
from redis import Redis

from configuration import Configuration
from models import *
from sqlalchemy import and_

if __name__ == '__main__':
    app = Flask(__name__)
    app.config.from_object(Configuration)

    db.init_app(app)

    with Redis(host=Configuration.REDIS_HOST) as redis:
        while True:
            print('Wait for redis request...')
            productsBytes = redis.blpop(Configuration.REDIS_PRODUCT_LIST)[1]

            with app.app_context() as context:
                productsJSON = productsBytes.decode('utf-8')
                productStrings = json.loads(productsJSON)

                for line in productStrings:
                    categoryNames = line[0].replace('\ufeff', '')
                    categoryNames = categoryNames.split('|')
                    productName = line[1]
                    quantity = int(line[2])
                    price = float(line[3])

                    categories = []
                    for catName in categoryNames:
                        category = Category.query.filter(Category.name.contains(str(catName).strip())).all()
                        if len(category) == 0:
                            # category doesn't exist
                            category = Category(name=catName)
                            db.session.add(category)
                            db.session.commit()
                        else:
                            category = category[0]
                        categories.append(category)

                    product = Product.query.filter(Product.name.contains(productName)).all()
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
                            contains = False
                            for category in categories:
                                if category.name == cat.name:
                                    contains = True
                                    break
                            if not contains:
                                # product is not valid
                                isValid = False
                                break


                        print(isValid)
                        if isValid:
                            # product is valid
                            product.price = (product.quantity * product.price + quantity * price) / (product.quantity + quantity)
                            product.quantity += quantity
                            db.session.commit()

                            # check PENDING orders
                            orders = Order.query.filter(Order.pending == True)\
                                                .join(IsOrdered)\
                                                .join(Product)\
                                                .filter(Product.name == product.name)\
                                                .filter(IsOrdered.requested - IsOrdered.received > 0)\
                                                .group_by(Order.id) \
                                                .order_by(Order.date) \
                                                .all()

                            for order in orders:
                                pendingProducts = IsOrdered.query.filter(IsOrdered.orderId == order.id)\
                                                                 .join(Product)\
                                                                 .filter(Product.name == product.name) \
                                                                 .filter(IsOrdered.requested - IsOrdered.received > 0)\
                                                                 .all()

                                productIdx = 0
                                while productIdx < len(pendingProducts):
                                    leftToReceive = pendingProducts[productIdx].requested - pendingProducts[productIdx].received
                                    if leftToReceive <= product.quantity:
                                        pendingProducts[productIdx].received += leftToReceive
                                        product.quantity -= leftToReceive
                                    else:
                                        pendingProducts[productIdx].received += product.quantity
                                        product.quantity = 0
                                        break
                                    db.session.commit()
                                    productIdx += 1

                                if productIdx == len(pendingProducts):
                                    # we need to check if the order is still pending
                                    pendingProducts = IsOrdered.query.filter(IsOrdered.orderId == order.id) \
                                            .filter(IsOrdered.requested - IsOrdered.received > 0) \
                                            .all()

                                    if len(pendingProducts) == 0:
                                        order.pending = False
                                        db.session.commit()











