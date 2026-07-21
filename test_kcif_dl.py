import requests
import urllib3
urllib3.disable_warnings()

url = 'https://www.kcif.or.kr/common/file/reportFileDownload?atch_no=8UsJvhdVCIQ0z81wLAeZFQ%3D%3D&lang=KR'
r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, verify=False)
ct = r.headers.get('Content-Type', '')
print(f'Status: {r.status_code}, Type: {ct}, Size: {len(r.content)}')

if 'pdf' in ct or 'octet' in ct:
    with open('test_kcif.pdf', 'wb') as f:
        f.write(r.content)
    print('Saved as test_kcif.pdf')
else:
    print('Not PDF. First 200 chars:')
    print(r.text[:200])
