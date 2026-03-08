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
            print("drop_all basliyor...")
            db.drop_all()
            print("drop_all tamam, create_all basliyor...")
            db.create_all()
            print("create_all tamam, stamp basliyor...")
            try:
                stamp()
            except Exception as se:
                print(f"stamp hatasi (devam ediliyor): {se}")
            print("seed import ediliyor...")
            try:
                from seed import seed
                print("seed import tamam, seed() cagriliyor...")
                seed()
                print("seed() tamamlandi.")
            except Exception as se:
                print(f"SEED HATASI: {se}")
                traceback.print_exc()
                raise
        else:
            print("Seed atlandi, mevcut veri korunuyor.")
    except Exception as e:
        print(f"HATA: {e}")
        traceback.print_exc()
        raise
