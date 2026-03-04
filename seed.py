import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Brand, Product, User, SiteImage
from werkzeug.security import generate_password_hash

BRANDS = [
    {
        'name': 'Rolex',
        'slug': 'rolex',
        'country': 'İsviçre',
        'founded_year': 1905,
        'sort_order': 1,
        'description': '1905 yılında Cenevre\'de kurulan Rolex, dünyanın en prestijli saat markasıdır.',
        'description_en': 'Founded in Geneva in 1905, Rolex is the world\'s most prestigious watch brand.',
    },
    {
        'name': 'Patek Philippe',
        'slug': 'patek-philippe',
        'country': 'İsviçre',
        'founded_year': 1839,
        'sort_order': 2,
        'description': '1839\'dan bu yana üretilen her Patek Philippe saati, saat yapım sanatının zirvesini temsil eder.',
        'description_en': 'Every Patek Philippe watch made since 1839 represents the pinnacle of watchmaking art.',
    },
    {
        'name': 'Cartier',
        'slug': 'cartier',
        'country': 'Fransa',
        'founded_year': 1847,
        'sort_order': 3,
        'description': 'Cartier, 1847\'den bu yana mücevher ve saatçilikte zarafet ile lüksün simgesidir.',
        'description_en': 'Cartier has been the symbol of elegance and luxury in jewelry and watchmaking since 1847.',
    },
    {
        'name': 'Grand Seiko',
        'slug': 'grand-seiko',
        'country': 'Japonya',
        'founded_year': 1960,
        'sort_order': 4,
        'description': 'Japonya\'nın zanaatkarlık geleneğini modern teknolojiyle harmanlayan Grand Seiko, eşsiz bir hassasiyet sunar.',
        'description_en': 'Grand Seiko blends Japan\'s craftsmanship tradition with modern technology for unparalleled precision.',
    },
    {
        'name': 'Omega',
        'slug': 'omega',
        'country': 'İsviçre',
        'founded_year': 1848,
        'sort_order': 5,
        'description': 'NASA\'nın resmi saati ve James Bond\'un tercihi olan Omega, 1848\'den bu yana mükemmeliyeti temsil eder.',
        'description_en': 'Official watch of NASA and James Bond\'s choice, Omega has represented excellence since 1848.',
    },
    {
        'name': 'TAG Heuer',
        'slug': 'tag-heuer',
        'country': 'İsviçre',
        'founded_year': 1860,
        'sort_order': 6,
        'description': '1860\'dan bu yana spor ve hassasiyetin simgesi olan TAG Heuer, kronograf saatlerin öncüsüdür.',
        'description_en': 'A symbol of sport and precision since 1860, TAG Heuer is the pioneer of chronograph watches.',
    },
    {
        'name': 'Breitling',
        'slug': 'breitling',
        'country': 'İsviçre',
        'founded_year': 1884,
        'sort_order': 7,
        'description': 'Havacılar ve deniz adamları için tasarlanan Breitling saatleri, 1884\'ten bu yana güvenilirliğin sembolüdür.',
        'description_en': 'Designed for aviators and seafarers, Breitling watches have been a symbol of reliability since 1884.',
    },
]

PRODUCTS = [
    # ROLEX
    {'brand': 'rolex', 'name': 'Rolex Submariner Date', 'name_en': 'Rolex Submariner Date',
     'description': 'Submariner Date, dünyanın en tanınan dalış saatidir. Çelik kasa ve siyah seramik bezel ile donatılmıştır.',
     'description_en': 'The Submariner Date is the world\'s most recognized dive watch, featuring a steel case and black ceramic bezel.',
     'gender': 'erkek', 'reference_number': '126610LN', 'case_material': 'Oyster Çelik',
     'case_diameter': '41mm', 'movement': 'Otomatik (Kalibr 3235)', 'water_resistance': '300m',
     'price': 185000, 'stock_qty': 5, 'is_featured': True},

    {'brand': 'rolex', 'name': 'Rolex Datejust 36', 'name_en': 'Rolex Datejust 36',
     'description': 'Datejust, 1945\'ten bu yana zamanın testi geçmiş klasik bir Rolex modelidir.',
     'description_en': 'The Datejust has stood the test of time as a classic Rolex model since 1945.',
     'gender': 'unisex', 'reference_number': '126200', 'case_material': 'Oyster Çelik',
     'case_diameter': '36mm', 'movement': 'Otomatik (Kalibr 3235)', 'water_resistance': '100m',
     'price': 145000, 'stock_qty': 7, 'is_featured': True},

    {'brand': 'rolex', 'name': 'Rolex Day-Date 40', 'name_en': 'Rolex Day-Date 40',
     'description': 'Presidentin saati olarak bilinen Day-Date, 18k altın kasa ile üretilir.',
     'description_en': 'Known as the President\'s watch, the Day-Date is crafted in 18k gold.',
     'gender': 'erkek', 'reference_number': '228235', 'case_material': '18k Everose Altın',
     'case_diameter': '40mm', 'movement': 'Otomatik (Kalibr 3255)', 'water_resistance': '100m',
     'price': 680000, 'stock_qty': 3, 'is_featured': False},

    {'brand': 'rolex', 'name': 'Rolex Lady-Datejust 28', 'name_en': 'Rolex Lady-Datejust 28',
     'description': 'Lady-Datejust, Rolex\'in kadınlara özel tasarlanmış zarif koleksiyon saatidir.',
     'description_en': 'The Lady-Datejust is Rolex\'s elegant collection watch designed exclusively for women.',
     'gender': 'kadin', 'reference_number': '279138RBR', 'case_material': 'Oyster Çelik',
     'case_diameter': '28mm', 'movement': 'Otomatik (Kalibr 2236)', 'water_resistance': '100m',
     'price': 178000, 'stock_qty': 6, 'is_featured': True},

    {'brand': 'rolex', 'name': 'Rolex GMT-Master II', 'name_en': 'Rolex GMT-Master II',
     'description': 'Aynı anda iki farklı saat dilimini gösteren GMT-Master II, gezginlerin vazgeçilmezidir.',
     'description_en': 'The GMT-Master II displays two time zones simultaneously, making it a traveler\'s essential.',
     'gender': 'erkek', 'reference_number': '126710BLNR', 'case_material': 'Oyster Çelik',
     'case_diameter': '40mm', 'movement': 'Otomatik (Kalibr 3285)', 'water_resistance': '100m',
     'price': 220000, 'stock_qty': 4, 'is_featured': True},

    # PATEK PHILIPPE
    {'brand': 'patek-philippe', 'name': 'Patek Philippe Nautilus', 'name_en': 'Patek Philippe Nautilus',
     'description': 'Gerald Genta tasarımlı Nautilus, spor-lüks saatlerin en ikonik örneğidir.',
     'description_en': 'Designed by Gerald Genta, the Nautilus is the most iconic example of sport-luxury watches.',
     'gender': 'erkek', 'reference_number': '5711/1A-014', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '40mm', 'movement': 'Otomatik (Kalibr 26-330 S C)', 'water_resistance': '120m',
     'price': 1450000, 'stock_qty': 2, 'is_featured': True},

    {'brand': 'patek-philippe', 'name': 'Patek Philippe Calatrava', 'name_en': 'Patek Philippe Calatrava',
     'description': 'Calatrava, saat tasarımındaki saflığın ve zarafetin en saf ifadesidir.',
     'description_en': 'The Calatrava is the purest expression of purity and elegance in watch design.',
     'gender': 'erkek', 'reference_number': '5196R-001', 'case_material': '18k Rose Altın',
     'case_diameter': '37mm', 'movement': 'Manuel Kurmalı (Kalibr 215 PS)', 'water_resistance': '30m',
     'price': 890000, 'stock_qty': 3, 'is_featured': False},

    {'brand': 'patek-philippe', 'name': 'Patek Philippe Twenty~4', 'name_en': 'Patek Philippe Twenty~4',
     'description': 'Modern kadınlar için tasarlanan Twenty~4, her ortama uyum sağlayan zarif bir saat.',
     'description_en': 'Designed for modern women, the Twenty~4 is an elegant watch that adapts to any setting.',
     'gender': 'kadin', 'reference_number': '7300/1200A-011', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '36mm', 'movement': 'Otomatik (Kalibr 324 S C)', 'water_resistance': '30m',
     'price': 750000, 'stock_qty': 4, 'is_featured': True},

    {'brand': 'patek-philippe', 'name': 'Patek Philippe Aquanaut', 'name_en': 'Patek Philippe Aquanaut',
     'description': 'Aquanaut, Patek Philippe\'nin Nautilus\'a rakip sportif ve çağdaş koleksiyonudur.',
     'description_en': 'The Aquanaut is Patek Philippe\'s sporty and contemporary collection rivaling the Nautilus.',
     'gender': 'erkek', 'reference_number': '5167A-001', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '40mm', 'movement': 'Otomatik (Kalibr 324 S C)', 'water_resistance': '120m',
     'price': 980000, 'stock_qty': 3, 'is_featured': False},

    # CARTIER
    {'brand': 'cartier', 'name': 'Cartier Santos', 'name_en': 'Cartier Santos',
     'description': 'Santos, uçuş sırasında bile okunabilen ilk bilek saatlerinden biridir. Efsanevi bir model.',
     'description_en': 'The Santos is one of the first wristwatches readable even during flight. A legendary model.',
     'gender': 'erkek', 'reference_number': 'WSSA0018', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '39.8mm', 'movement': 'Otomatik (Kalibr 1847 MC)', 'water_resistance': '100m',
     'price': 195000, 'stock_qty': 8, 'is_featured': True},

    {'brand': 'cartier', 'name': 'Cartier Tank Louis', 'name_en': 'Cartier Tank Louis',
     'description': 'Tank Louis Cartier, şık dikdörtgen formuyla zamanın ötesinde bir tasarım klasiğidir.',
     'description_en': 'The Tank Louis Cartier is a timeless design classic with its elegant rectangular form.',
     'gender': 'unisex', 'reference_number': 'WGTA0011', 'case_material': '18k Sarı Altın',
     'case_diameter': '33.7x25.5mm', 'movement': 'Manuel Kurmalı (Kalibr 430 MC)', 'water_resistance': '30m',
     'price': 420000, 'stock_qty': 5, 'is_featured': True},

    {'brand': 'cartier', 'name': 'Cartier Ballon Bleu', 'name_en': 'Cartier Ballon Bleu',
     'description': 'Yuvarlak kasası ve mavi çelik parçasıyla Ballon Bleu, kadınlar için romantik bir seçimdir.',
     'description_en': 'With its round case and blue steel component, the Ballon Bleu is a romantic choice for women.',
     'gender': 'kadin', 'reference_number': 'WSBB0049', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '33mm', 'movement': 'Otomatik (Kalibr 076)', 'water_resistance': '30m',
     'price': 145000, 'stock_qty': 9, 'is_featured': True},

    {'brand': 'cartier', 'name': 'Cartier Panthère de Cartier', 'name_en': 'Cartier Panthère de Cartier',
     'description': 'Panthère, Cartier\'nin efsanevi pars motifinden ilham alan ikonik kadın saatidir.',
     'description_en': 'The Panthère is an iconic women\'s watch inspired by Cartier\'s legendary panther motif.',
     'gender': 'kadin', 'reference_number': 'WJPN0019', 'case_material': '18k Sarı Altın',
     'case_diameter': '27mm', 'movement': 'Kuvars', 'water_resistance': '30m',
     'price': 680000, 'stock_qty': 4, 'is_featured': False},

    # GRAND SEIKO
    {'brand': 'grand-seiko', 'name': 'Grand Seiko Snowflake', 'name_en': 'Grand Seiko Snowflake',
     'description': 'Shinshū\'nun karlı manzarasından ilham alan kadranıyla Snowflake, Japon estetiğinin zirvesidir.',
     'description_en': 'Inspired by the snowy landscape of Shinshū, the Snowflake is the pinnacle of Japanese aesthetics.',
     'gender': 'erkek', 'reference_number': 'SBGA211', 'case_material': 'Titanyum',
     'case_diameter': '41mm', 'movement': 'Spring Drive (Kalibr 9R65)', 'water_resistance': '100m',
     'price': 285000, 'stock_qty': 6, 'is_featured': True},

    {'brand': 'grand-seiko', 'name': 'Grand Seiko Elegance', 'name_en': 'Grand Seiko Elegance',
     'description': 'Hi-Beat 36000 hareketi ile kusursuz hassasiyeti zarif bir tasarımla sunan koleksiyon.',
     'description_en': 'A collection offering flawless precision with Hi-Beat 36000 movement in an elegant design.',
     'gender': 'erkek', 'reference_number': 'SBGW231', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '37mm', 'movement': 'Manuel Kurmalı (Kalibr 9S64)', 'water_resistance': '30m',
     'price': 195000, 'stock_qty': 8, 'is_featured': False},

    {'brand': 'grand-seiko', 'name': 'Grand Seiko Birch', 'name_en': 'Grand Seiko Birch',
     'description': 'Huş ağacının zarif dokusundan ilham alan kadranıyla bu saat, doğanın estetiğini yansıtır.',
     'description_en': 'This watch reflects the beauty of nature with its dial inspired by the elegant texture of birch.',
     'gender': 'kadin', 'reference_number': 'STGK009', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '35.5mm', 'movement': 'Otomatik (Kalibr 9S45)', 'water_resistance': '30m',
     'price': 220000, 'stock_qty': 5, 'is_featured': True},

    {'brand': 'grand-seiko', 'name': 'Grand Seiko Spring Drive Chronograph', 'name_en': 'Grand Seiko Spring Drive Chronograph',
     'description': 'Spring Drive teknolojisini kronograf işleviyle birleştiren bu saat, teknik bir şaheserdir.',
     'description_en': 'Combining Spring Drive technology with chronograph function, this watch is a technical masterpiece.',
     'gender': 'erkek', 'reference_number': 'SBGC201', 'case_material': 'Titanyum',
     'case_diameter': '44.2mm', 'movement': 'Spring Drive (Kalibr 9R86)', 'water_resistance': '100m',
     'price': 380000, 'stock_qty': 3, 'is_featured': False},

    # OMEGA
    {'brand': 'omega', 'name': 'Omega Speedmaster Professional', 'name_en': 'Omega Speedmaster Professional',
     'description': 'Moonwatch olarak bilinen Speedmaster, 1969\'da Ay\'a ilk adımda astronotların bileğindeydi.',
     'description_en': 'Known as the Moonwatch, the Speedmaster was on astronauts\' wrists for the first steps on the Moon in 1969.',
     'gender': 'erkek', 'reference_number': '310.30.42.50.01.001', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '42mm', 'movement': 'Manuel Kurmalı (Kalibr 3861)', 'water_resistance': '50m',
     'price': 185000, 'stock_qty': 10, 'is_featured': True},

    {'brand': 'omega', 'name': 'Omega Seamaster Diver 300M', 'name_en': 'Omega Seamaster Diver 300M',
     'description': 'James Bond\'un tercih ettiği Seamaster, 300 metre su direnciyle profesyonel bir dalış saatidir.',
     'description_en': 'James Bond\'s choice, the Seamaster is a professional dive watch with 300m water resistance.',
     'gender': 'erkek', 'reference_number': '210.30.42.20.01.001', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '42mm', 'movement': 'Otomatik (Kalibr 8800)', 'water_resistance': '300m',
     'price': 148000, 'stock_qty': 12, 'is_featured': True},

    {'brand': 'omega', 'name': 'Omega De Ville Prestige', 'name_en': 'Omega De Ville Prestige',
     'description': 'De Ville Prestige, günlük şıklık arayanlar için ideal zarif bir saat.',
     'description_en': 'The De Ville Prestige is an ideal elegant watch for those seeking everyday sophistication.',
     'gender': 'kadin', 'reference_number': '428.15.36.60.02.002', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '36mm', 'movement': 'Otomatik (Kalibr 8800)', 'water_resistance': '30m',
     'price': 95000, 'stock_qty': 8, 'is_featured': False},

    {'brand': 'omega', 'name': 'Omega Constellation Co-Axial', 'name_en': 'Omega Constellation Co-Axial',
     'description': 'Constellation, Omega\'nın hassasiyet ve zarafeti birleştiren ikonik koleksiyonudur.',
     'description_en': 'The Constellation is Omega\'s iconic collection combining precision and elegance.',
     'gender': 'kadin', 'reference_number': '131.10.29.20.55.001', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '29mm', 'movement': 'Otomatik (Kalibr 8700)', 'water_resistance': '50m',
     'price': 108000, 'stock_qty': 7, 'is_featured': True},

    # TAG HEUER
    {'brand': 'tag-heuer', 'name': 'TAG Heuer Carrera Chronograph', 'name_en': 'TAG Heuer Carrera Chronograph',
     'description': 'Jack Heuer\'in 1963\'te yarış pistlerinden ilham alarak tasarladığı Carrera, spor saatçiliğinin simgesidir.',
     'description_en': 'Designed by Jack Heuer in 1963 inspired by racing circuits, the Carrera is the icon of sports watchmaking.',
     'gender': 'erkek', 'reference_number': 'CBN2A1B.FC6492', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '44mm', 'movement': 'Otomatik (Kalibr Heuer 02)', 'water_resistance': '100m',
     'price': 78000, 'stock_qty': 15, 'is_featured': True},

    {'brand': 'tag-heuer', 'name': 'TAG Heuer Monaco', 'name_en': 'TAG Heuer Monaco',
     'description': 'Steve McQueen\'in Le Mans filminde taktığı Monaco, dünyanın ilk su geçirmez kare kronografıdır.',
     'description_en': 'Worn by Steve McQueen in Le Mans, the Monaco is the world\'s first water-resistant square chronograph.',
     'gender': 'erkek', 'reference_number': 'CAW211P.FC6356', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '39mm', 'movement': 'Otomatik (Kalibr 11)', 'water_resistance': '100m',
     'price': 88000, 'stock_qty': 10, 'is_featured': False},

    {'brand': 'tag-heuer', 'name': 'TAG Heuer Aquaracer Professional', 'name_en': 'TAG Heuer Aquaracer Professional',
     'description': 'Aquaracer Professional 300, aktif yaşam tarzı için geliştirilmiş yüksek performanslı bir dalış saatidir.',
     'description_en': 'The Aquaracer Professional 300 is a high-performance dive watch developed for an active lifestyle.',
     'gender': 'erkek', 'reference_number': 'WBP201A.BA0632', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '43mm', 'movement': 'Otomatik (Kalibr 5)', 'water_resistance': '300m',
     'price': 55000, 'stock_qty': 18, 'is_featured': True},

    {'brand': 'tag-heuer', 'name': 'TAG Heuer Link Lady', 'name_en': 'TAG Heuer Link Lady',
     'description': 'Link Lady, birbirine bağlı S-link bileziğiyle sportif ve zarif bir tasarım sunar.',
     'description_en': 'The Link Lady offers a sporty yet elegant design with its interconnected S-link bracelet.',
     'gender': 'kadin', 'reference_number': 'WBC1311.BA0600', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '32mm', 'movement': 'Kuvars', 'water_resistance': '200m',
     'price': 42000, 'stock_qty': 12, 'is_featured': True},

    # BREITLING
    {'brand': 'breitling', 'name': 'Breitling Navitimer B01', 'name_en': 'Breitling Navitimer B01',
     'description': 'Pilotların tercihi olan Navitimer, kayan cetvel özelliğiyle uçuş hesaplamalarını kolaylaştırır.',
     'description_en': 'The pilot\'s choice, the Navitimer features a slide rule for easy flight calculations.',
     'gender': 'erkek', 'reference_number': 'AB0138211G1P1', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '46mm', 'movement': 'Otomatik (Kalibr B01)', 'water_resistance': '30m',
     'price': 145000, 'stock_qty': 8, 'is_featured': True},

    {'brand': 'breitling', 'name': 'Breitling Superocean Heritage', 'name_en': 'Breitling Superocean Heritage',
     'description': 'Superocean Heritage, vintage ilhamını modern dalış performansıyla birleştirir.',
     'description_en': 'The Superocean Heritage combines vintage inspiration with modern diving performance.',
     'gender': 'erkek', 'reference_number': 'AB2030121B1S1', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '46mm', 'movement': 'Otomatik (Kalibr 23)', 'water_resistance': '200m',
     'price': 115000, 'stock_qty': 10, 'is_featured': False},

    {'brand': 'breitling', 'name': 'Breitling Chronomat B01 42', 'name_en': 'Breitling Chronomat B01 42',
     'description': 'Chronomat, Breitling\'in amiral gemisi kronografıdır. Sağlamlık ve performansın simgesi.',
     'description_en': 'The Chronomat is Breitling\'s flagship chronograph. A symbol of robustness and performance.',
     'gender': 'erkek', 'reference_number': 'AB0134101B1A1', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '42mm', 'movement': 'Otomatik (Kalibr B01)', 'water_resistance': '200m',
     'price': 128000, 'stock_qty': 7, 'is_featured': True},

    {'brand': 'breitling', 'name': 'Breitling Galactic 36 SleekT', 'name_en': 'Breitling Galactic 36 SleekT',
     'description': 'Galactic, kadınlar için tasarlanmış şık ve çok yönlü bir Breitling modelidir.',
     'description_en': 'The Galactic is a chic and versatile Breitling model designed for women.',
     'gender': 'kadin', 'reference_number': 'A37330121A2A1', 'case_material': 'Paslanmaz Çelik',
     'case_diameter': '36mm', 'movement': 'Otomatik (Kalibr 65)', 'water_resistance': '50m',
     'price': 88000, 'stock_qty': 9, 'is_featured': True},
]

SITE_IMAGES = [
    {'key': 'hero_banner', 'label': 'Ana Sayfa Hero Banner'},
    {'key': 'hero_banner_2', 'label': 'Ana Sayfa İkinci Banner'},
    {'key': 'about_banner', 'label': 'Hakkımızda Banner'},
    {'key': 'brand_rolex', 'label': 'Rolex Marka Görseli'},
    {'key': 'brand_patek', 'label': 'Patek Philippe Marka Görseli'},
    {'key': 'brand_cartier', 'label': 'Cartier Marka Görseli'},
    {'key': 'brand_grandseiko', 'label': 'Grand Seiko Marka Görseli'},
    {'key': 'brand_omega', 'label': 'Omega Marka Görseli'},
    {'key': 'brand_tagheuer', 'label': 'TAG Heuer Marka Görseli'},
    {'key': 'brand_breitling', 'label': 'Breitling Marka Görseli'},
]


def seed():
    with app.app_context():
        brand_map = {}
        for b in BRANDS:
            existing = Brand.query.filter_by(slug=b['slug']).first()
            if not existing:
                brand = Brand(**b)
                db.session.add(brand)
                db.session.flush()
                brand_map[b['slug']] = brand
            else:
                brand_map[b['slug']] = existing

        for p in PRODUCTS:
            brand_slug = p.pop('brand')
            brand = brand_map.get(brand_slug)
            if not brand:
                continue
            existing = Product.query.filter_by(reference_number=p['reference_number']).first()
            if not existing:
                product = Product(brand_id=brand.id, **p)
                db.session.add(product)

        for si in SITE_IMAGES:
            existing = SiteImage.query.filter_by(key=si['key']).first()
            if not existing:
                db.session.add(SiteImage(**si))

        admin = User.query.filter_by(email='admin@luxwatch.com').first()
        if not admin:
            admin = User(
                email='admin@luxwatch.com',
                full_name='Admin',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        db.session.commit()
        print(f'Seed tamamlandi: {len(BRANDS)} marka, {len(PRODUCTS)} urun, {len(SITE_IMAGES)} site gorseli')
        print('Admin: admin@luxwatch.com / admin123')


if __name__ == '__main__':
    seed()
