import json
import os

r = json.load(open('data/reports.json', encoding='utf-8'))
print(f'Total reports: {len(r)}')
print()

# 기관별 집계
insts = sorted(set(x['institution'] for x in r))
for inst in insts:
    items = [x for x in r if x['institution'] == inst]
    print(f'  {inst}: {len(items)}건')
print()

# filename 없는 항목 (원문 링크만 있는 것)
no_file = [x for x in r if 'filename' not in x or not x.get('filename')]
print(f'파일 없는(원문 링크만 있는) 항목: {len(no_file)}건')
for x in no_file:
    print(f'  - [{x["institution"]}] {x["title"][:60]}')
print()

# filename 있는 항목 중 실제 파일이 존재하는지 확인
missing_files = []
for x in r:
    fn = x.get('filename', '')
    if fn:
        path = os.path.join('pdfs', fn)
        if not os.path.exists(path):
            missing_files.append(x)

print(f'filename은 있지만 실제 파일이 없는 항목: {len(missing_files)}건')
for x in missing_files:
    print(f'  - [{x["institution"]}] {x.get("filename", "")}')
