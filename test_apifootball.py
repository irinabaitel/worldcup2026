# -*- coding: utf-8 -*-
import sys, requests
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

KEY = '3d18f44d32bfd2e180e8844078a52579'
BASE = 'https://v3.football.api-sports.io'
H = {'x-apisports-key': KEY}

def get(path, **params):
    r = requests.get(f'{BASE}{path}', headers=H, params=params, timeout=20)
    return r.json()

# 1. gaseste liga World Cup
print("=== 1. Caut liga World Cup ===")
d = get('/leagues', search='World Cup')
print("errors:", d.get('errors'))
for L in d.get('response', [])[:5]:
    seasons = [s['year'] for s in L.get('seasons', [])]
    print(f"  id={L['league']['id']} | {L['league']['name']} ({L['league']['type']}) | sezoane recente: {seasons[-3:]}")

# 2. fixtures WC 2026 terminate (league 1 = FIFA World Cup)
print("\n=== 2. Meciuri terminate WC league=1 season=2026 ===")
f = get('/fixtures', league=1, season=2026, status='FT')
print("errors:", f.get('errors'), "| results:", f.get('results'))
fixtures = f.get('response', [])
if fixtures:
    fx = max(fixtures, key=lambda x:(x['goals']['home'] or 0)+(x['goals']['away'] or 0))
    fid = fx['fixture']['id']
    print(f"  Ex: {fx['teams']['home']['name']} {fx['goals']['home']}-{fx['goals']['away']} {fx['teams']['away']['name']} (fixture {fid})")

    # 3. evenimente (goluri + marcatori)
    print("\n=== 3. Marcatori (events) pentru acel meci ===")
    e = get('/fixtures/events', fixture=fid)
    print("errors:", e.get('errors'))
    for ev in e.get('response', []):
        if ev['type'] == 'Goal':
            print(f"  ⚽ {ev['time']['elapsed']}' {ev['player']['name']} ({ev['team']['name']}) [{ev['detail']}]")
