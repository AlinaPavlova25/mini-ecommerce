from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Product, Brand, Order, OrderItem, Coupon, NewsletterSubscriber
from utils.cart import get_cart_items, calculate_cart_total
from utils.stock import check_stock_availability
from datetime import datetime
import random
import string

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def home():
    featured_products = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    if len(featured_products) < 4:
        featured_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()

    brands = Brand.query.order_by(Brand.sort_order.asc()).all()

    from models import SiteImage
    site_images = {img.key: img for img in SiteImage.query.all()}

    return render_template('home.html',
                           featured_products=featured_products,
                           brands=brands,
                           site_images=site_images)


@shop_bp.route('/products')
def product_list():
    brand_slug = request.args.get('brand')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '').strip()
    sort = request.args.get('sort', '')
    page = request.args.get('page', 1, type=int)

    query = Product.query.filter_by(is_active=True)

    selected_brand = None
    if brand_slug:
        selected_brand = Brand.query.filter_by(slug=brand_slug).first()
        if selected_brand:
            query = query.filter_by(brand_id=selected_brand.id)

    if gender and gender in ['erkek', 'kadin', 'unisex']:
        query = query.filter_by(gender=gender)

    if search_query:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.name_en.ilike(f'%{search_query}%'),
                Product.reference_number.ilike(f'%{search_query}%')
            )
        )

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    elif sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.paginate(page=page, per_page=12, error_out=False)
    brands = Brand.query.order_by(Brand.sort_order.asc()).all()

    return render_template('products/list.html',
                           products=products,
                           brands=brands,
                           selected_brand=selected_brand,
                           gender=gender,
                           search=search_query,
                           sort=sort)


@shop_bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    related_products = Product.query.filter(
        Product.brand_id == product.brand_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()

    return render_template('products/detail.html', product=product, related_products=related_products)


@shop_bp.route('/brands/<slug>')
def brand_page(slug):
    brand = Brand.query.filter_by(slug=slug).first_or_404()
    men_products = Product.query.filter_by(brand_id=brand.id, gender='erkek', is_active=True).limit(4).all()
    women_products = Product.query.filter_by(brand_id=brand.id, gender='kadin', is_active=True).limit(4).all()
    unisex_products = Product.query.filter_by(brand_id=brand.id, gender='unisex', is_active=True).limit(4).all()
    return render_template('brand.html', brand=brand,
                           men_products=men_products,
                           women_products=women_products,
                           unisex_products=unisex_products)


@shop_bp.route('/cart/add', methods=['POST'])
def cart_add():
    product_id = request.args.get('product_id', type=int) or request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    if not product_id or quantity < 1:
        flash('Geçersiz ürün veya miktar.', 'danger')
        return redirect(url_for('shop.product_list'))

    product = Product.query.get_or_404(product_id)

    if not product.is_active:
        flash('Bu ürün şu anda satışta değil.', 'warning')
        return redirect(url_for('shop.product_list'))

    cart = session.get('cart', {})
    current_qty = cart.get(str(product_id), 0)
    new_qty = current_qty + quantity

    if not product.has_sufficient_stock(new_qty):
        flash(f'Yetersiz stok. Maksimum {product.stock_qty} adet ekleyebilirsiniz.', 'warning')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    cart[str(product_id)] = new_qty
    session['cart'] = cart
    session.modified = True

    flash(f'{product.name} sepete eklendi.', 'success')
    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/cart')
def cart_view():
    cart = session.get('cart', {})
    cart_items = get_cart_items(cart)
    total = calculate_cart_total(cart_items)
    coupon_discount = session.get('coupon_discount', 0)
    coupon_code = session.get('coupon_code', '')
    final_total = max(0, total - coupon_discount)

    return render_template('cart.html',
                           cart_items=cart_items,
                           total=total,
                           coupon_discount=coupon_discount,
                           coupon_code=coupon_code,
                           final_total=final_total)


@shop_bp.route('/cart/update', methods=['POST'])
def cart_update():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 0, type=int)
    action = request.form.get('action')

    cart = session.get('cart', {})

    if action == 'remove':
        if str(product_id) in cart:
            del cart[str(product_id)]
            flash('Ürün sepetten kaldırıldı.', 'info')
    elif quantity > 0:
        product = Product.query.get(product_id)
        if product and product.has_sufficient_stock(quantity):
            cart[str(product_id)] = quantity
            flash('Sepet güncellendi.', 'success')
        else:
            flash('Yetersiz stok.', 'warning')
    else:
        if str(product_id) in cart:
            del cart[str(product_id)]

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    code = request.form.get('coupon_code', '').strip().upper()
    cart = session.get('cart', {})
    cart_items = get_cart_items(cart)
    total = calculate_cart_total(cart_items)

    if not code:
        flash('Lütfen bir kupon kodu girin.', 'warning')
        return redirect(url_for('shop.cart_view'))

    coupon = Coupon.query.filter_by(code=code, is_used=False).first()
    if not coupon:
        flash('Geçersiz veya kullanılmış kupon kodu.', 'danger')
        return redirect(url_for('shop.cart_view'))

    discount = round(total * coupon.discount_percent / 100, 2)
    session['coupon_code'] = code
    session['coupon_discount'] = discount
    session.modified = True

    flash(f'Kupon uygulandı! %{coupon.discount_percent} indirim kazandınız.', 'success')
    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/cart/remove-coupon', methods=['POST'])
def remove_coupon():
    session.pop('coupon_code', None)
    session.pop('coupon_discount', None)
    session.modified = True
    flash('Kupon kaldırıldı.', 'info')
    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip().lower()

    if not email:
        return jsonify({'success': False, 'message': 'E-posta adresi gerekli.'})

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': False, 'message': 'Bu e-posta zaten kayıtlı.', 'already_subscribed': True})

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    while Coupon.query.filter_by(code=code).first():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    coupon = Coupon(code=code, discount_percent=15, source='newsletter')
    db.session.add(coupon)

    subscriber = NewsletterSubscriber(email=email, coupon_code=code)
    db.session.add(subscriber)
    db.session.commit()

    return jsonify({'success': True, 'coupon_code': code})


@shop_bp.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Sepetiniz boş.', 'warning')
        return redirect(url_for('shop.cart_view'))

    cart_items = get_cart_items(cart)
    total = calculate_cart_total(cart_items)
    coupon_discount = session.get('coupon_discount', 0)
    final_total = max(0, total - coupon_discount)

    from models import Address
    addresses = Address.query.filter_by(user_id=current_user.id).all()

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           coupon_discount=coupon_discount,
                           final_total=final_total,
                           addresses=addresses)


@shop_bp.route('/checkout/pay', methods=['POST'])
@login_required
def checkout_pay():
    from models import Address

    cart = session.get('cart', {})
    if not cart:
        flash('Sepetiniz boş.', 'warning')
        return redirect(url_for('shop.cart_view'))

    saved_address_id = request.form.get('saved_address_id')

    if saved_address_id and saved_address_id != 'new':
        address = Address.query.get(int(saved_address_id))
        if not address or address.user_id != current_user.id:
            flash('Geçersiz adres seçimi.', 'danger')
            return redirect(url_for('shop.checkout'))
        receiver_name = address.receiver_name
        receiver_surname = address.receiver_surname
        receiver_phone = address.receiver_phone
        delivery_city = address.city
        shipping_address = address.address
    else:
        receiver_name = request.form.get('receiver_name', '').strip()
        receiver_surname = request.form.get('receiver_surname', '').strip()
        receiver_phone = request.form.get('receiver_phone', '').strip()
        delivery_city = request.form.get('delivery_city', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()

    delivery_note = request.form.get('delivery_note', '').strip()

    if not all([receiver_name, receiver_surname, receiver_phone, delivery_city, shipping_address]):
        flash('Lütfen tüm gerekli alanları doldurun.', 'danger')
        return redirect(url_for('shop.checkout'))

    card_number = request.form.get('card_number', '').replace(' ', '')
    card_expiry = request.form.get('card_expiry', '').strip()
    card_cvv = request.form.get('card_cvv', '').strip()

    if not _luhn_check(card_number):
        flash('Geçersiz kart numarası.', 'danger')
        return redirect(url_for('shop.checkout'))

    if not _expiry_check(card_expiry):
        flash('Kartın son kullanma tarihi geçmiş veya geçersiz.', 'danger')
        return redirect(url_for('shop.checkout'))

    full_address = f"{receiver_name} {receiver_surname}\nTelefon: {receiver_phone}\n{delivery_city}\n{shipping_address}"

    try:
        cart_items = get_cart_items(cart)

        for item in cart_items:
            available, msg = check_stock_availability(item['product'].id, item['quantity'])
            if not available:
                flash(f"{item['product'].name}: {msg}", 'danger')
                return redirect(url_for('shop.cart_view'))

        total = calculate_cart_total(cart_items)
        coupon_code = session.get('coupon_code', '')
        coupon_discount = session.get('coupon_discount', 0)
        final_total = max(0, total - coupon_discount)

        new_order = Order(
            user_id=current_user.id,
            status='PAID',
            total_amount=final_total,
            shipping_address=full_address,
            delivery_note=delivery_note,
            coupon_code=coupon_code if coupon_code else None,
            coupon_discount=coupon_discount
        )
        db.session.add(new_order)
        db.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                unit_price_at_purchase=item['unit_price'],
                discount_percent_at_purchase=item['discount_percent']
            )
            db.session.add(order_item)
            product = item['product']
            product.stock_qty -= item['quantity']

        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                coupon.is_used = True
                coupon.used_by_email = current_user.email
                coupon.used_at = datetime.utcnow()

        db.session.commit()

        session.pop('cart', None)
        session.pop('coupon_code', None)
        session.pop('coupon_discount', None)
        session.modified = True

        flash('Ödemeniz başarıyla alındı! Siparişiniz hazırlanıyor.', 'success')
        return redirect(url_for('shop.order_detail', order_id=new_order.id))

    except Exception as e:
        db.session.rollback()
        flash('Ödeme sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'danger')
        return redirect(url_for('shop.checkout'))


def _luhn_check(card_number):
    if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
        return False
    digits = [int(d) for d in card_number]
    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _expiry_check(expiry):
    try:
        parts = expiry.replace('-', '/').split('/')
        if len(parts) != 2:
            return False
        month = int(parts[0])
        year = int(parts[1])
        if year < 100:
            year += 2000
        if month < 1 or month > 12:
            return False
        now = datetime.utcnow()
        if year < now.year or (year == now.year and month < now.month):
            return False
        return True
    except Exception:
        return False


@shop_bp.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/list.html', orders=user_orders)


@shop_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Bu siparişe erişim yetkiniz yok.', 'danger')
        return redirect(url_for('shop.orders'))

    return render_template('orders/detail.html', order=order)


@shop_bp.route('/orders/<int:order_id>/cancel-request', methods=['POST'])
@login_required
def cancel_request(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Bu siparişe erişim yetkiniz yok.', 'danger')
        return redirect(url_for('shop.orders'))

    if not order.can_request_cancel():
        flash('Bu sipariş iptal edilemez.', 'warning')
        return redirect(url_for('shop.order_detail', order_id=order_id))

    if order.can_cancel_directly():
        order.status = 'CANCELED'
        order.updated_at = datetime.utcnow()
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock_qty += item.quantity
        db.session.commit()
        flash('Siparişiniz iptal edildi.', 'info')
    else:
        order.status = 'CANCEL_REQUESTED'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash('İptal talebiniz alındı. Admin onayı bekleniyor.', 'info')

    return redirect(url_for('shop.order_detail', order_id=order_id))
