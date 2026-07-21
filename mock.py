import json, os, datetime

data = [
    {'institution': '한국은행', 'title': '2023년 하반기 금융안정보고서', 'date': datetime.datetime.now().strftime('%Y-%m-%d'), 'filename': 'sample_bok.pdf', 'url': '#'},
    {'institution': 'KDI', 'title': '최근 경제동향 및 전망', 'date': datetime.datetime.now().strftime('%Y-%m-%d'), 'filename': 'sample_kdi.pdf', 'url': '#'},
    {'institution': '국제금융센터', 'title': '글로벌 경제이슈 브리프', 'date': datetime.datetime.now().strftime('%Y-%m-%d'), 'filename': 'sample_kcif.pdf', 'url': '#'}
]

os.makedirs('data', exist_ok=True)
os.makedirs('pdfs', exist_ok=True)

with open('data/reports.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

for d in data:
    with open(f"pdfs/{d['filename']}", 'wb') as f:
        f.write(b'%PDF-1.4 mock')
