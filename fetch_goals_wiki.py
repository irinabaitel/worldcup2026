# -*- coding: utf-8 -*-
"""Completeaza marcatorii (goals) in worldcup2026.html din Wikipedia.
Nu atinge meciurile care au deja marcatori."""
import sys, os, re, json, time, subprocess, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
UA = {'User-Agent': 'WC2026-update/1.0 (irinabaitel; educational project)'}
BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, 'worldcup2026.html')

# cod FIFA (cum apare pe Wikipedia) -> nume romana (cum e pe carduri)
CODE2RO = {
 'MEX':'Mexic','RSA':'Africa de Sud','KOR':'Coreea de Sud','CZE':'Rep. Cehă',
 'CAN':'Canada','SUI':'Elveția','BIH':'Bosnia','QAT':'Qatar','SCO':'Scoția',
 'BRA':'Brazilia','MAR':'Maroc','HAI':'Haiti','USA':'SUA','PAR':'Paraguay',
 'AUS':'Australia','TUR':'Turcia','GER':'Germania','CIV':'Coasta de Fildeș',
 'ECU':'Ecuador','CUW':'Curaçao','NED':'Olanda','JPN':'Japonia','SWE':'Suedia',
 'TUN':'Tunisia','ESP':'Spania','CPV':'Capul Verde','KSA':'Arabia Saudită',
 'URU':'Uruguay','BEL':'Belgia','EGY':'Egipt','IRN':'Iran','NZL':'Noua Zeelandă',
 'FRA':'Franța','SEN':'Senegal','NOR':'Norvegia','IRQ':'Irak','ARG':'Argentina',
 'ALG':'Algeria','AUT':'Austria','JOR':'Iordania','POR':'Portugalia','COL':'Columbia',
 'COD':'R.D. Congo','UZB':'Uzbekistan','ENG':'Anglia','CRO':'Croația','GHA':'Ghana','PAN':'Panama',
}
GROUPS = (os.environ.get('WC_GROUPS') or 'ABCDEFGHIJKL')

def wikitext(page):
    for attempt in range(3):
        try:
            r = requests.get('https://en.wikipedia.org/w/api.php', headers=UA, timeout=25, params={
                'action':'parse','page':page,'prop':'wikitext','format':'json','formatversion':'2'})
            j = r.json()
            return None if 'error' in j else j['parse']['wikitext']
        except Exception as e:
            print(f'  (retry {page}: {e})')
            time.sleep(2)
    return None

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
            if name: out.append(f"{name} {mn}'{suf}")
    return out

def matches_from(wt):
    res = []
    for chunk in wt.split('{{#invoke:football box')[1:]:
        c1 = re.search(r'team1\s*=\s*\{\{#invoke:flag\|fb[^|}]*\|([A-Za-z]{2,3})', chunk)
        c2 = re.search(r'team2\s*=\s*\{\{#invoke:flag\|fb[^|}]*\|([A-Za-z]{2,3})', chunk)
        sc = re.search(r'score\s*=.*?(\d+)[–\-](\d+)', chunk)
        g1 = re.search(r'goals1\s*=(.*?)\n\s*\|', chunk, re.S)
        g2 = re.search(r'goals2\s*=(.*?)\n\s*\|', chunk, re.S)
        if not (c1 and c2 and sc): continue
        res.append((c1.group(1), c2.group(1),
                    parse_scorers(g1.group(1)) if g1 else [],
                    parse_scorers(g2.group(1)) if g2 else []))
    return res

def main():
    html = open(HTML, encoding='utf-8').read()

    # nimic de facut daca toate meciurile au deja marcatori (evita fetch inutil)
    if not re.search(r"score:\[\d+,\d+\]\}", html):
        print('Toate meciurile au deja marcatori - nimic de facut.')
        return

    unknown, filled, zerozero, missed = set(), [], 0, []
    for gl in GROUPS:
        time.sleep(0.5)
        wt = wikitext(f'2026 FIFA World Cup Group {gl}')
        if not wt:
            print(f'  ⚠ Grupa {gl}: n-am putut citi pagina'); continue
        for t1, t2, g1, g2 in matches_from(wt):
            if t1 not in CODE2RO: unknown.add(t1); continue
            if t2 not in CODE2RO: unknown.add(t2); continue
            home, away = CODE2RO[t1], CODE2RO[t2]
            for (hx, ax, gh, ga) in [(home, away, g1, g2), (away, home, g2, g1)]:
                pat = re.compile(rf"(\{{h:'{re.escape(hx)}',\s*a:'{re.escape(ax)}',\s*date:'[^']*',\s*score:\[(\d+),(\d+)\])\}}")
                m = pat.search(html)
                if not m:
                    continue
                total = int(m.group(2)) + int(m.group(3))
                if g1 or g2 or total == 0:
                    gobj = f"goals:{{h:{json.dumps(gh,ensure_ascii=False)},a:{json.dumps(ga,ensure_ascii=False)}}}"
                    html = html[:m.start()] + m.group(1) + ', ' + gobj + '}' + html[m.end():]
                    if g1 or g2: filled.append(f"{hx} {gh} | {ax} {ga}")
                    else: zerozero += 1
                else:
                    missed.append(f"{hx} vs {ax} ({m.group(2)}-{m.group(3)})")
                break

    print(f"✅ Marcatori completati: {len(filled)} | 0-0 marcate: {zerozero}")
    for x in filled[:60]: print("  ", x)
    if unknown: print(f"⚠ CODURI NEMAPATE: {sorted(unknown)}")
    if missed: print(f"⚠ Scor non-zero, marcatori negasiti ({len(missed)}): {missed[:20]}")

    if filled or zerozero:
        open(HTML, 'w', encoding='utf-8').write(html)
        try:
            os.chdir(BASE)
            subprocess.run(['git', 'add', 'worldcup2026.html'], check=True)
            subprocess.run(['git', 'commit', '-m', f'Marcatori Wikipedia ({len(filled)} meciuri)'], check=True)
            subprocess.run(['git', 'push'], check=True)
            print('Push GitHub reusit (marcatori).')
        except subprocess.CalledProcessError as e:
            print(f'Eroare git: {e}')
    else:
        print('Nicio modificare.')


if __name__ == '__main__':
    main()
