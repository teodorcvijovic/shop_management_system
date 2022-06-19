from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

ADMIN_ROLE_ID = 1
SALESMAN_ROLE_ID = 2
CUSTOMER_ROLE_ID = 3

class HasRole(db.Model):
    __tablename__ = "hasrole"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    roleId = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True);
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    forename = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(256), nullable=False)

    roles = db.relationship("Role", secondary=HasRole.__table__, back_populates="users")


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    users = db.relationship("User", secondary=HasRole.__table__, back_populates="roles")

    def __repr__(self):
        return self.name
