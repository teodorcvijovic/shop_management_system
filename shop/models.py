import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class HasCategory(db.Model):
    __tablename__ = "hascategory"

    id = db.Column(db.Integer, primary_key=True)
    productId = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    categoryId = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

class IsOrdered(db.Model):
    __tablename__ = 'isordered'

    id = db.Column(db.Integer, primary_key=True)
    productId = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    requested = db.Column(db.Integer, nullable=False)
    received = db.Column(db.Integer, nullable=False)

    products = db.relationship("Product", secondary=HasCategory.__table__, back_populates="categories")

    def __repr__(self):
        return self.name

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    categories = db.relationship("Category", secondary=HasCategory.__table__, back_populates="products")
    orders = db.relationship("Order", secondary=HasCategory.__table__, back_populates="products")

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    successful = db.Column(db.Boolean, nullable=False)  # status: SUCCESSFUL or ON WAITING
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    products = db.relationship("Product", secondary=HasCategory.__table__, back_populates="orders")

