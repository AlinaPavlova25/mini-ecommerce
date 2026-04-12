from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from models import db, Product, Brand, Order, OrderItem, DiscountRule, User, SiteImage, Coupon, NewsletterSubscriber, ProductImage, CartItem, Wishlist, StockNotification
from utils.upload import save_product_image, delete_product_image, save_product_video, save_banner_image
from utils.mail import send_stock_notification
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(*roles):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


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
    sort = request.args.get('sort', 'created_desc')
    brand_filter = request.args.get('brand', type=int)
    gender_filter = request.args.get('gender', '')
    search = request.args.get('q', '').strip()

    query = Product.query
    if brand_filter:
        query = query.filter_by(brand_id=brand_filter)
    if gender_filter:
        query = query.filter_by(gender=gender_filter)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    sort_map = {
        'created_desc': Product.created_at.desc(),
        'created_asc':  Product.created_at.asc(),
        'name_asc':     Product.name.asc(),
        'name_desc':    Product.name.desc(),
        'price_asc':    Product.price.asc(),
        'price_desc':   Product.price.desc(),
        'stock_asc':    Product.stock_qty.asc(),
        'stock_desc':   Product.stock_qty.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))
    all_products = query.all()
    all_brands = Brand.query.order_by(Brand.name.asc()).all()

    return render_template('admin/products.html', products=all_products,
                           all_brands=all_brands, sort=sort,
                           brand_filter=brand_filter, gender_filter=gender_filter,
                           search=search)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def product_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        name_en = request.form.get('name_en', '').strip()
        description = request.form.get('description', '').strip()
        description_en = request.form.get('description_en', '').strip()
        brand_id = request.form.get('brand_id', type=int)
        gender = request.form.get('gender', 'unisex')
        reference_number = request.form.get('reference_number', '').strip()
        case_material = request.form.get('case_material', '').strip()
        case_material_en = request.form.get('case_material_en', '').strip()
        case_diameter = request.form.get('case_diameter', '').strip()
        movement = request.form.get('movement', '').strip()
        movement_en = request.form.get('movement_en', '').strip()
        water_resistance = request.form.get('water_resistance', '').strip()
        price = request.form.get('price', type=float)
        stock_qty = request.form.get('stock_qty', type=int)
        is_featured = request.form.get('is_featured') == '1'

        if not name or not brand_id or not price or stock_qty is None:
            flash('Tüm gerekli alanları doldurun.', 'danger')
            return redirect(url_for('admin.product_new'))

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_filename = save_product_image(file, current_app.config['UPLOAD_FOLDER'])
                if not image_filename:
                    flash('Görsel yüklenirken hata oluştu.', 'warning')

        new_product = Product(
            name=name,
            name_en=name_en,
            description=description,
            description_en=description_en,
            brand_id=brand_id,
            gender=gender,
            reference_number=reference_number,
            case_material=case_material,
            case_material_en=case_material_en,
            case_diameter=case_diameter,
            movement=movement,
            movement_en=movement_en,
            water_resistance=water_resistance,
            price=price,
            stock_qty=stock_qty,
            image_path=image_filename,
            is_active=True,
            is_featured=is_featured
        )
        db.session.add(new_product)
        db.session.commit()

        flash(f'{name} ürünü başarıyla eklendi.', 'success')
        return redirect(url_for('admin.products'))

    brands = Brand.query.order_by(Brand.name.asc()).all()
    return render_template('admin/product_form.html', brands=brands, product=None)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.name_en = request.form.get('name_en', '').strip()
        product.description = request.form.get('description', '').strip()
        product.description_en = request.form.get('description_en', '').strip()
        product.brand_id = request.form.get('brand_id', type=int)
        product.gender = request.form.get('gender', 'unisex')
        product.reference_number = request.form.get('reference_number', '').strip()
        product.case_material = request.form.get('case_material', '').strip()
        product.case_material_en = request.form.get('case_material_en', '').strip()
        product.case_diameter = request.form.get('case_diameter', '').strip()
        product.movement = request.form.get('movement', '').strip()
        product.movement_en = request.form.get('movement_en', '').strip()
        product.water_resistance = request.form.get('water_resistance', '').strip()
        product.price = request.form.get('price', type=float)
        product.stock_qty = request.form.get('stock_qty', type=int)
        product.is_featured = request.form.get('is_featured') == '1'

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
                    flash('Görsel yüklenirken hata oluştu.', 'warning')

        db.session.commit()
        flash(f'{product.name} güncellendi.', 'success')
        return redirect(url_for('admin.product_edit', product_id=product_id))

    brands = Brand.query.order_by(Brand.name.asc()).all()
    return render_template('admin/product_form.html', brands=brands, product=product)


@admin_bp.route('/products/<int:product_id>/images/upload', methods=['POST'])
@admin_required
def product_image_upload(product_id):
    product = Product.query.get_or_404(product_id)
    files = request.files.getlist('images')
    uploaded = 0
    for file in files:
        if file and file.filename:
            path = save_product_image(file, current_app.config['UPLOAD_FOLDER'])
            if path:
                img = ProductImage(product_id=product.id, image_path=path, sort_order=len(product.images))
                db.session.add(img)
                uploaded += 1
    db.session.commit()
    if uploaded:
        flash(f'{uploaded} görsel yüklendi.', 'success')
    else:
        flash('Görsel yüklenemedi.', 'warning')
    return redirect(url_for('admin.product_edit', product_id=product_id))


@admin_bp.route('/products/<int:product_id>/images/<int:image_id>/delete', methods=['POST'])
@admin_required
def product_image_delete(product_id, image_id):
    img = ProductImage.query.get_or_404(image_id)
    delete_product_image(img.image_path, current_app.config['UPLOAD_FOLDER'])
    db.session.delete(img)
    db.session.commit()
    flash('Görsel silindi.', 'info')
    return redirect(url_for('admin.product_edit', product_id=product_id))


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    if product.image_path:
        delete_product_image(product.image_path, current_app.config['UPLOAD_FOLDER'])
    if product.video_path:
        delete_product_image(product.video_path, current_app.config['UPLOAD_FOLDER'])
    for img in product.images:
        delete_product_image(img.image_path, current_app.config['UPLOAD_FOLDER'])
    CartItem.query.filter_by(product_id=product_id).delete()
    Wishlist.query.filter_by(product_id=product_id).delete()
    StockNotification.query.filter_by(product_id=product_id).delete()
    db.session.delete(product)
    db.session.commit()
    flash(f'"{name}" silindi.', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/video/upload', methods=['POST'])
@admin_required
def product_video_upload(product_id):
    product = Product.query.get_or_404(product_id)
    file = request.files.get('video')
    if not file or not file.filename:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('admin.product_edit', product_id=product_id))
    if product.video_path:
        delete_product_image(product.video_path, current_app.config['UPLOAD_FOLDER'])
    path = save_product_video(file, current_app.config['UPLOAD_FOLDER'])
    if path:
        product.video_path = path
        db.session.commit()
        flash('Video yüklendi.', 'success')
    else:
        flash('Video yüklenemedi. MP4, WEBM veya MOV dosyası seçin.', 'danger')
    return redirect(url_for('admin.product_edit', product_id=product_id))


@admin_bp.route('/products/<int:product_id>/video/delete', methods=['POST'])
@admin_required
def product_video_delete(product_id):
    product = Product.query.get_or_404(product_id)
    if product.video_path:
        delete_product_image(product.video_path, current_app.config['UPLOAD_FOLDER'])
        product.video_path = None
        db.session.commit()
        flash('Video silindi.', 'info')
    return redirect(url_for('admin.product_edit', product_id=product_id))


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


@admin_bp.route('/brands')
@admin_required
def brands():
    all_brands = Brand.query.order_by(Brand.sort_order.asc()).all()
    return render_template('admin/brands.html', brands=all_brands)


@admin_bp.route('/brands/new', methods=['GET', 'POST'])
@admin_required
def brand_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        description_en = request.form.get('description_en', '').strip()
        founded_year = request.form.get('founded_year', type=int)
        country = request.form.get('country', '').strip()
        sort_order = request.form.get('sort_order', 0, type=int)

        if not name or not slug:
            flash('İsim ve slug gerekli.', 'danger')
            return redirect(url_for('admin.brand_new'))

        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                logo_path = save_product_image(file, current_app.config['UPLOAD_FOLDER'])

        cover_image_path = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                cover_image_path = save_banner_image(file, current_app.config['UPLOAD_FOLDER'])

        brand = Brand(name=name, slug=slug, description=description, description_en=description_en,
                      founded_year=founded_year, country=country, sort_order=sort_order,
                      logo_path=logo_path, cover_image_path=cover_image_path)
        db.session.add(brand)
        db.session.commit()
        flash(f'{name} markası eklendi.', 'success')
        return redirect(url_for('admin.brands'))

    return render_template('admin/brand_form.html', brand=None)


@admin_bp.route('/brands/<int:brand_id>/edit', methods=['GET', 'POST'])
@admin_required
def brand_edit(brand_id):
    brand = Brand.query.get_or_404(brand_id)

    if request.method == 'POST':
        brand.name = request.form.get('name', '').strip()
        brand.slug = request.form.get('slug', '').strip()
        brand.description = request.form.get('description', '').strip()
        brand.description_en = request.form.get('description_en', '').strip()
        brand.founded_year = request.form.get('founded_year', type=int)
        brand.country = request.form.get('country', '').strip()
        brand.sort_order = request.form.get('sort_order', 0, type=int)

        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                if brand.logo_path:
                    delete_product_image(brand.logo_path, current_app.config['UPLOAD_FOLDER'])
                brand.logo_path = save_product_image(file, current_app.config['UPLOAD_FOLDER'])

        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                if brand.cover_image_path:
                    delete_product_image(brand.cover_image_path, current_app.config['UPLOAD_FOLDER'])
                brand.cover_image_path = save_banner_image(file, current_app.config['UPLOAD_FOLDER'])

        db.session.commit()
        flash(f'{brand.name} güncellendi.', 'success')
        return redirect(url_for('admin.brands'))

    return render_template('admin/brand_form.html', brand=brand)


@admin_bp.route('/stock')
@admin_required
def stock():
    sort_by = request.args.get('sort', 'stock')
    brand_filter = request.args.get('brand', type=int)

    query = Product.query

    if brand_filter:
        query = query.filter_by(brand_id=brand_filter)

    if sort_by == 'stock':
        query = query.order_by(Product.stock_qty.asc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'brand':
        query = query.join(Brand).order_by(Brand.name.asc(), Product.name.asc())

    products = query.all()
    brands = Brand.query.order_by(Brand.name.asc()).all()

    return render_template('admin/stock.html', products=products, brands=brands,
                           sort_by=sort_by, brand_filter=brand_filter)


@admin_bp.route('/stock/adjust', methods=['POST'])
@admin_required
def stock_adjust():
    product_id = request.form.get('product_id', type=int)
    adjustment = request.form.get('adjustment', type=int)

    if product_id is None or adjustment is None:
        flash('Geçersiz istek.', 'danger')
        return redirect(url_for('admin.stock'))

    product = Product.query.get_or_404(product_id)
    was_out_of_stock = product.stock_qty == 0
    product.stock_qty += adjustment
    if product.stock_qty < 0:
        product.stock_qty = 0

    db.session.commit()

    if was_out_of_stock and product.stock_qty > 0:
        notifications = StockNotification.query.filter_by(product_id=product.id).all()
        if notifications:
            product_url = url_for('shop.product_detail', product_id=product.id, _external=True)
            for notif in notifications:
                try:
                    send_stock_notification(
                        email=notif.email,
                        product_name=product.name,
                        product_url=product_url,
                    )
                except Exception:
                    pass
            StockNotification.query.filter_by(product_id=product.id).delete()
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
        flash('Bu ürün için zaten bir kampanya var.', 'warning')
        return redirect(url_for('admin.campaigns'))

    new_campaign = DiscountRule(product_id=product_id, percent=percent, name=name, active=True)
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
        flash('Bu sipariş iptal onayı beklemiyor.', 'warning')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    order.status = 'CANCELED'
    order.updated_at = datetime.utcnow()

    for item in order.items:
        product = db.session.get(Product, item.product_id)
        if product:
            product.stock_qty += item.quantity

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
        product = db.session.get(Product, item.product_id)
        if product:
            product.stock_qty += item.quantity

    db.session.commit()
    flash(f'Sipariş #{order.id} iadesi tamamlandı.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/site-images')
@admin_required
def site_images():
    images = SiteImage.query.order_by(SiteImage.key.asc()).all()
    return render_template('admin/site_images.html', images=images)


@admin_bp.route('/site-images/<int:image_id>/upload', methods=['POST'])
@admin_required
def site_image_upload(image_id):
    site_img = SiteImage.query.get_or_404(image_id)

    if 'image' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('admin.site_images'))

    file = request.files['image']
    if not file or not file.filename:
        flash('Geçerli bir dosya seçin.', 'warning')
        return redirect(url_for('admin.site_images'))

    if site_img.image_path:
        delete_product_image(site_img.image_path, current_app.config['UPLOAD_FOLDER'])

    new_path = save_banner_image(file, current_app.config['UPLOAD_FOLDER'])
    if new_path:
        site_img.image_path = new_path
        site_img.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'"{site_img.label}" görseli güncellendi.', 'success')
    else:
        flash('Görsel yüklenirken hata oluştu.', 'danger')

    return redirect(url_for('admin.site_images'))


@admin_bp.route('/site-images/<int:image_id>/delete', methods=['POST'])
@admin_required
def site_image_delete(image_id):
    site_img = SiteImage.query.get_or_404(image_id)

    if site_img.image_path:
        delete_product_image(site_img.image_path, current_app.config['UPLOAD_FOLDER'])
        site_img.image_path = None
        site_img.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'"{site_img.label}" görseli silindi.', 'success')
    else:
        flash('Silinecek görsel bulunamadı.', 'warning')

    return redirect(url_for('admin.site_images'))


@admin_bp.route('/newsletter')
@admin_required
def newsletter():
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/newsletter.html', subscribers=subscribers, coupons=coupons)
