from app import app, db
from flask_migrate import stamp
from models import Brand

with app.app_context():
    db.create_all()
    stamp()
    if Brand.query.count() == 0:
        from seed import seed
        seed()
