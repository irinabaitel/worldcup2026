# -*- coding: utf-8 -*-
"""
update_worldcup.py
Ruleaza zilnic (via Task Scheduler).
- Preia TOATE meciurile terminate de la football-data.org (self-healing: daca pica o zi, recupereaza)
- Completeaza scorurile in worldcup2026.html (potrivire indiferent de ordinea gazda/oaspete)
- Cauta rezumate YouTube (canal Antena Sport) pentru meciurile fara highlight
- Face push pe GitHub
"""

import requests, re, json, subprocess, os, time, sys
from datetime import datetime

# Forteaza UTF-8 la output (altfel print-ul crapa pe consola Windows cp1252 la diacritice)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

API_TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN', '')   # din Secret (cloud) sau env local
BASE = os.path.dirname(os.path.abspath(__file__))        # directorul scriptului (merge si pe Linux)
HTML_FILE = os.path.join(BASE, 'worldcup2026.html')
WC_COMPETITION = 'WC'

# Mapare nume API (football-data.org) -> romana (cum apar in HTML)
TEAM_MAP = {
    'Mexico': 'Mexic',
    'South Korea': 'Coreea de Sud',
    'Korea Republic': 'Coreea de Sud',
    'Czechia': 'Rep. Cehă',
    'Czech Republic': 'Rep. Cehă',
    'South Africa': 'Africa de Sud',
    'Canada': 'Canada',
    'Switzerland': 'Elveția',
    'Bosnia-Herzegovina': 'Bosnia',
    'Bosnia and Herzegovina': 'Bosnia',
    'Qatar': 'Qatar',
    'Scotland': 'Scoția',
    'Brazil': 'Brazilia',
    'Morocco': 'Maroc',
    'Haiti': 'Haiti',
    'Australia': 'Australia',
    'Turkey': 'Turcia',
    'Türkiye': 'Turcia',
    'Germany': 'Germania',
    'Ivory Coast': 'Coasta de Fildeș',
    "Côte d'Ivoire": 'Coasta de Fildeș',
    'Ecuador': 'Ecuador',
    'Curaçao': 'Curaçao',
    'Netherlands': 'Olanda',
    'Japan': 'Japonia',
    'Sweden': 'Suedia',
    'Tunisia': 'Tunisia',
    'Spain': 'Spania',
    'Cape Verde Islands': 'Capul Verde',
    'Cape Verde': 'Capul Verde',
    'Saudi Arabia': 'Arabia Saudită',
    'Uruguay': 'Uruguay',
    'Belgium': 'Belgia',
    'Egypt': 'Egipt',
    'Iran': 'Iran',
    'New Zealand': 'Noua Zeelandă',
    'France': 'Franța',
    'Senegal': 'Senegal',
    'Norway': 'Norvegia',
    'Iraq': 'Irak',
    'Argentina': 'Argentina',
    'Algeria': 'Algeria',
    'Austria': 'Austria',
    'Jordan': 'Iordania',
    'Portugal': 'Portugalia',
    'Colombia': 'Columbia',
    'Congo DR': 'R.D. Congo',
    'DR Congo': 'R.D. Congo',
    'Uzbekistan': 'Uzbekistan',
    'England': 'Anglia',
    'Croatia': 'Croația',
    'Ghana': 'Ghana',
    'Panama': 'Panama',
    'USA': 'SUA',
    'United States': 'SUA',
    'Paraguay': 'Paraguay',
}

MONTHS = 'ian feb mar apr mai iun iul aug sep oct nov dec'.split()


def ro(name):
    if name not in TEAM_MAP:
        print(f'  ⚠ Nume nemapat (verifica TEAM_MAP): "{name}"')
    return TEAM_MAP.get(name, name)


def get_finished_matches():
    """Toate meciurile terminate (nu doar de ieri) -> self-healing."""
    url = f'https://api.football-data.org/v4/competitions/{WC_COMPETITION}/matches'
    headers = {'X-Auth-Token': API_TOKEN}
    r = requests.get(url, headers=headers, params={'status': 'FINISHED'}, timeout=20)
    if r.status_code != 200:
        print(f'Eroare API: {r.status_code} - {r.text[:200]}')
        return []
    matches = []
    for m in r.json().get('matches', []):
        dt = datetime.strptime(m['utcDate'][:10], '%Y-%m-%d')
        grp = m.get('group')
        matches.append({
            'home': ro(m['homeTeam']['name']),
            'away': ro(m['awayTeam']['name']),
            'hg': m['score']['fullTime']['home'],
            'ag': m['score']['fullTime']['away'],
            'day': f'{dt.day} {MONTHS[dt.month-1]}',
            'group': grp[-1] if grp else None,          # 'GROUP_A' -> 'A'
            'is_group': m.get('stage') == 'GROUP_STAGE',
        })
    return matches


def fill_score(html, home, away, hg, ag):
    """Completeaza score:null in HTML, indiferent de ordinea gazda/oaspete."""
    # orientare normala (gazda=home)
    pat = rf"(\{{h:'{re.escape(home)}',\s*a:'{re.escape(away)}',\s*date:'[^']*',\s*score:)null"
    new, n = re.subn(pat, rf"\g<1>[{hg},{ag}]", html)
    if n:
        return new, True
    # orientare inversata (gazda=away) -> scor inversat
    pat = rf"(\{{h:'{re.escape(away)}',\s*a:'{re.escape(home)}',\s*date:'[^']*',\s*score:)null"
    new, n = re.subn(pat, rf"\g<1>[{ag},{hg}]", html)
    if n:
        return new, True
    return html, False


def highlight_exists(html, home, away):
    """True daca exista deja un highlight cu cele doua echipe (orice ordine)."""
    a = re.search(rf"m:'[^']*{re.escape(home)}[^']*{re.escape(away)}[^']*'", html)
    b = re.search(rf"m:'[^']*{re.escape(away)}[^']*{re.escape(home)}[^']*'", html)
    return bool(a or b)


def _oembed(vid):
    try:
        r = requests.get('https://www.youtube.com/oembed',
                         params={'url': f'https://www.youtube.com/watch?v={vid}', 'format': 'json'},
                         headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return d.get('author_name', ''), d.get('width', 0), d.get('height', 0), d.get('title', '')
    except Exception:
        pass
    return '', 0, 0, ''


def search_youtube(home, away, hg, ag):
    """Cauta rezumatul de pe canalul AntenaPLAY, format landscape (exclude Shorts verticale)."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    query = f'Rezumat {home} {away} {hg}-{ag} Campionatul Mondial 2026'
    # sp=EgIYAw... = filtru durata 4-20 min -> exclude Shorts-urile verticale
    url = f'https://www.youtube.com/results?search_query={requests.utils.quote(query)}&sp=EgIYAw%253D%253D'
    try:
        r = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        print(f'  YouTube search error: {e}')
        return None
    ids = []
    for b in r.text.split('"videoRenderer"')[1:]:
        m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', b)
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    for vid in ids[:8]:
        author, w, h, title = _oembed(vid)
        if author == 'AntenaPLAY' and w and h and w >= h:
            tl = title.lower()
            if home.lower() in tl or away.lower() in tl:
                return vid          # doar AntenaPLAY landscape, meci corect
    return None                     # mai bine niciun clip decat unul gresit/vertical


def add_highlight(html, m, vid):
    grp = f"group:'{m['group']}', " if m['group'] else ''
    entry = (f"  {{day:'{m['day']}', stage:'Grupe', {grp}"
             f"m:'{m['home']} {m['hg']}–{m['ag']} {m['away']}', id:'{vid}'}},\n")
    return html.replace('  // Optimi', entry + '  // Optimi', 1)


def trigger_pages_build():
    """GitHub Pages nu reconstruieste mereu automat dupa push -> il fortam."""
    try:
        subprocess.run(['gh', 'api', 'repos/irinabaitel/worldcup2026/pages/builds', '-X', 'POST'],
                       check=True, capture_output=True)
        print('Build GitHub Pages declansat manual.')
    except Exception as e:
        print(f'  (Nu am putut forta build-ul Pages, se face oricum automat de obicei: {e})')


def git_push(msg):
    os.chdir(BASE)
    subprocess.run(['git', 'add', 'worldcup2026.html'], check=True)
    subprocess.run(['git', 'commit', '-m', msg], check=True)
    subprocess.run(['git', 'push'], check=True)
    print('Push GitHub reusit!')
    trigger_pages_build()


def main():
    print(f'\n=== Update World Cup {datetime.now().strftime("%d.%m.%Y %H:%M")} ===\n')

    if not API_TOKEN:
        print('EROARE: lipseste FOOTBALL_DATA_TOKEN (variabila de mediu / GitHub Secret).')
        return

    matches = get_finished_matches()
    if not matches:
        print('Niciun meci terminat (sau API indisponibil).')
        return
    print(f'1. {len(matches)} meciuri terminate preluate de la API.\n')

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    changed = False

    # --- Scoruri ---
    print('2. Completez scorurile lipsa...')
    for m in matches:
        html, ok = fill_score(html, m['home'], m['away'], m['hg'], m['ag'])
        if ok:
            print(f"   ✔ {m['home']} {m['hg']}-{m['ag']} {m['away']} ({m['day']})")
            changed = True

    # --- Highlights (doar grupe, doar meciurile fara highlight) ---
    print('\n3. Caut highlight-uri pentru meciurile fara rezumat...')
    for m in matches:
        if not m['is_group']:
            continue  # faza eliminatorie -> de tratat separat cand exista sectiunea
        if highlight_exists(html, m['home'], m['away']):
            continue
        vid = search_youtube(m['home'], m['away'], m['hg'], m['ag'])
        if vid and f"id:'{vid}'" in html:
            # acelasi clip e deja folosit de alt meci -> aproape sigur gresit, nu-l pune
            print(f"   ⚠ Sar (video {vid} deja folosit de alt meci): {m['home']} vs {m['away']}")
            vid = None
        if vid:
            html = add_highlight(html, m, vid)
            print(f"   ✔ Highlight adaugat: {m['home']} vs {m['away']} ({vid})")
            changed = True
        else:
            print(f"   – Negasit/sarit: {m['home']} vs {m['away']}")
        time.sleep(2)

    # --- Salveaza + push ---
    if changed:
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print('\n4. Push pe GitHub...')
        try:
            git_push(f'Auto-update {datetime.now().strftime("%d.%m %H:%M")}')
        except subprocess.CalledProcessError as e:
            print(f'Eroare git: {e}')
    else:
        print('\nNicio modificare necesara (totul e deja la zi).')

    print('\nGata!')


if __name__ == '__main__':
    main()
