import os
from flask import Flask, render_template, session, request, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager
from models import db, User, Brand

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes.auth import auth_bp
from routes.shop import shop_bp
from routes.admin import admin_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(profile_bp)

@app.route('/set-newsletter-shown', methods=['POST'])
def set_newsletter_shown():
    session['newsletter_popup_shown'] = True
    session.modified = True
    from flask import Response
    return Response(status=204)

@app.route('/set-language/<language>')
def set_language(language):
    if language in ['tr', 'en']:
        session['language'] = language
    return redirect(request.referrer or url_for('shop.home'))

@app.context_processor
def inject_globals():
    from utils.i18n import t
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    brands = Brand.query.order_by(Brand.sort_order.asc()).all()
    current_lang = session.get('language', 'tr')

    def get_localized_name(obj):
        if hasattr(obj, 'get_name'):
            return obj.get_name(current_lang)
        return obj.name if hasattr(obj, 'name') else str(obj)

    return {
        'cart_count': cart_count,
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
    app.run(debug=True, host='0.0.0.0', port=5000)
