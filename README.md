# LuxWatch — Lüks Saat E-Ticaret Platformu

Flask tabanlı lüks saat satış ve yönetim sistemi.

## Hızlı Başlangıç

```bash
cd mini-ecommerce
venv\Scripts\activate
python app.py
```

Tarayıcıda aç: http://127.0.0.1:5000

### Test Hesapları

| Rol   | Email             | Şifre    |
|-------|-------------------|----------|
| Admin | admin@example.com | admin123 |
| User  | user@example.com  | user123  |

---

## Özellikler

### Kullanıcı Tarafı
- Ürün listeleme, arama ve filtreleme (marka, cinsiyet, fiyat)
- Çoklu ürün fotoğrafı galerisi + video oynatıcı
- Sepet sistemi
- Checkout (81 il)
- Sipariş takibi ve iptal yönetimi
- Adres defteri ve profil yönetimi
- Favori listesi
- Çift dil desteği (TR / EN)
- Newsletter aboneliği

### Admin Tarafı
- Dashboard (sipariş ve stok özeti)
- Ürün yönetimi (CRUD, çoklu görsel, video)
- Marka yönetimi
- Stok yönetimi
- Kampanya / indirim kodu yönetimi
- Sipariş yönetimi ve durum güncelleme
- Site görselleri yönetimi (hero banner, vs.)
- Newsletter yönetimi

---

## Teknolojiler

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Database:** SQLite
- **Frontend:** Jinja2, Bootstrap 5, Custom CSS
- **Görsel İşleme:** Pillow (pillow-avif-plugin dahil)

---

## Proje Yapısı

```
mini-ecommerce/
├── app.py                  # Ana uygulama ve konfigürasyon
├── models.py               # Veritabanı modelleri
├── seed.py                 # Veritabanı seed scripti
├── routes/
│   ├── admin.py            # Admin paneli route'ları
│   ├── auth.py             # Kimlik doğrulama
│   ├── profile.py          # Profil route'ları
│   └── shop.py             # E-ticaret route'ları
├── templates/              # HTML template'leri
├── static/
│   ├── css/
│   │   ├── custom.css
│   │   └── admin.css
│   └── uploads/            # Yüklenen görseller (gitignore'da)
├── utils/
│   ├── cart.py
│   ├── i18n.py
│   ├── stock.py
│   └── upload.py
└── translations/
    ├── tr.json
    └── en.json
```

---

## Veritabanı

Veritabanı ilk çalıştırmada otomatik oluşturulur. Sıfırdan oluşturmak için:

```bash
python seed.py
```

---

## Sipariş Durumları

```
PAID → PREPARING → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
            ↓ (iptal)     ↓ (admin onayı ile)
        CANCELED    CANCEL_REQUESTED → RETURN_ARRIVED → CANCELED
```

---

## Kurulum

```bash
pip install -r requirements.txt
```

---

## Sorun Giderme

**Port 5000 kullanımda:**
```bash
netstat -ano | findstr :5000
taskkill /F /PID <pid>
```

**Veritabanı hatası:**
```bash
python seed.py
```

**Import hatası — virtual environment aktif mi?**
```bash
venv\Scripts\activate
pip install -r requirements.txt
```
