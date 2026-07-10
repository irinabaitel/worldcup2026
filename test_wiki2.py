# -*- coding: utf-8 -*-
import sys, re, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'WC2026-update/1.0 (educational)'}

def wikitext(page):
    r = requests.get('https://en.wikipedia.org/w/api.php', headers=UA, timeout=20, params={
        'action':'parse','page':page,'prop':'wikitext','format':'json','formatversion':'2'})
    return r.json()['parse']['wikitext']

def parse_scorers(block):
    out = []
    for line in block.split('\n'):
        line = line.strip()
        if not line.startswith('*'): continue
        line = re.sub(r'<ref[\s\S]*?</ref>', '', line[1:])
        line = re.sub(r'<ref[^>]*/?>', '', line)
        nm = re.search(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', line)
        name = nm.group(1).strip() if nm else re.split(r"\d|\{\{", line)[0].strip()
        name = re.sub(r'\{\{[^}]*\}\}', '', name).strip(" ([{")
        goals = []
        for gt in re.findall(r'\{\{goal\|([^}]+)\}\}', line, re.I):
            args = [a.strip() for a in gt.split('|')]
            suf = 'pen' if any('pen' in a.lower() for a in args) else \
                  ('csc' if any(('o.g' in a.lower() or 'own' in a.lower()) for a in args) else '')
            for a in args:
                mm = re.match(r'^(\d+(?:\+\d+)?)', a)
                if mm: goals.append((mm.group(1), suf))
        if not goals:
            pen = '(pen' in line.lower()
            og = 'o.g.' in line.lower() or 'own goal' in line.lower()
            for mn in re.findall(r"(\d+(?:\+\d+)?)'", line):
                goals.append((mn, 'pen' if pen else ('csc' if og else '')))
        for mn, suf in goals:
            out.append(f"{name} {mn}'{suf}")
    return out

def matches_from(page):
    wt = wikitext(page)
    res = []
    for chunk in wt.split('{{#invoke:football box')[1:]:
        c1 = re.search(r'team1\s*=\s*\{\{#invoke:flag\|fb[^|}]*\|([A-Za-z]{2,3})', chunk)
        c2 = re.search(r'team2\s*=\s*\{\{#invoke:flag\|fb[^|}]*\|([A-Za-z]{2,3})', chunk)
        sc = re.search(r'score\s*=.*?(\d+)[–\-](\d+)', chunk)
        g1 = re.search(r'goals1\s*=(.*?)\n\s*\|', chunk, re.S)
        g2 = re.search(r'goals2\s*=(.*?)\n\s*\|', chunk, re.S)
        if not (c1 and c2 and sc): continue
        res.append({'t1':c1.group(1),'t2':c2.group(1),'score':f"{sc.group(1)}-{sc.group(2)}",
                    'g1':parse_scorers(g1.group(1)) if g1 else [],
                    'g2':parse_scorers(g2.group(1)) if g2 else []})
    return res

for page in ['2026 FIFA World Cup Group A']:
    print(f"===== {page} =====")
    for m in matches_from(page):
        print(f"  {m['t1']} {m['score']} {m['t2']}  | {m['g1']} || {m['g2']}")
