from sqlalchemy import create_engine, TIMESTAMP, Column, Integer, String, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from urllib.parse import quote_plus
from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a Flask web application instance
app = Flask(__name__)

# Database configuration - Retrieve values from environment variables
db_name = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = quote_plus(os.getenv('DB_PASSWORD'))  # Encode the password with special characters
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')

# Construct the database URL using the retrieved configuration values
db_url = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"

# Configure the Flask app with the database URL and disable modification tracking
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()

# Creating Flask-Migrate instance
migrate = Migrate(app, db)

# User table with information about the user
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    role = db.Column(db.String(255))
    email_list = db.Column(db.Boolean)
    verified_email = db.Column(db.Boolean)
    verification_code = db.Column(db.String(255))
    verification_code_created_at = db.Column(db.TIMESTAMP)
    logged_in = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)

    orders = db.relationship("Order", back_populates="user")
    cart_items = db.relationship("Cart", back_populates="user")
    email_subscriptions = db.relationship("EmailList", back_populates="user")

    def serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'user_type': self.user_type,
            'email_list': self.email_list,
            'verified_email': self.verified_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
# Product categories
class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)

    products = db.relationship("Product", back_populates="category")
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
# Product information
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    title = db.Column(db.String(255))
    status = db.Column(db.String(255))
    description = db.Column(db.Text)
    meta_description = db.Column(db.String(160))
    focus_keyword = db.Column(db.String(160))
    sale_price = db.Column(db.Float)
    price = db.Column(db.Float)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)

    category = db.relationship("Category", back_populates="products")
    images = db.relationship("ProductImage", back_populates="product")
    order_items = db.relationship("OrderItem", back_populates="product")
    cart = db.relationship("Cart", back_populates="product")

    def serialize(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'title': self.title,
            'status': self.status,
            'description': self.description,
            'meta_description': self.meta_description,
            'focus_keyword': self.focus_keyword,
            'sale_price': self.sale_price,
            'price': self.price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Product images
class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    main_image = db.Column(db.Text)
    mockup_01 = db.Column(db.Text)
    mockup_02 = db.Column(db.Text)
    mockup_03 = db.Column(db.Text)
    mockup_04 = db.Column(db.Text)
    mockup_05 = db.Column(db.Text)
    mockup_06 = db.Column(db.Text)
    mockup_07 = db.Column(db.Text)
    mockup_08 = db.Column(db.Text)
    mockup_09 = db.Column(db.Text)
    mockup_10 = db.Column(db.Text)
    mockup_11 = db.Column(db.Text)
    mockup_12 = db.Column(db.Text)
    mockup_13 = db.Column(db.Text)
    mockup_14 = db.Column(db.Text)

    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'))
    
    product = db.relationship("Product", back_populates="images")
    order_item = db.relationship("OrderItem", back_populates="product_image")

    def serialize(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'main_image': self.main_image,
            'mockup_01': self.mockup_01,
            'mockup_02': self.mockup_02,
            'mockup_03': self.mockup_03,
            'mockup_04': self.mockup_04,
            'mockup_05': self.mockup_05,
            'mockup_06': self.mockup_06,
            'mockup_07': self.mockup_07,
            'mockup_08': self.mockup_08,
            'mockup_09': self.mockup_09,
            'mockup_10': self.mockup_10,
            'mockup_11': self.mockup_11,
            'mockup_12': self.mockup_12,
            'mockup_13': self.mockup_13,
            'mockup_14': self.mockup_14
        }

# Completed order
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    download_link = db.Column(db.String(255))
    order_date = db.Column(db.TIMESTAMP)
    total_amount = db.Column(db.Float)

    # Add the foreign key to establish the relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="orders")

    items = db.relationship("OrderItem", back_populates="order")

    def serialize(self):
        return {
            'id': self.id,
            'download_link': self.download_link,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'total_amount': self.total_amount
        }

# Information about a single item in the completed order
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    price_per_unit = db.Column(db.Float)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")
    product_image = db.relationship("ProductImage", back_populates="order_item")

    def serialize(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'price_per_unit': self.price_per_unit
        }

# Information about what the user put in the cart
class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    created_at = db.Column(db.TIMESTAMP)

    user = db.relationship("User", back_populates="cart_items")
    product = db.relationship("Product", back_populates="cart")

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# A list of user who agreed to join the email list
class EmailList(db.Model):
    __tablename__ = 'email_list'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    first_name = db.Column(db.String(255))
    email = db.Column(db.String(255))

    user = db.relationship("User", back_populates="email_subscriptions")

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'email': self.email
        }
        
if __name__ == '__main__':
    app.run()