from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Product, Category, Order, OrderItem
from utils.cart import get_cart_items, calculate_cart_total
from utils.stock import check_stock_availability
from datetime import datetime

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/debug-images')
def debug_images():
    return render_template('debug_images.html')

@shop_bp.route('/image-test')
def image_test():
    return render_template('image_test.html')

@shop_bp.route('/')
def home():
    featured_products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    
    discounted_products = []
    for product in Product.query.filter_by(is_active=True).all():
        if product.active_discount:
            discounted_products.append(product)
    
    return render_template('home.html', 
                         featured_products=featured_products,
                         discounted_products=discounted_products)

@shop_bp.route('/products')
def product_list():
    category_slug = request.args.get('category')
    search_query = request.args.get('search', '').strip()
    sort = request.args.get('sort', '')
    page = request.args.get('page', 1, type=int)
    show_discounted = request.args.get('discounted', type=int)
    
    query = Product.query.filter_by(is_active=True)
    
    category = None
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    if show_discounted:
        # İndirimli ürünleri getir
        from models import DiscountRule
        discounted_ids = db.session.query(DiscountRule.product_id).filter_by(active=True).all()
        discounted_ids = [d[0] for d in discounted_ids]
        query = query.filter(Product.id.in_(discounted_ids))
    
    if search_query:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
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
    
    return render_template('products/list.html', products=products, category=category, search=search_query, show_discounted=show_discounted)

@shop_bp.route('/products/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    return render_template('products/detail.html', product=product, related_products=related_products)

@shop_bp.route('/cart/add', methods=['POST'])
def cart_add():
    # URL parametresi veya form'dan product_id al
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
    
    return render_template('cart.html', cart_items=cart_items, total=total)

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

@shop_bp.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Sepetiniz boş.', 'warning')
        return redirect(url_for('shop.cart_view'))
    
    cart_items = get_cart_items(cart)
    total = calculate_cart_total(cart_items)
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@shop_bp.route('/checkout/pay', methods=['POST'])
@login_required
def checkout_pay():
    from models import Address
    
    cart = session.get('cart', {})
    if not cart:
        flash('Sepetiniz boş.', 'warning')
        return redirect(url_for('shop.cart_view'))
    
    # Kayıtlı adres veya yeni adres
    saved_address_id = request.form.get('saved_address_id')
    
    if saved_address_id and saved_address_id != 'new':
        # Kayıtlı adres kullan
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
        # Manuel adres
        receiver_name = request.form.get('receiver_name', '').strip()
        receiver_surname = request.form.get('receiver_surname', '').strip()
        receiver_phone = request.form.get('receiver_phone', '').strip()
        delivery_city = request.form.get('delivery_city', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
    
    delivery_note = request.form.get('delivery_note', '').strip()
    anonymous_sender = request.form.get('anonymous_sender') == '1'
    
    if not all([receiver_name, receiver_surname, receiver_phone, delivery_city, shipping_address]):
        flash('Lütfen tüm gerekli alanları doldurun.', 'danger')
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
        
        new_order = Order(
            user_id=current_user.id,
            status='PAID',
            total_amount=total,
            shipping_address=full_address,
            delivery_note=delivery_note,
            anonymous_sender=anonymous_sender
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
        
        db.session.commit()
        
        session['cart'] = {}
        session.modified = True
        
        flash('Ödemeniz başarıyla alındı! Siparişiniz hazırlanıyor.', 'success')
        return redirect(url_for('shop.order_detail', order_id=new_order.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Ödeme sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'danger')
        return redirect(url_for('shop.checkout'))

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
        flash('Siparişiniz iptal edildi ve stok iade edildi.', 'info')
    else:
        order.status = 'CANCEL_REQUESTED'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash('İptal talebiniz alındı. Admin onayı bekleniyor.', 'info')
    
    return redirect(url_for('shop.order_detail', order_id=order_id))
