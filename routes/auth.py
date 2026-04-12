from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from models import db, User, CartItem
from utils.mail import send_password_reset, send_welcome_email
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not email or not password:
            flash('Email ve şifre gereklidir.', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'danger')
            return redirect(url_for('auth.register'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Bu email adresi zaten kayıtlı.', 'danger')
            return redirect(url_for('auth.register'))

        if phone:
            existing_phone = User.query.filter_by(phone=phone).first()
            if existing_phone:
                flash('Bu telefon numarası zaten kayıtlı.', 'danger')
                return redirect(url_for('auth.register'))
        
        new_user = User(
            email=email,
            full_name=full_name,
            phone=phone
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        try:
            shop_url = url_for('shop.product_list', _external=True)
            send_welcome_email(
                user_email=email,
                full_name=full_name or email,
                shop_url=shop_url
            )
        except Exception:
            pass

        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email ve şifre gereklidir.', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session_cart = session.get('cart', {})
            login_user(user)

            if session_cart:
                for product_id_str, qty in session_cart.items():
                    if qty > 0:
                        existing = CartItem.query.filter_by(user_id=user.id, product_id=int(product_id_str)).first()
                        if existing:
                            existing.quantity += qty
                        else:
                            db.session.add(CartItem(user_id=user.id, product_id=int(product_id_str), quantity=qty))
                db.session.commit()
                session.pop('cart', None)
                session.modified = True

            flash(f'Hoş geldiniz, {user.full_name or user.email}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('shop.home'))
        else:
            flash('Email veya şifre hatalı.', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('coupon_code', None)
    session.pop('coupon_discount', None)
    session.pop('compare', None)
    session.modified = True
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('shop.home'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Lütfen e-posta adresinizi girin.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                send_password_reset(user_email=user.email, reset_url=reset_url)
            except Exception:
                pass

            flash('Şifre sıfırlama linki e-posta adresinize gönderildi.', 'success')
        else:
            flash('Eğer bu e-posta kayıtlıysa, şifre sıfırlama linki gönderildi.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Geçersiz veya süresi dolmuş sıfırlama linki.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Şifreniz başarıyla değiştirildi. Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
