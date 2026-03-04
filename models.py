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
    label = db.Column(db.String(50), nullable=False)
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


class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    logo_path = db.Column(db.String(200))
    founded_year = db.Column(db.Integer)
    country = db.Column(db.String(100))
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship('Product', back_populates='brand', lazy='dynamic')

    def __repr__(self):
        return f'<Brand {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    GENDER_CHOICES = ['erkek', 'kadin', 'unisex']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200))
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    gender = db.Column(db.String(10), nullable=False, default='unisex')  # erkek / kadin / unisex
    reference_number = db.Column(db.String(100))   # örn: Rolex 116610LN
    case_material = db.Column(db.String(100))       # Çelik, Altın, Titanyum
    case_diameter = db.Column(db.String(20))        # örn: 41mm
    movement = db.Column(db.String(100))            # Otomatik, Kuvars vb.
    water_resistance = db.Column(db.String(50))     # örn: 300m
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_qty = db.Column(db.Integer, default=0, nullable=False)
    image_path = db.Column(db.String(200))
    video_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    brand = db.relationship('Brand', back_populates='products')
    discount_rule = db.relationship('DiscountRule', back_populates='product', uselist=False)
    order_items = db.relationship('OrderItem', back_populates='product')
    images = db.relationship('ProductImage', back_populates='product', cascade='all, delete-orphan', order_by='ProductImage.sort_order')

    def get_name(self, lang='tr'):
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name

    def get_description(self, lang='tr'):
        if lang == 'en' and self.description_en:
            return self.description_en
        return self.description

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
        if self.active_discount:
            return float(self.price) - self.discounted_price
        return 0

    def has_sufficient_stock(self, quantity):
        return self.stock_qty >= quantity

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', back_populates='images')

    def __repr__(self):
        return f'<ProductImage {self.id} - Product {self.product_id}>'


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


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False, default=15)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_by_email = db.Column(db.String(120))
    source = db.Column(db.String(50), default='newsletter')  # newsletter / manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Coupon {self.code} - {self.discount_percent}%>'


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    coupon_code = db.Column(db.String(50))
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Newsletter {self.email}>'


class SiteImage(db.Model):
    __tablename__ = 'site_images'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)  # hero_banner, brand_rolex vb.
    label = db.Column(db.String(100), nullable=False)             # Admin'de gösterilecek isim
    image_path = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SiteImage {self.key}>'


class Order(db.Model):
    __tablename__ = 'orders'

    STATUS_CHOICES = [
        'PAID', 'PREPARING', 'SHIPPED', 'OUT_FOR_DELIVERY',
        'DELIVERED', 'CANCEL_REQUESTED', 'CANCELED', 'RETURN_ARRIVED'
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='PAID')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    delivery_note = db.Column(db.Text)
    coupon_code = db.Column(db.String(50))
    coupon_discount = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

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
