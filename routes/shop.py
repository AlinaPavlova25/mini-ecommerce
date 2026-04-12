from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Product, Brand, Order, OrderItem, Coupon, NewsletterSubscriber, CartItem, StockNotification
from utils.cart import get_cart_items, calculate_cart_total
from utils.mail import send_order_confirmation
from utils.stock import check_stock_availability
from datetime import datetime
import random
import string

shop_bp = Blueprint('shop', __name__)


def _get_cart_dict():
    if current_user.is_authenticated:
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        return {str(item.product_id): item.quantity for item in items}
    return session.get('cart', {})


def _save_cart_dict(cart_dict):
    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        for product_id_str, qty in cart_dict.items():
            if qty > 0:
                db.session.add(CartItem(user_id=current_user.id, product_id=int(product_id_str), quantity=qty))
        db.session.commit()
    else:
        session['cart'] = cart_dict
        session.modified = True


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


PRICE_RANGES = [
    ('0-50000',    0,      50000),
    ('50000-150000', 50000, 150000),
    ('150000-500000', 150000, 500000),
    ('500000+',    500000, None),
]


@shop_bp.route('/products')
def product_list():
    brand_slug = request.args.get('brand')
    gender = request.args.get('gender')
    search_query = request.args.get('search', '').strip()
    sort = request.args.get('sort', '')
    price_range = request.args.get('price_range', '')
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
                Product.name_en.ilike(f'%{search_query}%')
            )
        )

    selected_price_range = None
    price_low = None
    price_high = None
    if price_range:
        for key, low, high in PRICE_RANGES:
            if key == price_range:
                selected_price_range = key
                price_low = low
                price_high = high
                break

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

    if selected_price_range is not None:
        all_products = query.all()
        filtered = [
            p for p in all_products
            if p.discounted_price >= price_low and (price_high is None or p.discounted_price < price_high)
        ]
        per_page = 12
        total = len(filtered)
        start = (page - 1) * per_page
        items = filtered[start:start + per_page]

        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = max(1, -(-total // per_page))
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if (num <= left_edge or
                        (self.page - left_current - 1 < num < self.page + right_current) or
                        num > self.pages - right_edge):
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num

        products = SimplePagination(items, page, per_page, total)
    else:
        products = query.paginate(page=page, per_page=12, error_out=False)
    brands = Brand.query.order_by(Brand.sort_order.asc()).all()

    return render_template('products/list.html',
                           products=products,
                           brands=brands,
                           selected_brand=selected_brand,
                           gender=gender,
                           search=search_query,
                           sort=sort,
                           price_range=selected_price_range,
                           price_ranges=PRICE_RANGES)


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
    men_products     = Product.query.filter_by(brand_id=brand.id, gender='erkek',  is_active=True).limit(4).all()
    women_products   = Product.query.filter_by(brand_id=brand.id, gender='kadin',  is_active=True).limit(4).all()
    unisex_products  = Product.query.filter_by(brand_id=brand.id, gender='unisex', is_active=True).limit(4).all()
    total_products   = Product.query.filter_by(brand_id=brand.id, is_active=True).count()
    featured_product = (Product.query
                        .filter_by(brand_id=brand.id, is_active=True)
                        .filter(Product.stock_qty > 0)
                        .order_by(Product.price.desc())
                        .first())
    return render_template('brand.html', brand=brand,
                           men_products=men_products,
                           women_products=women_products,
                           unisex_products=unisex_products,
                           total_products=total_products,
                           featured_product=featured_product)


@shop_bp.route('/stock-notify/<int:product_id>', methods=['POST'])
def stock_notify(product_id):
    product = Product.query.get_or_404(product_id)
    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Lütfen e-posta adresinizi girin.' if session.get('language', 'tr') == 'tr' else 'Please enter your email address.', 'warning')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    if product.stock_qty > 0:
        flash('Bu ürün zaten stokta mevcut.' if session.get('language', 'tr') == 'tr' else 'This product is already in stock.', 'info')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    existing = StockNotification.query.filter_by(product_id=product_id, email=email).first()
    if existing:
        flash('Bu e-posta zaten bildirim listesinde.' if session.get('language', 'tr') == 'tr' else 'This email is already on the notification list.', 'info')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    notif = StockNotification(product_id=product_id, email=email)
    db.session.add(notif)
    db.session.commit()

    flash('Ürün tekrar stoka girdiğinde e-posta ile bildirileceksiniz.' if session.get('language', 'tr') == 'tr' else 'You will be notified by email when this product is back in stock.', 'success')
    return redirect(url_for('shop.product_detail', product_id=product_id))


@shop_bp.route('/compare/add/<int:product_id>', methods=['POST'])
def compare_add(product_id):
    Product.query.get_or_404(product_id)
    compare = session.get('compare', [])
    if product_id not in compare:
        if len(compare) >= 3:
            flash('En fazla 3 ürün karşılaştırabilirsiniz.' if session.get('language', 'tr') == 'tr' else 'You can compare up to 3 products.', 'warning')
        else:
            compare.append(product_id)
            session['compare'] = compare
            session.modified = True
    return redirect(request.referrer or url_for('shop.product_list'))


@shop_bp.route('/compare/remove/<int:product_id>', methods=['POST'])
def compare_remove(product_id):
    compare = session.get('compare', [])
    if product_id in compare:
        compare.remove(product_id)
        session['compare'] = compare
        session.modified = True
    return redirect(request.referrer or url_for('shop.compare_view'))


@shop_bp.route('/compare/clear', methods=['POST'])
def compare_clear():
    session.pop('compare', None)
    session.modified = True
    return redirect(url_for('shop.product_list'))


@shop_bp.route('/compare')
def compare_view():
    compare_ids = session.get('compare', [])
    products = [db.session.get(Product, pid) for pid in compare_ids if db.session.get(Product, pid)]
    return render_template('products/compare.html', products=products)


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

    cart = _get_cart_dict()
    current_qty = cart.get(str(product_id), 0)
    new_qty = current_qty + quantity

    if not product.has_sufficient_stock(new_qty):
        flash(f'Yetersiz stok. Maksimum {product.stock_qty} adet ekleyebilirsiniz.', 'warning')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    cart[str(product_id)] = new_qty
    _save_cart_dict(cart)

    flash(f'{product.name} sepete eklendi.', 'success')
    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/cart')
def cart_view():
    cart = _get_cart_dict()
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

    cart = _get_cart_dict()

    if action == 'remove':
        if str(product_id) in cart:
            del cart[str(product_id)]
            flash('Ürün sepetten kaldırıldı.', 'info')
    elif quantity > 0:
        product = db.session.get(Product, product_id)
        if product and product.has_sufficient_stock(quantity):
            cart[str(product_id)] = quantity
            flash('Sepet güncellendi.', 'success')
        else:
            flash('Yetersiz stok.', 'warning')
    else:
        if str(product_id) in cart:
            del cart[str(product_id)]

    _save_cart_dict(cart)

    return redirect(url_for('shop.cart_view'))


@shop_bp.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    code = request.form.get('coupon_code', '').strip().upper()
    cart = _get_cart_dict()
    cart_items = get_cart_items(cart)
    total = calculate_cart_total(cart_items)

    if not code:
        flash('Lütfen bir kupon kodu girin.', 'warning')
        return redirect(url_for('shop.cart_view'))

    coupon = Coupon.query.filter_by(code=code, is_used=False).first()
    if not coupon:
        flash('Geçersiz veya kullanılmış kupon kodu.', 'danger')
        return redirect(url_for('shop.cart_view'))

    if coupon.source == 'newsletter':
        subscriber = NewsletterSubscriber.query.filter_by(coupon_code=code).first()
        if subscriber:
            user_email = current_user.email if current_user.is_authenticated else None
            if not user_email or subscriber.email.lower() != user_email.lower():
                flash('Bu kupon kodu size ait değil.', 'danger')
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
    cart = _get_cart_dict()
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

    cart = _get_cart_dict()
    if not cart:
        flash('Sepetiniz boş.', 'warning')
        return redirect(url_for('shop.cart_view'))

    saved_address_id = request.form.get('saved_address_id')

    if saved_address_id and saved_address_id != 'new':
        address = db.session.get(Address, int(saved_address_id))
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
    installment_count = request.form.get('installment_count', 1, type=int)
    if installment_count not in [1, 2, 3, 4, 5, 6, 9, 12]:
        installment_count = 1

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

        ANNUAL_RATE = 0.12
        if installment_count <= 1:
            installment_total = final_total
        elif installment_count <= 3:
            installment_total = final_total
        else:
            monthly_rate = ANNUAL_RATE / 12
            monthly = final_total * (monthly_rate * (1 + monthly_rate) ** installment_count) / ((1 + monthly_rate) ** installment_count - 1)
            installment_total = round(monthly * installment_count, 2)

        new_order = Order(
            user_id=current_user.id,
            status='PAID',
            total_amount=installment_total,
            shipping_address=full_address,
            delivery_note=delivery_note,
            coupon_code=coupon_code if coupon_code else None,
            coupon_discount=coupon_discount,
            installment_count=installment_count
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

        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        session.pop('coupon_code', None)
        session.pop('coupon_discount', None)
        session.modified = True

        try:
            send_order_confirmation(
                user_email=current_user.email,
                user_name=current_user.full_name or current_user.email,
                order=new_order,
            )
        except Exception:
            pass

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
            product = db.session.get(Product, item.product_id)
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


@shop_bp.route('/orders/<int:order_id>/return-request', methods=['POST'])
@login_required
def return_request(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Bu siparişe erişim yetkiniz yok.', 'danger')
        return redirect(url_for('shop.orders'))

    if not order.can_request_return():
        flash('Bu sipariş için iade talebi oluşturulamaz.', 'warning')
        return redirect(url_for('shop.order_detail', order_id=order_id))

    code = 'RET-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    order.return_code = code
    order.return_requested_at = datetime.utcnow()
    order.status = 'RETURN_REQUESTED'
    order.updated_at = datetime.utcnow()
    db.session.commit()

    flash(f'İade kodunuz: {code} — Bu kodu kargo paketinize yazın.', 'info')
    return redirect(url_for('shop.order_detail', order_id=order_id))


@shop_bp.route('/hakkimizda')
@shop_bp.route('/about')
def about():
    return render_template('about.html')


@shop_bp.route('/sss')
@shop_bp.route('/faq')
def faq():
    return render_template('faq.html')
