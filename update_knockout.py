# -*- coding: utf-8 -*-
"""
update_knockout.py
Populeaza/actualizeaza bracketul fazei eliminatorii (obiectul KNOCKOUT din
worldcup2026.html) din football-data.org. Ordinea meciurilor din API = ordinea
bracketului (perechi consecutive -> meciul din runda urmatoare).
MARCATORII din eliminatorii se iau AICI, de pe Wikipedia (pagina 'knockout stage'),
si se scriu in campul goals al fiecarui meci -> nu se pierd la regenerare.
Ruleaza ca pas in workflow-ul cloud, dupa scoruri.
"""
import requests, re, os, sys, subprocess, json
from datetime import datetime
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from update_worldcup import TEAM_MAP, MONTHS
from fetch_goals_wiki import wikitext, matches_from, CODE2RO   # reutilizam parsarea Wikipedia

API_TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN', '')
BASE = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE, 'worldcup2026.html')

# API stage -> cheia din KNOCKOUT (HTML)
STAGE2KEY = {
    'LAST_32': 'Șaisprezecimi',
    'LAST_16': 'Optimi',
    'QUARTER_FINALS': 'Sferturi',
    'SEMI_FINALS': 'Semifinale',
    'THIRD_PLACE': 'Finala mică',
    'FINAL': 'Finala',
}
ORDER = ['Șaisprezecimi', 'Optimi', 'Sferturi', 'Semifinale', 'Finala', 'Finala mică']


def ro(name):
    if not name:
        return None
    if name not in TEAM_MAP:
        print(f'  ⚠ Nume nemapat (TEAM_MAP): "{name}"')
    return TEAM_MAP.get(name, name)


def flag_map(html):
    """RO_nume -> steag, citit din datele GROUPS din HTML."""
    fm = {}
    for n, f in re.findall(r"\{n:'([^']+)',\s*f:'([^']*)'\}", html):
        fm[n] = f
    return fm


def day_str(utc):
    dt = datetime.strptime(utc[:10], '%Y-%m-%d')
    return f'{dt.day} {MONTHS[dt.month-1]}'


def js_team(v):
    return 'null' if v is None else "'" + v.replace("'", "\\'") + "'"


def _winner_ro(m):
    w = m.get('score', {}).get('winner')
    if w == 'HOME_TEAM': return ro(m['homeTeam'].get('name'))
    if w == 'AWAY_TEAM': return ro(m['awayTeam'].get('name'))
    return None


def reorder_r32(r32, optimi):
    """API returneaza Șaisprezecimile in alta ordine (dupa data/stadion), NU in
    ordinea bracketului -> liniile catre optimi ies gresite. Le reordonam ca
    fiecare pereche consecutiva sa hraneasca optimea de langa ea. (Optimi/sferturi/
    semi sunt deja in ordine buna in API: perechi vecine -> runda urmatoare.)"""
    by_winner = {}
    for m in r32:
        w = _winner_ro(m)
        if w:
            by_winner[w] = m
    ordered, seen = [], set()
    for om in optimi:
        for name in (ro(om['homeTeam'].get('name')), ro(om['awayTeam'].get('name'))):
            m = by_winner.get(name)
            if m is not None and id(m) not in seen:
                ordered.append(m); seen.add(id(m))
    for m in r32:                       # optime inca nedecisa -> lasam ordinea API
        if id(m) not in seen:
            ordered.append(m); seen.add(id(m))
    return ordered


def knockout_scorers():
    """{frozenset({roA, roB}): {roA:[goluri], roB:[goluri]}} din Wikipedia. Doua pagini:
    'round of 32' (Șaisprezecimile, template 'Football box') + 'knockout stage'
    (optimi+). Marcatorii sunt din 90'+prelungiri (nu loviturile de departajare)."""
    lookup = {}
    for page in ['2026 FIFA World Cup round of 32', '2026 FIFA World Cup knockout stage']:
        wt = wikitext(page)
        if not wt:
            print(f'  ⚠ N-am putut citi "{page}".')
            continue
        for t1, t2, g1, g2 in matches_from(wt):
            if t1 not in CODE2RO or t2 not in CODE2RO:
                continue
            r1, r2 = CODE2RO[t1], CODE2RO[t2]
            lookup[frozenset((r1, r2))] = {r1: g1, r2: g2}
    print(f'  Marcatori knockout Wikipedia: {len(lookup)} meciuri.')
    return lookup


def match_obj(m, fm, scorers):
    home = ro(m['homeTeam'].get('name'))
    away = ro(m['awayTeam'].get('name'))
    hf = fm.get(home, '') if home else ''
    af = fm.get(away, '') if away else ''
    parts = [f"h:{js_team(home)}", f"a:{js_team(away)}",
             f"hf:'{hf}'", f"af:'{af}'", f"date:'{day_str(m['utcDate'])}'"]
    s = m.get('score', {})
    if m.get('status') == 'FINISHED':
        if s.get('duration') == 'PENALTY_SHOOTOUT':
            # ATENTIE: fullTime include penalty-urile adunate la scor -> folosim
            # scorul din 90'+prelungiri (egalitate) si penalty-urile separat
            rt = s.get('regularTime') or {}
            et = s.get('extraTime') or {}
            sh = (rt.get('home') or 0) + (et.get('home') or 0)
            sa = (rt.get('away') or 0) + (et.get('away') or 0)
            pen = s.get('penalties') or {}
            parts.append(f"score:[{sh},{sa}]")
            parts.append(f"pen:[{pen.get('home',0)},{pen.get('away',0)}]")
        else:
            ft = s.get('fullTime') or {}
            if ft.get('home') is not None and ft.get('away') is not None:
                parts.append(f"score:[{ft['home']},{ft['away']}]")
    # marcatori din Wikipedia (daca ii avem pentru perechea asta)
    if home and away:
        gg = scorers.get(frozenset((home, away)))
        if gg:
            gh, ga = gg.get(home, []), gg.get(away, [])
            if gh or ga:
                parts.append(f"goals:{{h:{json.dumps(gh, ensure_ascii=False)},a:{json.dumps(ga, ensure_ascii=False)}}}")
    return '{' + ', '.join(parts) + '}'


def main():
    if not API_TOKEN:
        print('EROARE: lipseste FOOTBALL_DATA_TOKEN.')
        return
    r = requests.get('https://api.football-data.org/v4/competitions/WC/matches',
                     headers={'X-Auth-Token': API_TOKEN}, timeout=25)
    if r.status_code != 200:
        print(f'Eroare API: {r.status_code} - {r.text[:200]}')
        return
    matches = r.json().get('matches', [])

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    fm = flag_map(html)

    # grupeaza meciurile pe runda, in ordinea returnata de API (= ordine bracket)
    buckets = {k: [] for k in ORDER}
    for m in matches:
        key = STAGE2KEY.get(m.get('stage'))
        if key:
            buckets[key].append(m)

    if not any(buckets.values()):
        print('Inca niciun meci de eliminatorii la API.')
        return

    # Șaisprezecimile vin in ordine gresita de la API -> reordoneaza dupa bracket
    buckets['Șaisprezecimi'] = reorder_r32(buckets['Șaisprezecimi'], buckets['Optimi'])

    scorers = knockout_scorers()

    lines = ['const KNOCKOUT = {']
    for i, key in enumerate(ORDER):
        arr = ','.join(match_obj(m, fm, scorers) for m in buckets[key])
        comma = ',' if i < len(ORDER) - 1 else ''
        lines.append(f"  '{key}':[{arr}]{comma}")
    lines.append('};')
    new_block = '\n'.join(lines)

    new_html, n = re.subn(r'const KNOCKOUT = \{[\s\S]*?\n\};', new_block, html, count=1)
    if not n:
        print('EROARE: n-am gasit blocul KNOCKOUT in HTML.')
        return
    if new_html == html:
        print('Bracket deja la zi — nicio modificare.')
        return

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)
    cnt = {k: sum(1 for m in v if m.get('homeTeam', {}).get('name')) for k, v in buckets.items()}
    fin = sum(1 for v in buckets.values() for m in v if m.get('status') == 'FINISHED')
    print(f'✅ Bracket actualizat. Meciuri cu echipe: {cnt}. Terminate: {fin}.')

    # commit + push (in cloud)
    try:
        os.chdir(BASE)
        subprocess.run(['git', 'add', 'worldcup2026.html'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Bracket eliminatorii actualizat {datetime.now().strftime("%d.%m %H:%M")}'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print('Push GitHub reusit (bracket).')
    except subprocess.CalledProcessError as e:
        print(f'Eroare git (sau nimic de comis): {e}')


if __name__ == '__main__':
    main()
