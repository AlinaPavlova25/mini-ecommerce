from flask import current_app, render_template_string
from flask_mail import Message
from threading import Thread


def _send_async(app, mail, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, html_body, text_body=None):
    from app import mail
    msg = Message(subject=subject, recipients=recipients)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    app = current_app._get_current_object()
    Thread(target=_send_async, args=(app, mail, msg), daemon=True).start()


ORDER_CONFIRM_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0f0f; color: #f0ead8; margin: 0; padding: 0; }
  .wrap { max-width: 600px; margin: 0 auto; padding: 2rem; }
  .header { text-align: center; padding: 2rem 0 1.5rem; border-bottom: 1px solid rgba(198,167,94,0.25); }
  .logo { font-size: 1.8rem; font-weight: 700; letter-spacing: 0.08em; color: #c6a75e; }
  .tagline { font-size: 0.6rem; letter-spacing: 0.3em; text-transform: uppercase; color: #a89880; margin-top: 4px; }
  h2 { color: #c6a75e; font-size: 1.2rem; margin: 2rem 0 0.5rem; font-weight: 400; letter-spacing: 0.05em; }
  p { color: #a89880; font-size: 0.9rem; line-height: 1.8; margin: 0.5rem 0; }
  .order-box { background: #1a1a1a; border: 1px solid rgba(198,167,94,0.2); border-radius: 4px; padding: 1.5rem; margin: 1.5rem 0; }
  .order-id { font-size: 1.4rem; color: #c6a75e; font-weight: 700; letter-spacing: 0.1em; }
  table { width: 100%; border-collapse: collapse; margin: 1.25rem 0; }
  th { font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase; color: #6b5d4f; border-bottom: 1px solid rgba(198,167,94,0.15); padding: 0.5rem 0; text-align: left; }
  td { font-size: 0.85rem; color: #f0ead8; padding: 0.65rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
  td.price { text-align: right; color: #c6a75e; }
  .total-row td { border-top: 1px solid rgba(198,167,94,0.3); font-size: 1rem; color: #c6a75e; font-weight: 600; padding-top: 1rem; }
  .footer { text-align: center; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(198,167,94,0.15); font-size: 0.75rem; color: #6b5d4f; line-height: 2; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">LuxWatch</div>
    <div class="tagline">Horologerie de Luxe</div>
  </div>

  <h2>Siparişiniz Alındı</h2>
  <p>Merhaba {{ user_name }},</p>
  <p>Siparişiniz başarıyla alındı ve hazırlanmaya başlandı. Aşağıda sipariş özetinizi bulabilirsiniz.</p>

  <div class="order-box">
    <p style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:#6b5d4f;margin-bottom:0.3rem;">Sipariş No</p>
    <div class="order-id">#{{ order_id }}</div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Ürün</th>
        <th style="text-align:center;">Adet</th>
        <th style="text-align:right;">Fiyat</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.name }}</td>
        <td style="text-align:center;">{{ item.quantity }}</td>
        <td class="price">{{ "%.2f"|format(item.total) }} TL</td>
      </tr>
      {% endfor %}
      {% if coupon_discount and coupon_discount > 0 %}
      <tr>
        <td colspan="2" style="color:#a89880;">Kupon İndirimi ({{ coupon_code }})</td>
        <td class="price" style="color:#4caf50;">-{{ "%.2f"|format(coupon_discount) }} TL</td>
      </tr>
      {% endif %}
    </tbody>
    <tfoot>
      <tr class="total-row">
        <td colspan="2">Toplam</td>
        <td class="price">{{ "%.2f"|format(total_amount) }} TL</td>
      </tr>
    </tfoot>
  </table>

  <h2>Teslimat Adresi</h2>
  <p style="white-space:pre-line;">{{ shipping_address }}</p>

  {% if installment_count and installment_count > 1 %}
  <p style="margin-top:1rem;"><span style="color:#c6a75e;">{{ installment_count }} taksit</span> seçildi.</p>
  {% endif %}

  <div class="footer">
    <p>LuxWatch &mdash; Seçkin Saatler</p>
    <p>Bu e-posta otomatik olarak oluşturulmuştur, lütfen yanıtlamayın.</p>
  </div>
</div>
</body>
</html>
"""

RESET_PASSWORD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0f0f; color: #f0ead8; margin: 0; padding: 0; }
  .wrap { max-width: 560px; margin: 0 auto; padding: 2rem; }
  .header { text-align: center; padding: 2rem 0 1.5rem; border-bottom: 1px solid rgba(198,167,94,0.25); }
  .logo { font-size: 1.8rem; font-weight: 700; letter-spacing: 0.08em; color: #c6a75e; }
  .tagline { font-size: 0.6rem; letter-spacing: 0.3em; text-transform: uppercase; color: #a89880; margin-top: 4px; }
  h2 { color: #c6a75e; font-size: 1.2rem; margin: 2rem 0 0.5rem; font-weight: 400; letter-spacing: 0.05em; }
  p { color: #a89880; font-size: 0.9rem; line-height: 1.8; margin: 0.5rem 0; }
  .btn { display: inline-block; margin: 1.5rem 0; padding: 0.85rem 2.5rem; background: #c6a75e; color: #0f0f0f; text-decoration: none; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; border-radius: 2px; }
  .link-note { font-size: 0.75rem; color: #6b5d4f; word-break: break-all; }
  .footer { text-align: center; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(198,167,94,0.15); font-size: 0.75rem; color: #6b5d4f; line-height: 2; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">LuxWatch</div>
    <div class="tagline">Horologerie de Luxe</div>
  </div>

  <h2>Şifre Sıfırlama</h2>
  <p>Merhaba,</p>
  <p>LuxWatch hesabınız için şifre sıfırlama talebinde bulunuldu. Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz.</p>
  <p style="text-align:center;">
    <a href="{{ reset_url }}" class="btn">Şifremi Sıfırla</a>
  </p>
  <p class="link-note">Buton çalışmıyorsa aşağıdaki linki tarayıcınıza kopyalayın:<br>{{ reset_url }}</p>
  <p style="margin-top:1.5rem;">Bu link <strong style="color:#f0ead8;">1 saat</strong> geçerlidir. Eğer bu talebi siz yapmadıysanız bu e-postayı dikkate almayın.</p>

  <div class="footer">
    <p>LuxWatch &mdash; Seçkin Saatler</p>
    <p>Bu e-posta otomatik olarak oluşturulmuştur, lütfen yanıtlamayın.</p>
  </div>
</div>
</body>
</html>
"""


def send_order_confirmation(user_email, user_name, order):
    items = []
    for oi in order.items:
        unit = float(oi.unit_price_at_purchase)
        if oi.discount_percent_at_purchase:
            unit = unit * (1 - float(oi.discount_percent_at_purchase) / 100)
        items.append({
            'name': oi.product.name,
            'quantity': oi.quantity,
            'total': unit * oi.quantity,
        })

    html = render_template_string(
        ORDER_CONFIRM_HTML,
        user_name=user_name,
        order_id=order.id,
        items=items,
        total_amount=float(order.total_amount),
        shipping_address=order.shipping_address,
        coupon_code=order.coupon_code,
        coupon_discount=float(order.coupon_discount) if order.coupon_discount else 0,
        installment_count=order.installment_count,
    )
    send_email(
        subject=f'LuxWatch — Sipariş #{order.id} Onayı',
        recipients=[user_email],
        html_body=html,
    )


def send_password_reset(user_email, reset_url):
    html = render_template_string(RESET_PASSWORD_HTML, reset_url=reset_url)
    send_email(
        subject='LuxWatch — Şifre Sıfırlama',
        recipients=[user_email],
        html_body=html,
    )


NEWSLETTER_COUPON_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0f0f; color: #f0ead8; margin: 0; padding: 0; }
  .wrap { max-width: 560px; margin: 0 auto; padding: 2rem; }
  .header { text-align: center; padding: 2rem 0 1.5rem; border-bottom: 1px solid rgba(198,167,94,0.25); }
  .logo { font-size: 1.8rem; font-weight: 700; letter-spacing: 0.08em; color: #c6a75e; }
  .tagline { font-size: 0.6rem; letter-spacing: 0.3em; text-transform: uppercase; color: #a89880; margin-top: 4px; }
  h2 { color: #c6a75e; font-size: 1.2rem; margin: 2rem 0 0.5rem; font-weight: 400; letter-spacing: 0.05em; }
  p { color: #a89880; font-size: 0.9rem; line-height: 1.8; margin: 0.5rem 0; }
  .coupon-box { background: #1a1a1a; border: 1px solid rgba(198,167,94,0.4); padding: 1.5rem; margin: 1.5rem 0; text-align: center; }
  .coupon-label { font-size: 0.6rem; letter-spacing: 0.25em; text-transform: uppercase; color: #6b5d4f; margin-bottom: 0.5rem; }
  .coupon-code { font-size: 1.8rem; font-family: monospace; letter-spacing: 0.25em; color: #c6a75e; font-weight: 700; }
  .coupon-pct { font-size: 0.8rem; color: #a89880; margin-top: 0.5rem; }
  .footer { text-align: center; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(198,167,94,0.15); font-size: 0.75rem; color: #6b5d4f; line-height: 2; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">LuxWatch</div>
    <div class="tagline">Horologerie de Luxe</div>
  </div>
  <h2>Hoş Geldiniz</h2>
  <p>LuxWatch bültenine abone olduğunuz için teşekkürler. İlk siparişinizde kullanabileceğiniz özel indirim kodunuz aşağıdadır.</p>
  <div class="coupon-box">
    <div class="coupon-label">İndirim Kodunuz</div>
    <div class="coupon-code">{{ coupon_code }}</div>
    <div class="coupon-pct">%{{ discount_percent }} indirim · Tek kullanımlık</div>
  </div>
  <p>Bu kodu sepet sayfasında "Kupon Kodu" alanına girerek indiriminizi uygulayabilirsiniz.</p>
  <p style="font-size:0.8rem; color:#6b5d4f;">Kupon yalnızca bu e-posta adresine kayıtlı hesabınızla kullanılabilir.</p>
  <div class="footer">
    <p>LuxWatch &mdash; Seçkin Saatler</p>
    <p>Bu e-posta otomatik olarak oluşturulmuştur, lütfen yanıtlamayın.</p>
  </div>
</div>
</body>
</html>
"""


def send_newsletter_coupon(email, coupon_code, discount_percent=15):
    html = render_template_string(
        NEWSLETTER_COUPON_HTML,
        coupon_code=coupon_code,
        discount_percent=discount_percent,
    )
    send_email(
        subject='LuxWatch — %{} İndirim Kodunuz'.format(discount_percent),
        recipients=[email],
        html_body=html,
    )


WELCOME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #0f0f0f; color: #f0ead8; margin: 0; padding: 0; }
  .wrap { max-width: 560px; margin: 0 auto; padding: 2rem; }
  .header { text-align: center; padding: 2rem 0 1.5rem; border-bottom: 1px solid rgba(198,167,94,0.25); }
  .logo { font-size: 1.8rem; font-weight: 700; letter-spacing: 0.08em; color: #c6a75e; }
  .tagline { font-size: 0.6rem; letter-spacing: 0.3em; text-transform: uppercase; color: #a89880; margin-top: 4px; }
  h2 { color: #c6a75e; font-size: 1.2rem; margin: 2rem 0 0.5rem; font-weight: 400; letter-spacing: 0.05em; }
  p { color: #a89880; font-size: 0.9rem; line-height: 1.8; margin: 0.5rem 0; }
  .btn { display: inline-block; margin: 1.5rem 0; padding: 0.85rem 2.5rem; background: #c6a75e; color: #0f0f0f; text-decoration: none; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; border-radius: 2px; }
  .divider { width: 40px; height: 1px; background: rgba(198,167,94,0.4); margin: 1rem auto; }
  .footer { text-align: center; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(198,167,94,0.15); font-size: 0.75rem; color: #6b5d4f; line-height: 2; }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">LuxWatch</div>
    <div class="tagline">Horologerie de Luxe</div>
  </div>
  <h2>Hoş Geldiniz, {{ full_name }}</h2>
  <div class="divider"></div>
  <p>LuxWatch ailesine katıldığınız için teşekkür ederiz. Hesabınız başarıyla oluşturuldu.</p>
  <p>Dünyanın en prestijli saat markalarından oluşan koleksiyonumuzu keşfetmeye başlayabilirsiniz.</p>
  <p style="text-align: center;">
    <a href="{{ shop_url }}" class="btn">Koleksiyonu Keşfet</a>
  </p>
  <p style="font-size: 0.8rem; color: #6b5d4f;">Herhangi bir sorunuz olursa bize ulaşmaktan çekinmeyin.</p>
  <div class="footer">
    <p>LuxWatch &mdash; Seçkin Saatler</p>
    <p>Bu e-posta otomatik olarak oluşturulmuştur, lütfen yanıtlamayın.</p>
  </div>
</div>
</body>
</html>
"""


def send_welcome_email(user_email, full_name, shop_url):
    html = render_template_string(WELCOME_HTML, full_name=full_name, shop_url=shop_url)
    send_email(
        subject='LuxWatch\'a Hoş Geldiniz',
        recipients=[user_email],
        html_body=html,
    )
