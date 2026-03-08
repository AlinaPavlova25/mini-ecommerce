import traceback
from app import app, db
from flask_migrate import stamp
from models import Brand, Product

with app.app_context():
    try:
        db.create_all()
        try:
            stamp()
        except Exception:
            pass
        print("DB tablolari olusturuldu.")
        needs_seed = (
            Brand.query.count() == 0 or
            Product.query.count() == 0
        )
        print(f"needs_seed: {needs_seed}")
        if needs_seed:
            db.drop_all()
            db.create_all()
            try:
                stamp()
            except Exception:
                pass
            from seed import seed
            seed()
        else:
            print("Seed atlandi, mevcut veri korunuyor.")
    except Exception as e:
        print(f"HATA: {e}")
        traceback.print_exc()
        raise
