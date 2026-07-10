# -*- coding: utf-8 -*-
"""
backfill_highlights.py — completeaza highlights-urile lipsa pentru TOATE meciurile
de grupa deja jucate (cu scor) din worldcup2026.html, folosind search_youtube
imbunatatit din update_worldcup.py. Nu are nevoie de API (citeste meciurile din HTML).
"""
import sys, re, time, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from update_worldcup import search_youtube, highlight_exists, add_highlight

BASE = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE, 'worldcup2026.html')

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

# Decupez doar sectiunea GROUPS (ca sa nu prind meciuri din faza eliminatorie)
g_start = html.index('const GROUPS = {')
g_end = html.index('function calcStandings', g_start)
section = html[g_start:g_end]

# Pozitiile literelor de grupa (name:'A'..'L')
group_marks = [(m.start(), m.group(1)) for m in re.finditer(r"name:'([A-L])'", section)]

def group_of(pos):
    g = '?'
    for mpos, letter in group_marks:
        if mpos <= pos:
            g = letter
        else:
            break
    return g

# Toate meciurile jucate (cu scor numeric)
mre = re.compile(r"\{h:'([^']*)',\s*a:'([^']*)',\s*date:'([^']*)',\s*score:\[(\d+),\s*(\d+)\]")
played = []
for m in mre.finditer(section):
    home, away, date, hg, ag = m.group(1), m.group(2), m.group(3), int(m.group(4)), int(m.group(5))
    played.append({'home': home, 'away': away, 'day': date, 'hg': hg, 'ag': ag, 'group': group_of(m.start())})

print(f'{len(played)} meciuri de grupa jucate gasite.\n')

changed = False
added, skipped, notfound = 0, 0, 0
for m in played:
    if highlight_exists(html, m['home'], m['away']):
        skipped += 1
        continue
    print(f"Caut: [{m['group']}] {m['home']} {m['hg']}-{m['ag']} {m['away']} ({m['day']})")
    vid = search_youtube(m['home'], m['away'], m['hg'], m['ag'])
    if vid and f"id:'{vid}'" in html:
        print(f"   ⚠ Sar (video {vid} deja folosit de alt meci)")
        vid = None
    if vid:
        html = add_highlight(html, m, vid)
        print(f"   ✔ Adaugat: {vid}")
        added += 1
        changed = True
    else:
        print(f"   – Negasit")
        notfound += 1
    time.sleep(2)

print(f"\nRezultat: {added} adaugate, {skipped} aveau deja, {notfound} negasite.")

if changed:
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML salvat.")
else:
    print("Nicio modificare.")
