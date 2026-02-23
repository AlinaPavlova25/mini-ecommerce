from models import Product, db

def check_stock_availability(product_id, quantity):
    product = Product.query.get(product_id)
    if not product:
        return False, "Ürün bulunamadı"
    
    if not product.is_active:
        return False, "Ürün aktif değil"
    
    if product.stock_qty < quantity:
        return False, f"Yetersiz stok. Mevcut: {product.stock_qty}"
    
    return True, "OK"

def decrease_stock(product_id, quantity):
    product = Product.query.get(product_id)
    if product:
        product.stock_qty -= quantity
        db.session.commit()

def increase_stock(product_id, quantity):
    product = Product.query.get(product_id)
    if product:
        product.stock_qty += quantity
        db.session.commit()

def restore_order_stock(order):
    for item in order.items:
        increase_stock(item.product_id, item.quantity)
