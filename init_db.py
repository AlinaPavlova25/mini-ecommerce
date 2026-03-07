from app import app, db
from flask_migrate import stamp
from models import Brand, Product, ProductImage

with app.app_context():
    db.create_all()
    stamp()
    needs_seed = (
        Brand.query.count() == 0 or
        Product.query.filter(Product.image_path == None).count() > 0 or
        ProductImage.query.count() == 0
    )
    if needs_seed:
        db.drop_all()
        db.create_all()
        stamp()
        from seed import seed
        seed()
