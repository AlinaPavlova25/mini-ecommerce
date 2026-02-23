from models import Product, DiscountRule

def get_cart_items(cart_dict):
    items = []
    for product_id_str, quantity in cart_dict.items():
        product = Product.query.get(int(product_id_str))
        if product and product.is_active:
            discount = product.active_discount
            discount_percent = discount.percent if discount else 0
            
            items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': float(product.price),
                'discounted_price': float(product.discounted_price),
                'discount_percent': discount_percent,
                'subtotal': float(product.discounted_price) * quantity
            })
    return items

def calculate_cart_total(cart_items):
    return sum(item['subtotal'] for item in cart_items)

def get_cart_count(cart_dict):
    return sum(cart_dict.values())
