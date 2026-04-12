import os
from flask import Flask, render_template, session, request, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from models import db, User, Brand, CartItem, Wishlist

load_dotenv()

mail = Mail()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
csrf = CSRFProtect()

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['WTF_CSRF_CHECK_DEFAULT'] = True

database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'shop.db'))
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

app.config['MAIL_SERVER']        = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT']          = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']       = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME']      = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD']      = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@luxwatch.com')
app.config['MAIL_SUPPRESS_SEND'] = not bool(os.environ.get('MAIL_USERNAME', ''))

db.init_app(app)
mail.init_app(app)
limiter.init_app(app)
csrf.init_app(app)
migrate = Migrate(app, db)

@app.template_filter('tl')
def tl_format(value):
    try:
        return '{:,.0f}'.format(float(value)).replace(',', '.')
    except (ValueError, TypeError):
        return value

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from routes.auth import auth_bp
from routes.shop import shop_bp
from routes.admin import admin_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(profile_bp)

limiter.limit('10 per hour')(app.view_functions['auth.login'])
limiter.limit('10 per hour')(app.view_functions['auth.register'])
limiter.limit('5 per hour')(app.view_functions['auth.forgot_password'])
limiter.limit('20 per hour')(app.view_functions['shop.newsletter_subscribe'])

@app.route('/set-newsletter-shown', methods=['POST'])
def set_newsletter_shown():
    session['newsletter_popup_shown'] = True
    session.modified = True
    from flask import Response
    return Response(status=204)

csrf.exempt(set_newsletter_shown)

from routes.shop import newsletter_subscribe
csrf.exempt(newsletter_subscribe)

@app.route('/set-language/<language>')
def set_language(language):
    if language in ['tr', 'en']:
        session['language'] = language
    return redirect(request.referrer or url_for('shop.home'))

@app.context_processor
def inject_globals():
    from utils.i18n import t
    from flask_login import current_user

    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_count = sum(item.quantity for item in cart_items)
        wishlist_ids = {w.product_id for w in Wishlist.query.filter_by(user_id=current_user.id).all()}
    else:
        cart = session.get('cart', {})
        cart_count = sum(cart.values())
        wishlist_ids = set()

    brands = Brand.query.order_by(Brand.sort_order.asc()).all()
    current_lang = session.get('language', 'tr')

    def get_localized_name(obj):
        if hasattr(obj, 'get_name'):
            return obj.get_name(current_lang)
        return obj.name if hasattr(obj, 'name') else str(obj)

    return {
        'cart_count': cart_count,
        'wishlist_ids': wishlist_ids,
        'brands': brands,
        't': t,
        'current_lang': current_lang,
        'get_name': get_localized_name
    }

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
