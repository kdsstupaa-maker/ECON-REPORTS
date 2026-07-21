import sqlite3
db_path = 'data/bok_news.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("테이블 목록:", tables)
for t in tables:
    cur.execute(f"SELECT count(*) FROM {t[0]}")
    print(f"  {t[0]}: {cur.fetchone()[0]}건")
# 오늘 자료만 삭제 (재처리 허용)
cur.execute("DELETE FROM reports WHERE created_at >= date('now', 'localtime')")
deleted = cur.rowcount
conn.commit()
conn.close()
print(f"오늘 처리 이력 {deleted}건 초기화 완료")
