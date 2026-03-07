from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Address, Wishlist, Product, User, Coupon, NewsletterSubscriber
from werkzeug.security import generate_password_hash

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def index():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()

    subscriber = NewsletterSubscriber.query.filter_by(email=current_user.email).first()
    coupons = []
    if subscriber and subscriber.coupon_code:
        coupon = Coupon.query.filter_by(code=subscriber.coupon_code).first()
        if coupon:
            coupons.append(coupon)

    return render_template('profile/index.html', addresses=addresses, wishlist_items=wishlist_items, coupons=coupons)

@profile_bp.route('/update', methods=['POST'])
@login_required
def update_info():
    current_user.full_name = request.form.get('full_name', '').strip()
    current_user.phone = request.form.get('phone', '').strip()
    
    new_password = request.form.get('new_password', '').strip()
    if new_password:
        current_user.set_password(new_password)
        flash('Bilgileriniz ve şifreniz güncellendi.', 'success')
    else:
        flash('Bilgileriniz güncellendi.', 'success')
    
    db.session.commit()
    return redirect(url_for('profile.index'))

# Adres yönetimi
@profile_bp.route('/address/add', methods=['POST'])
@login_required
def address_add():
    label = request.form.get('label', '').strip()
    receiver_name = request.form.get('receiver_name', '').strip()
    receiver_surname = request.form.get('receiver_surname', '').strip()
    receiver_phone = request.form.get('receiver_phone', '').strip()
    city = request.form.get('city', '').strip()
    address = request.form.get('address', '').strip()
    is_default = request.form.get('is_default') == 'on'
    
    if not all([label, receiver_name, receiver_surname, receiver_phone, city, address]):
        flash('Lütfen tüm alanları doldurun.', 'danger')
        return redirect(url_for('profile.index'))
    
    # Eğer varsayılan yapıldıysa diğerlerini kaldır
    if is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    
    new_address = Address(
        user_id=current_user.id,
        label=label,
        receiver_name=receiver_name,
        receiver_surname=receiver_surname,
        receiver_phone=receiver_phone,
        city=city,
        address=address,
        is_default=is_default
    )
    
    db.session.add(new_address)
    db.session.commit()
    
    flash(f'{label} adresi eklendi.', 'success')
    return redirect(url_for('profile.index'))

@profile_bp.route('/address/<int:address_id>/edit', methods=['POST'])
@login_required
def address_edit(address_id):
    address = Address.query.get_or_404(address_id)

    if address.user_id != current_user.id:
        flash('Bu adrese erişim yetkiniz yok.', 'danger')
        return redirect(url_for('profile.index'))

    label = request.form.get('label', '').strip()
    receiver_name = request.form.get('receiver_name', '').strip()
    receiver_surname = request.form.get('receiver_surname', '').strip()
    receiver_phone = request.form.get('receiver_phone', '').strip()
    city = request.form.get('city', '').strip()
    addr_text = request.form.get('address', '').strip()

    if not all([label, receiver_name, receiver_surname, receiver_phone, city, addr_text]):
        flash('Lütfen tüm alanları doldurun.', 'danger')
        return redirect(url_for('profile.index') + '?tab=addresses')

    address.label = label
    address.receiver_name = receiver_name
    address.receiver_surname = receiver_surname
    address.receiver_phone = receiver_phone
    address.city = city
    address.address = addr_text
    db.session.commit()

    flash(f'{label} adresi güncellendi.', 'success')
    return redirect(url_for('profile.index') + '?tab=addresses')


@profile_bp.route('/address/<int:address_id>/delete', methods=['POST'])
@login_required
def address_delete(address_id):
    address = Address.query.get_or_404(address_id)
    
    if address.user_id != current_user.id:
        flash('Bu adrese erişim yetkiniz yok.', 'danger')
        return redirect(url_for('profile.index'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Adres silindi.', 'info')
    return redirect(url_for('profile.index'))

@profile_bp.route('/address/<int:address_id>/set-default', methods=['POST'])
@login_required
def address_set_default(address_id):
    address = Address.query.get_or_404(address_id)
    
    if address.user_id != current_user.id:
        flash('Bu adrese erişim yetkiniz yok.', 'danger')
        return redirect(url_for('profile.index'))
    
    # Tüm adresleri varsayılan olmaktan çıkar
    Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    
    # Bu adresi varsayılan yap
    address.is_default = True
    db.session.commit()
    
    flash(f'{address.label} varsayılan adres olarak ayarlandı.', 'success')
    return redirect(url_for('profile.index'))

# Wishlist yönetimi
@profile_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def wishlist_add(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Zaten ekli mi kontrol et
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash(f'{product.name} zaten beğenilen ürünler listenizde.', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f'{product.name} beğenilen ürünlere eklendi.', 'success')
    
    # Geri dön
    return redirect(request.referrer or url_for('shop.home'))

@profile_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def wishlist_remove(product_id):
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Ürün beğenilen listesinden kaldırıldı.', 'info')
    
    return redirect(request.referrer or url_for('profile.index'))
