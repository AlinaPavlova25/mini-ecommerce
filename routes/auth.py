from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from models import db, User
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
        
        new_user = User(
            email=email,
            full_name=full_name,
            phone=phone
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
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
            login_user(user)
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
    session.pop('cart', None)
    logout_user()
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
            # Token oluştur
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Mail gönderme (basit versiyon - gerçek mail göndermeden)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            
            # GERÇEK UYGULAMADA BURADA MAİL GÖNDERİLECEK
            # send_email(user.email, 'Şifre Sıfırlama', reset_link)
            
            # Geliştirme aşaması için linki göster
            flash(f'Şifre sıfırlama linki (mail yerine): {reset_link}', 'info')
            flash('Şifre sıfırlama linki e-posta adresinize gönderildi.', 'success')
        else:
            # Güvenlik için kullanıcı bulunamasa bile başarılı mesajı göster
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
