import sqlite3
conn = sqlite3.connect('instance/shop.db')
cur = conn.cursor()
cur.execute('SELECT id, name, image_path FROM products ORDER BY id')
rows = cur.fetchall()
for r in rows:
    print(r)
cur.execute('SELECT id, name, cover_image_path FROM brands ORDER BY id')
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
