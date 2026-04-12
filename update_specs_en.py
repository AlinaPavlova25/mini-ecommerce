import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Product

SPECS_EN = {
    '126610LN':        {'case_material_en': 'Oyster Steel',        'movement_en': 'Automatic (Calibre 3235)',        'water_resistance_en': '300m'},
    '126200':          {'case_material_en': 'Oyster Steel',        'movement_en': 'Automatic (Calibre 3235)',        'water_resistance_en': '100m'},
    '228235':          {'case_material_en': '18k Everose Gold',    'movement_en': 'Automatic (Calibre 3255)',        'water_resistance_en': '100m'},
    '279138RBR':       {'case_material_en': 'Oyster Steel',        'movement_en': 'Automatic (Calibre 2236)',        'water_resistance_en': '100m'},
    '126710BLNR':      {'case_material_en': 'Oyster Steel',        'movement_en': 'Automatic (Calibre 3285)',        'water_resistance_en': '100m'},
    '5711/1A-014':     {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 26-330 S C)', 'water_resistance_en': '120m'},
    '5196R-001':       {'case_material_en': '18k Rose Gold',       'movement_en': 'Manual Wind (Calibre 215 PS)',   'water_resistance_en': '30m'},
    '7300/1200A-011':  {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 324 S C)',    'water_resistance_en': '30m'},
    '5167A-001':       {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 324 S C)',    'water_resistance_en': '120m'},
    'WSSA0018':        {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 1847 MC)',    'water_resistance_en': '100m'},
    'WGTA0011':        {'case_material_en': '18k Yellow Gold',     'movement_en': 'Manual Wind (Calibre 430 MC)',   'water_resistance_en': '30m'},
    'WSBB0049':        {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 076)',        'water_resistance_en': '30m'},
    'WJPN0019':        {'case_material_en': '18k Yellow Gold',     'movement_en': 'Quartz',                         'water_resistance_en': '30m'},
    'SBGA211':         {'case_material_en': 'Titanium',            'movement_en': 'Spring Drive (Calibre 9R65)',    'water_resistance_en': '100m'},
    'SBGW231':         {'case_material_en': 'Stainless Steel',     'movement_en': 'Manual Wind (Calibre 9S64)',     'water_resistance_en': '30m'},
    'STGK009':         {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 9S45)',       'water_resistance_en': '30m'},
    'SBGC201':         {'case_material_en': 'Titanium',            'movement_en': 'Spring Drive (Calibre 9R86)',    'water_resistance_en': '100m'},
    '310.30.42.50.01.001': {'case_material_en': 'Stainless Steel', 'movement_en': 'Manual Wind (Calibre 3861)',     'water_resistance_en': '50m'},
    '210.30.42.20.01.001': {'case_material_en': 'Stainless Steel', 'movement_en': 'Automatic (Calibre 8800)',       'water_resistance_en': '300m'},
    '428.15.36.60.02.002': {'case_material_en': 'Stainless Steel', 'movement_en': 'Automatic (Calibre 8800)',       'water_resistance_en': '30m'},
    '131.10.29.20.55.001': {'case_material_en': 'Stainless Steel', 'movement_en': 'Automatic (Calibre 8700)',       'water_resistance_en': '50m'},
    'CBN2A1B.FC6492':  {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre Heuer 02)',   'water_resistance_en': '100m'},
    'CAW211P.FC6356':  {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 11)',         'water_resistance_en': '100m'},
    'WBP201A.BA0632':  {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 5)',          'water_resistance_en': '300m'},
    'WBC1311.BA0600':  {'case_material_en': 'Stainless Steel',     'movement_en': 'Quartz',                         'water_resistance_en': '200m'},
    'AB0138211G1P1':   {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre B01)',        'water_resistance_en': '30m'},
    'AB2030121B1S1':   {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 23)',         'water_resistance_en': '200m'},
    'AB0134101B1A1':   {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre B01)',        'water_resistance_en': '200m'},
    'A37330121A2A1':   {'case_material_en': 'Stainless Steel',     'movement_en': 'Automatic (Calibre 65)',         'water_resistance_en': '50m'},
}

with app.app_context():
    updated = 0
    for ref, specs in SPECS_EN.items():
        product = Product.query.filter_by(reference_number=ref).first()
        if product:
            product.case_material_en = specs['case_material_en']
            product.movement_en = specs['movement_en']
            product.water_resistance_en = specs['water_resistance_en']
            updated += 1
        else:
            print(f'Bulunamadi: {ref}')
    db.session.commit()
    print(f'{updated} urun guncellendi.')
