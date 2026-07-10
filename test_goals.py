# -*- coding: utf-8 -*-
import sys, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

TOKEN = 'fef99d5929c242629c2507c86bdd649f'
H = {'X-Auth-Token': TOKEN}

# ia un meci terminat
r = requests.get('https://api.football-data.org/v4/competitions/WC/matches',
                 headers=H, params={'status':'FINISHED'}, timeout=20).json()
m = r['matches'][0]
mid = m['id']
print(f"Meci: {m['homeTeam']['name']} {m['score']['fullTime']['home']}-{m['score']['fullTime']['away']} {m['awayTeam']['name']} (id {mid})")
print(f"In lista, camp 'goals': {m.get('goals', 'LIPSESTE')}")

# cere detaliul meciului (endpoint individual)
d = requests.get(f'https://api.football-data.org/v4/matches/{mid}', headers=H, timeout=20).json()
print(f"\nDetaliu meci, camp 'goals': {d.get('goals', 'LIPSESTE')}")
print(f"Nr. goluri returnate: {len(d.get('goals') or [])}")
