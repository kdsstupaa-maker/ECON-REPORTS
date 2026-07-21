import sqlite3

conn = sqlite3.connect('data/bok_news.db')
cursor = conn.cursor()
cursor.execute("SELECT id, title, pdf_path FROM reports WHERE pdf_path LIKE '%kiet.re.kr%' LIMIT 5")
for row in cursor.fetchall():
    print(row)
conn.close()
