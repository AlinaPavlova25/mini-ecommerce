from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from models import db, Product, Category, Order, OrderItem, DiscountRule, User
from utils.upload import save_product_image, delete_product_image
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    total_orders = Order.query.count()
    
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    
    low_stock_products = Product.query.filter(Product.stock_qty <= 5, Product.is_active == True).all()
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_orders=total_orders,
                         today_orders=today_orders,
                         low_stock_products=low_stock_products,
                         recent_orders=recent_orders)

@admin_bp.route('/products')
@admin_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=all_products)

@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def product_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        product_type = request.form.get('product_type', '').strip()
        price = request.form.get('price', type=float)
        stock_qty = request.form.get('stock_qty', type=int)
        
        if not name or not category_id or not price or stock_qty is None:
            flash('Tüm gerekli alanları doldurun.', 'danger')
            return redirect(url_for('admin.product_new'))
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_filename = save_product_image(file, current_app.config['UPLOAD_FOLDER'])
                if not image_filename:
                    flash('Görsel yüklenirken hata oluştu. Geçerli bir resim dosyası seçin.', 'warning')
        
        new_product = Product(
            name=name,
            description=description,
            category_id=category_id,
            product_type=product_type,
            price=price,
            stock_qty=stock_qty,
            image_path=image_filename,
            is_active=True
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash(f'{name} ürünü başarıyla eklendi.', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', categories=categories, product=None)

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.product_type = request.form.get('product_type', '').strip()
        product.price = request.form.get('price', type=float)
        product.stock_qty = request.form.get('stock_qty', type=int)
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                if product.image_path:
                    delete_product_image(product.image_path, current_app.config['UPLOAD_FOLDER'])
                
                new_image = save_product_image(file, current_app.config['UPLOAD_FOLDER'])
                if new_image:
                    product.image_path = new_image
                    flash('Görsel başarıyla yüklendi.', 'success')
                else:
                    flash('Görsel yüklenirken hata oluştu. Geçerli bir resim dosyası seçin.', 'warning')
        
        db.session.commit()
        flash(f'{product.name} güncellendi.', 'success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', categories=categories, product=product)

@admin_bp.route('/products/<int:product_id>/delete-image', methods=['POST'])
@admin_required
def product_delete_image(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.image_path:
        delete_product_image(product.image_path, current_app.config['UPLOAD_FOLDER'])
        product.image_path = None
        db.session.commit()
        flash(f'{product.name} görseli silindi.', 'success')
    else:
        flash('Silinecek görsel bulunamadı.', 'warning')
    
    return redirect(url_for('admin.product_edit', product_id=product_id))

@admin_bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@admin_required
def product_toggle(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    
    status = "aktif" if product.is_active else "pasif"
    flash(f'{product.name} artık {status}.', 'info')
    return redirect(url_for('admin.products'))

@admin_bp.route('/stock')
@admin_required
def stock():
    sort_by = request.args.get('sort', 'stock')
    category_filter = request.args.get('category', type=int)
    subcategory_filter = request.args.get('subcategory', '')
    
    query = Product.query
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    if subcategory_filter:
        query = query.filter_by(subcategory=subcategory_filter)
    
    if sort_by == 'stock':
        query = query.order_by(Product.stock_qty.asc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'category':
        query = query.join(Category).order_by(Category.name.asc(), Product.name.asc())
    
    products = query.all()
    categories = Category.query.all()
    
    # Alt kategori listesi
    subcategories = db.session.query(Product.subcategory).filter(Product.subcategory.isnot(None)).distinct().all()
    subcategories = [s[0] for s in subcategories if s[0]]
    
    return render_template('admin/stock.html', products=products, categories=categories, subcategories=subcategories, sort_by=sort_by, category_filter=category_filter, subcategory_filter=subcategory_filter)

@admin_bp.route('/stock/adjust', methods=['POST'])
@admin_required
def stock_adjust():
    product_id = request.form.get('product_id', type=int)
    adjustment = request.form.get('adjustment', type=int)
    
    product = Product.query.get_or_404(product_id)
    product.stock_qty += adjustment
    
    if product.stock_qty < 0:
        product.stock_qty = 0
    
    db.session.commit()
    flash(f'{product.name} stoku güncellendi: {product.stock_qty}', 'success')
    return redirect(url_for('admin.stock'))

@admin_bp.route('/campaigns')
@admin_required
def campaigns():
    all_campaigns = DiscountRule.query.order_by(DiscountRule.created_at.desc()).all()
    products = Product.query.filter_by(is_active=True).all()
    return render_template('admin/campaigns.html', campaigns=all_campaigns, products=products)

@admin_bp.route('/campaigns/new', methods=['POST'])
@admin_required
def campaign_new():
    product_id = request.form.get('product_id', type=int)
    percent = request.form.get('percent', type=int)
    name = request.form.get('name', '').strip()
    
    if not product_id or not percent or not name:
        flash('Tüm alanları doldurun.', 'danger')
        return redirect(url_for('admin.campaigns'))
    
    if percent < 0 or percent > 100:
        flash('İndirim yüzdesi 0-100 arasında olmalıdır.', 'danger')
        return redirect(url_for('admin.campaigns'))
    
    existing = DiscountRule.query.filter_by(product_id=product_id).first()
    if existing:
        flash('Bu ürün için zaten bir kampanya var. Düzenlemek için mevcut kampanyayı güncelleyin.', 'warning')
        return redirect(url_for('admin.campaigns'))
    
    new_campaign = DiscountRule(
        product_id=product_id,
        percent=percent,
        name=name,
        active=True
    )
    
    db.session.add(new_campaign)
    db.session.commit()
    
    flash(f'{name} kampanyası oluşturuldu.', 'success')
    return redirect(url_for('admin.campaigns'))

@admin_bp.route('/campaigns/<int:campaign_id>/toggle', methods=['POST'])
@admin_required
def campaign_toggle(campaign_id):
    campaign = DiscountRule.query.get_or_404(campaign_id)
    campaign.active = not campaign.active
    db.session.commit()
    
    status = "aktif" if campaign.active else "pasif"
    flash(f'{campaign.name} artık {status}.', 'info')
    return redirect(url_for('admin.campaigns'))

@admin_bp.route('/campaigns/<int:campaign_id>/edit', methods=['POST'])
@admin_required
def campaign_edit(campaign_id):
    campaign = DiscountRule.query.get_or_404(campaign_id)
    percent = request.form.get('percent', type=int)
    name = request.form.get('name', '').strip()
    
    if not percent or not name:
        flash('Tüm alanları doldurun.', 'danger')
        return redirect(url_for('admin.campaigns'))
    
    if percent < 0 or percent > 100:
        flash('İndirim yüzdesi 0-100 arasında olmalıdır.', 'danger')
        return redirect(url_for('admin.campaigns'))
    
    campaign.percent = percent
    campaign.name = name
    db.session.commit()
    
    flash(f'{name} kampanyası güncellendi.', 'success')
    return redirect(url_for('admin.campaigns'))

@admin_bp.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
@admin_required
def campaign_delete(campaign_id):
    campaign = DiscountRule.query.get_or_404(campaign_id)
    name = campaign.name
    db.session.delete(campaign)
    db.session.commit()
    flash(f'{name} kampanyası silindi.', 'info')
    return redirect(url_for('admin.campaigns'))

@admin_bp.route('/orders')
@admin_required
def orders():
    status_filter = request.args.get('status')
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=all_orders, status_filter=status_filter)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in Order.STATUS_CHOICES:
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Sipariş durumu güncellendi: {new_status}', 'success')
    else:
        flash('Geçersiz durum.', 'danger')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/approve-cancel', methods=['POST'])
@admin_required
def order_approve_cancel(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'CANCEL_REQUESTED':
        flash('Bu sipariş iptal onayı beklemyor.', 'warning')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    
    order.status = 'CANCELED'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Sipariş #{order.id} iptal edildi.', 'info')
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/return-arrived', methods=['POST'])
@admin_required
def order_return_arrived(order_id):
    order = Order.query.get_or_404(order_id)
    
    order.status = 'RETURN_ARRIVED'
    order.updated_at = datetime.utcnow()
    
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock_qty += item.quantity
    
    db.session.commit()
    
    flash(f'Sipariş #{order.id} iadesi tamamlandı ve stok geri yüklendi.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))
