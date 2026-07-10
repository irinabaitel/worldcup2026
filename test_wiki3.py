# -*- coding: utf-8 -*-
import sys, re, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'WC2026-update/1.0 (educational)'}
def wikitext(page):
    r = requests.get('https://en.wikipedia.org/w/api.php', headers=UA, timeout=20, params={
        'action':'parse','page':page,'prop':'wikitext','format':'json','formatversion':'2'})
    return r.json()['parse']['wikitext']

wt = wikitext('2026 FIFA World Cup Group A')
for chunk in wt.split('{{#invoke:football box')[1:]:
    sc = re.search(r'score\s*=.*?(\d+)[–\-](\d+)', chunk)
    g1 = re.search(r'goals1\s*=(.*?)\n\s*\|', chunk, re.S)
    g2 = re.search(r'goals2\s*=(.*?)\n\s*\|', chunk, re.S)
    sco = f"{sc.group(1)}-{sc.group(2)}" if sc else "?"
    # arata meciul 1-0 (Mex-Kor) si unul cu penalty (1-1 Cze-Rsa)
    if sco in ('1-0','1-1'):
        print(f"===== scor {sco} =====")
        print("goals1 RAW:", repr(g1.group(1)[:200]) if g1 else "NONE")
        print("goals2 RAW:", repr(g2.group(1)[:200]) if g2 else "NONE")
        print()
