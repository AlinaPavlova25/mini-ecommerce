# LuxWatch — Lüks Saat E-Ticaret Platformu

Flask tabanlı lüks saat satış ve yönetim sistemi.

**Canlı Demo:** https://lux-watch.up.railway.app

---

## Hızlı Başlangıç

```bash
cd mini-ecommerce
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

Tarayıcıda aç: http://127.0.0.1:5000

### Test Hesapları

| Rol   | Email                | Şifre    |
|-------|----------------------|----------|
| Admin | admin@luxwatch.com   | admin123 |

---

## Özellikler

### Kullanıcı Tarafı
- Ürün listeleme, arama (ürün adına göre) ve filtreleme (marka, cinsiyet, fiyat aralığı)
- Fiyat filtresi indirimli fiyatı baz alır
- Çoklu ürün fotoğrafı galerisi + video oynatıcı
- Sepet sistemi
- Checkout (81 il, taksit seçeneği — backend faiz hesabı dahil)
- Sipariş takibi ve iptal / iade yönetimi
- Adres defteri (ekleme, düzenleme, silme)
- Profil yönetimi
- Favori listesi
- Çift dil desteği (TR / EN)
- Newsletter aboneliği — kupon yoksa profil/kuponlarım sekmesinden de abone olunabilir
- Hakkımızda ve SSS/Garanti sayfaları
- WhatsApp iletişim yönlendirmesi
- Karanlık mod desteği

### Admin Tarafı
- Dashboard (sipariş ve stok özeti)
- Ürün yönetimi (CRUD, çoklu görsel, video, komple silme)
- Kampanya yönetimi (arama + marka/cinsiyet/alfabe filtrelemeli ürün seçici)
- Marka yönetimi
- Stok yönetimi
- İndirim / kupon kodu yönetimi
- Sipariş yönetimi ve durum güncelleme
- Site görselleri yönetimi (hero banner, vb.)
- Newsletter yönetimi

---

## Teknolojiler

- **Backend:** Flask, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-Mail, Flask-Limiter
- **Database:** PostgreSQL (production) / SQLite (local geliştirme)
- **Frontend:** Jinja2, Custom CSS (Bootstrap bağımlılığı yok)
- **Görsel İşleme:** Pillow
- **Güvenlik:** python-dotenv (.env), rate limiting, rol bazlı yetkilendirme
- **Deploy:** Railway (gunicorn)

---

## Proje Yapısı

```
mini-ecommerce/
├── app.py                  # Ana uygulama ve konfigürasyon
├── models.py               # Veritabanı modelleri
├── seed.py                 # Veritabanı seed scripti (görsel yolları dahil)
├── init_db.py              # Railway başlangıç scripti
├── Procfile                # Railway/gunicorn başlatma
├── railway.json            # Railway deploy konfigürasyonu
├── .env                    # Ortam değişkenleri (gitignore'da)
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
│   └── uploads/            # Ürün ve site görselleri
├── utils/
│   ├── cart.py
│   ├── i18n.py
│   ├── mail.py
│   ├── stock.py
│   └── upload.py
├── migrations/             # Flask-Migrate migration dosyaları
└── translations/
    ├── tr.json
    └── en.json
```

---

## Ortam Değişkenleri

`.env` dosyası oluşturun:

```
SECRET_KEY=gizli-anahtar-buraya
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@luxwatch.com
```

Railway'de **Variables** sekmesinden `SECRET_KEY` ve `DATABASE_URL` ekleyin.

---

## Veritabanı

### Local Geliştirme (SQLite)

```bash
python seed.py
```

Migration uygulamak için:

```bash
flask db upgrade
```

### Production (PostgreSQL)

`DATABASE_URL` environment variable otomatik olarak okunur. `init_db.py` başlangıçta tabloları oluşturur; Brand veya Product tablosu boşsa seed çalıştırır, doluysa mevcut veriyi korur.

---

## Railway Deploy

1. GitHub reposunu Railway'e bağlayın
2. Railway dashboard'dan **PostgreSQL** servisi ekleyin
3. Web servisinin Variables sekmesine `DATABASE_URL` (PostgreSQL public URL) ve `SECRET_KEY` ekleyin
4. Deploy otomatik başlar — tablolar oluşturulur, ilk kez seed çalışır
5. Sonraki deploy'larda tüm veriler (siparişler, kullanıcılar, ayarlar) korunur

---

## Sipariş Durumları

```
PAID → PREPARING → SHIPPED → OUT_FOR_DELIVERY → DELIVERED
            ↓ (iptal)
        CANCELED
        CANCEL_REQUESTED → RETURN_ARRIVED → CANCELED
```

---

## Rol Sistemi

| Rol       | Yetki                 |
|-----------|-----------------------|
| user      | Standart müşteri      |
| moderator | Admin paneline erişim |
| admin     | Tam yetki             |

---

## Sorun Giderme

**Port 5000 kullanımda:**
```bash
netstat -ano | findstr :5000
taskkill /F /PID <pid>
```

**Veritabanı hatası:**
```bash
flask db upgrade
python seed.py
```

**Import hatası — virtual environment aktif mi?**
```bash
venv\Scripts\activate
pip install -r requirements.txt
```
