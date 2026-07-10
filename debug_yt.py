# -*- coding: utf-8 -*-
"""Diagnostic: ce primeste cloud-ul de la YouTube (de ce nu gaseste clipurile)."""
import sys, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

q = 'Rezumat Franța Maroc Campionatul Mondial 2026'
url = f'https://www.youtube.com/results?search_query={requests.utils.quote(q)}&gl=RO&hl=ro'
h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
     'Accept-Language': 'ro-RO,ro;q=0.9'}
r = requests.get(url, headers=h, timeout=20)
t = r.text
low = t.lower()
print('status:', r.status_code, '| len:', len(t))
print('videoRenderer:', t.count('"videoRenderer"'))
print('AntenaPLAY:', t.count('AntenaPLAY'))
print('consent-related:', any(w in low for w in ['consent', 'consimt', 'before you continue', 'accept all', 'cookies']))
print('captcha/blocked:', any(w in low for w in ['unusual traffic', 'captcha', 'not a robot', 'sorry/index']))
print('title-ish:', t[:400].replace('\n', ' ')[:400])
