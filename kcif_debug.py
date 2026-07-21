import requests
from bs4 import BeautifulSoup
import re

res = requests.get('https://www.kcif.or.kr/annual/reportView?rpt_no=37327&mn=001002', 
                   headers={'User-Agent':'Mozilla/5.0'}, verify=False)
soup = BeautifulSoup(res.text, 'html.parser')

# 외부 JS 파일 목록
for s in soup.find_all('script', src=True):
    print('JS:', s['src'])

# reportdownload 함수 정의 찾기
for s in soup.find_all('script'):
    if s.string and 'reportdownload' in (s.string or '').lower():
        print('=== Found reportdownload in inline script ===')
        print(s.string[:1000])
        
# reportdownload 호출의 파라미터 추출
for btn in soup.find_all(attrs={'onclick': True}):
    onclick = btn['onclick']
    if 'reportdownload' in onclick:
        print(f'ONCLICK: {onclick}')

# 직접 PDF 다운로드 시도
# reportdownload('8UsJvhdVCIQ0z81wLAeZFQ%3D%3D') => 이 값이 파일 ID
file_id = '8UsJvhdVCIQ0z81wLAeZFQ%3D%3D'
download_url = f'https://www.kcif.or.kr/front/board/reportdownload.do?fileId={file_id}'
print(f'\nTrying: {download_url}')
r = requests.get(download_url, headers={'User-Agent':'Mozilla/5.0'}, verify=False, allow_redirects=True)
print(f'Status: {r.status_code}, Content-Type: {r.headers.get("Content-Type")}, Size: {len(r.content)}')

# POST 시도
download_url2 = f'https://www.kcif.or.kr/front/board/reportdownload.do'
r2 = requests.post(download_url2, data={'fileId': file_id}, headers={'User-Agent':'Mozilla/5.0'}, verify=False)
print(f'POST Status: {r2.status_code}, Content-Type: {r2.headers.get("Content-Type")}, Size: {len(r2.content)}')

# /cmm/fms/FileDown.do 시도
download_url3 = f'https://www.kcif.or.kr/cmm/fms/FileDown.do?atchFileId={file_id}'
r3 = requests.get(download_url3, headers={'User-Agent':'Mozilla/5.0'}, verify=False)
print(f'FileDown Status: {r3.status_code}, Content-Type: {r3.headers.get("Content-Type")}, Size: {len(r3.content)}')
