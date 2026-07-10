# -*- coding: utf-8 -*-
import sys, re, requests
from collections import Counter
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'WC2026-update/1.0 (educational)'}

def wikitext(page):
    r = requests.get('https://en.wikipedia.org/w/api.php', headers=UA, timeout=20, params={
        'action':'parse','page':page,'prop':'wikitext','format':'json','formatversion':'2'})
    return r.json()['parse']['wikitext']

wt = wikitext('2026 FIFA World Cup Group A')

# ce template-uri exista?
names = Counter(re.findall(r'\{\{\s*([A-Za-z][\w ]+?)[\s\|\n]', wt))
print("=== Template-uri frecvente ===")
for n, c in names.most_common(15):
    print(f"  {c:3}  {{{{{n}}}}}")

# snippet in jurul primului 'goals1' sau '{{goal'
idx = wt.find('goals1')
if idx < 0: idx = wt.find('{{goal')
print("\n=== Context in jurul marcatorilor ===")
print(wt[max(0,idx-400):idx+500])
