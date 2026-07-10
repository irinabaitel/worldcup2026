# -*- coding: utf-8 -*-
import sys, re, json, time, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
HTML = r"C:\Users\irina\Sporturi\worldcup2026.html"

src = open(r"C:\Users\irina\Sporturi\update_worldcup.py", encoding="utf-8").read()
g = {'__file__': r'C:\Users\irina\Sporturi\update_worldcup.py'}
exec(compile(src.split("def get_finished_matches")[0], "uw", "exec"), g)
TEAM_MAP = g['TEAM_MAP']
def ro(n): return TEAM_MAP.get(n, n)

def channel_of(vid):
    """Canalul real al unui clip - din pagina video (merge si pe embed dezactivat)."""
    try:
        r = requests.get(f'https://www.youtube.com/watch?v={vid}', headers=UA, timeout=15)
        m = re.search(r'"ownerChannelName":"([^"]+)"', r.text)
        return m.group(1) if m else ''
    except Exception:
        return ''

def search_antena(home, away, hg, ag):
    query = f'Rezumat {home} {away} {hg}-{ag} Campionatul Mondial 2026'
    url = f'https://www.youtube.com/results?search_query={requests.utils.quote(query)}&sp=EgIYAw%253D%253D'
    try: r = requests.get(url, headers=UA, timeout=15)
    except Exception: return None
    for b in r.text.split('"videoRenderer"')[1:9]:
        mid = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', b)
        ch = re.search(r'"(?:ownerText|longBylineText)":\{"runs":\[\{"text":"([^"]+)"', b)
        ti = re.search(r'"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', b)
        if not mid: continue
        channel = ch.group(1) if ch else ''
        title = (ti.group(1) if ti else '').lower()
        if channel == 'AntenaPLAY' and (home.lower() in title or away.lower() in title):
            return mid.group(1)
    return None

html = open(HTML, encoding='utf-8').read()
sched = json.load(open(r"C:\Users\irina\Sporturi\schedule_compact.json", encoding='utf-8'))
finished = [m for m in sched if m['stage']=='GROUP_STAGE' and m['status']=='FINISHED']

ok, replaced, kept, noentry = 0, [], [], []
for m in finished:
    home, away = ro(m['h']), ro(m['a'])
    hg, ag = m['score']
    pat = re.compile(rf"(m:'[^']*(?:{re.escape(home)}[^']*{re.escape(away)}|{re.escape(away)}[^']*{re.escape(home)})[^']*',\s*id:')([a-zA-Z0-9_-]{{11}})(')")
    mm = pat.search(html)
    if not mm:
        noentry.append(f"{home} vs {away}"); continue
    cur = mm.group(2)
    ch = channel_of(cur)
    if ch == 'AntenaPLAY':
        ok += 1; continue
    vid = search_antena(home, away, hg, ag)
    if vid and vid != cur:
        html = html[:mm.start(2)] + vid + html[mm.end(2):]
        replaced.append(f"{home} vs {away}: {cur} ({ch or '?'}) -> {vid} (AntenaPLAY)")
    else:
        kept.append(f"{home} vs {away}: ramas {cur} (canal: {ch or '?'}) - n-am gasit rezumat AntenaPLAY")
    time.sleep(0.2)

open(HTML, 'w', encoding='utf-8').write(html)
print(f"✅ Deja AntenaPLAY (neatinse): {ok}")
print(f"\n🔁 INLOCUITE cu AntenaPLAY ({len(replaced)}):")
for x in replaced: print("  ", x)
print(f"\n⚠ Ramase non-AntenaPLAY ({len(kept)}):")
for x in kept: print("  ", x)
if noentry:
    print(f"\nFara intrare highlight ({len(noentry)}):")
    for x in noentry: print("  ", x)
