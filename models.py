from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    
    orders = db.relationship('Order', back_populates='user', lazy='dynamic')
    addresses = db.relationship('Address', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    wishlist = db.relationship('Wishlist', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(50), nullable=False)  # "Ev", "İş", vs.
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_surname = db.Column(db.String(100), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='addresses')
    
    def __repr__(self):
        return f'<Address {self.label} - {self.city}>'


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='wishlist')
    product = db.relationship('Product')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),)
    
    def __repr__(self):
        return f'<Wishlist User:{self.user_id} Product:{self.product_id}>'


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    name_en = db.Column(db.String(50))  # İngilizce isim
    slug = db.Column(db.String(50), nullable=False, unique=True)
    
    products = db.relationship('Product', back_populates='category', lazy='dynamic')
    
    def get_name(self, lang='tr'):
        """Dile göre kategori ismini döndür"""
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))  # İngilizce isim
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    product_type = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_qty = db.Column(db.Integer, default=0, nullable=False)
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    special_occasion = db.Column(db.String(100))  # Sevgiliye, Dogum Gunu, Anneye, vb.
    subcategory = db.Column(db.String(100))  # Buket, Saksi, Madlen, Tablet, vb.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('Category', back_populates='products')
    discount_rule = db.relationship('DiscountRule', back_populates='product', uselist=False)
    order_items = db.relationship('OrderItem', back_populates='product')
    
    def get_name(self, lang='tr'):
        """Dile göre ürün ismini döndür"""
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name
    
    @property
    def active_discount(self):
        if self.discount_rule and self.discount_rule.active:
            return self.discount_rule
        return None
    
    @property
    def discounted_price(self):
        discount = self.active_discount
        if discount:
            return float(self.price) * (1 - discount.percent / 100)
        return float(self.price)
    
    @property
    def discount_amount(self):
        discount = self.active_discount
        if discount:
            return float(self.price) - self.discounted_price
        return 0
    
    def has_sufficient_stock(self, quantity):
        return self.stock_qty >= quantity
    
    def __repr__(self):
        return f'<Product {self.name}>'


class DiscountRule(db.Model):
    __tablename__ = 'discount_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True)
    percent = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', back_populates='discount_rule')
    
    def __repr__(self):
        return f'<DiscountRule {self.name} - {self.percent}%>'


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='PAID')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    delivery_note = db.Column(db.Text)
    anonymous_sender = db.Column(db.Boolean, default=False)  # Gizli gönderici
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    
    STATUS_CHOICES = [
        'PAID', 'PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY', 
        'DELIVERED', 'CANCEL_REQUESTED', 'CANCELED', 'RETURN_ARRIVED'
    ]
    
    def can_cancel_directly(self):
        return self.status in ['PAID', 'PREPARING']
    
    def can_request_cancel(self):
        return self.status not in ['DELIVERED', 'CANCELED', 'RETURN_ARRIVED']
    
    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent_at_purchase = db.Column(db.Integer, default=0, nullable=False)
    
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')
    
    @property
    def effective_price(self):
        if self.discount_percent_at_purchase > 0:
            return float(self.unit_price_at_purchase) * (1 - self.discount_percent_at_purchase / 100)
        return float(self.unit_price_at_purchase)
    
    @property
    def subtotal(self):
        return self.effective_price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.id} - Product {self.product_id}>'
