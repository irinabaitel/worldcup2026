# -*- coding: utf-8 -*-
"""Diagnostic: arata ce extrage parsarea din fiecare rezultat (in cloud)."""
import sys, re, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

q = 'Rezumat Franța Maroc Campionatul Mondial 2026'
url = f'https://www.youtube.com/results?search_query={requests.utils.quote(q)}&gl=RO&hl=ro'
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
     'Accept-Language': 'ro-RO,ro;q=0.9'}
t = requests.get(url, headers=h, timeout=20).text
print('len', len(t), '| videoRenderer blocks:', len(t.split('"videoRenderer"'))-1)
for i, b in enumerate(t.split('"videoRenderer"')[1:25]):
    mid = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', b)
    ch = re.search(r'"(?:ownerText|longBylineText)":\{"runs":\[\{"text":"([^"]+)"', b)
    ti = re.search(r'"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', b)
    if not mid: continue
    print(f'  [{i}] ch={ch.group(1) if ch else "?"!r} | ti={(ti.group(1) if ti else "?")[:55]!r}')
