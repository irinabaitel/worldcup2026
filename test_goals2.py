# -*- coding: utf-8 -*-
import sys, json, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
H = {'X-Auth-Token': 'fef99d5929c242629c2507c86bdd649f'}

# ia un meci terminat cu multe goluri (ca sa fie clar daca apar marcatori)
r = requests.get('https://api.football-data.org/v4/competitions/WC/matches',
                 headers=H, params={'status':'FINISHED'}, timeout=20).json()
# caut un meci cu scor mare
big = max(r['matches'], key=lambda m:(m['score']['fullTime']['home'] or 0)+(m['score']['fullTime']['away'] or 0))
mid = big['id']
print(f"Meci ales: {big['homeTeam']['name']} {big['score']['fullTime']['home']}-{big['score']['fullTime']['away']} {big['awayTeam']['name']} (id {mid})")

d = requests.get(f'https://api.football-data.org/v4/matches/{mid}', headers=H, timeout=20).json()
print("\n=== Toate cheile din detaliul meciului ===")
print(list(d.keys()))
print("\n=== goals ===")
print(json.dumps(d.get('goals', 'CHEIE LIPSA'), ensure_ascii=False)[:600])
# poate sub alt nume
for k in ('scorers','bookings','events','lineup'):
    if k in d: print(f"\n{k}: prezent -> {json.dumps(d[k], ensure_ascii=False)[:300]}")
