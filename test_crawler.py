import sys
sys.path.insert(0, '.')
from src.crawlers.bok_news_crawler import BOKNewsCrawler

print("=== BOK 뉴스 크롤러 테스트 ===\n")
crawler = BOKNewsCrawler(pdf_dir='data/pdfs', today_only=True, max_items=5)
items = crawler.fetch_today_news()
print(f'\n수집 건수: {len(items)}')
for i, item in enumerate(items, 1):
    print(f'\n[{i}] {item["title"]}')
    print(f'    날짜: {item["date"]} | 카테고리: {item["category"]}')
    print(f'    URL: {item["detail_url"][:80]}')
    for a in item.get("attachments", []):
        print(f'    첨부: {a["name"][:40]} ({a["ext"]})')
