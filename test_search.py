# -*- coding: utf-8 -*-
import sys, re, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def search_antena(home, away, hg, ag):
    query = f'Rezumat {home} {away} {hg}-{ag} Campionatul Mondial 2026'
    url = f'https://www.youtube.com/results?search_query={requests.utils.quote(query)}&sp=EgIYAw%253D%253D'
    r = requests.get(url, headers=UA, timeout=15)
    for b in r.text.split('"videoRenderer"')[1:9]:
        mid = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', b)
        ch = re.search(r'"(?:ownerText|longBylineText)":\{"runs":\[\{"text":"([^"]+)"', b)
        ti = re.search(r'"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', b)
        if not mid: continue
        channel = ch.group(1) if ch else ''
        title = ti.group(1) if ti else ''
        tl = title.lower()
        if channel == 'AntenaPLAY' and (home.lower() in tl or away.lower() in tl):
            return mid.group(1), title
    return None, None

tests = [
    ('Iordania','Algeria',1,2), ('Anglia','Ghana',0,0),
    ('Panama','Croația',0,1), ('Columbia','R.D. Congo',1,0),
    ('SUA','Australia',2,0), ('Scoția','Maroc',0,1),
]
for h,a,hg,ag in tests:
    vid, title = search_antena(h,a,hg,ag)
    print(f"{h} vs {a}: {vid or '— negasit'}  | {title or ''}")
