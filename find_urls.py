import re

content = open(r'C:\Users\infomax\.gemini\antigravity\brain\94073b8f-1361-4da7-b40c-6291bb627902\.system_generated\steps\46\content.md', encoding='utf-8').read()
urls = re.findall(r'https?://[^\s"\'`]+', content)
print([u for u in set(urls) if 'rss' in u or 'api' in u or 'feed' in u])
