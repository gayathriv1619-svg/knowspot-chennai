import json, glob, math, os
D = os.path.dirname(os.path.abspath(__file__))
LO0, LO1, LA0, LA1 = 80.02, 80.33, 12.82, 13.25
W, H = round((LO1 - LO0) * 51286), round((LA1 - LA0) * 52632)
def P(lat, lon): return ((lon - LO0) / (LO1 - LO0) * W, (LA1 - lat) / (LA1 - LA0) * H)
def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
    i, dm = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dm: i, dm = k, d
    return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps) if dm > eps else [a, b]
def path(ways, eps, close=False):
    out = []
    for g in ways:
        pts = dp([P(p['lat'], p['lon']) for p in g], eps)
        if len(pts) < 2: continue
        s = 'M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in pts)
        out.append(s + ('Z' if close else ''))
    return ''.join(out)
def load(f):
    try: return json.load(open(f))['elements']
    except Exception: return []
main = list({e['id']: e for f in [f'{D}/main.json'] + glob.glob(f'{D}/mainT_*.json') for e in load(f)}.values()); nat = load(f'{D}/nat.json')
res = list({e['id']: e for f in glob.glob(f'{D}/res_*.json') for e in load(f)}.values())
MAJ = ('motorway', 'trunk', 'primary', 'motorway_link', 'trunk_link', 'primary_link')
major = [e['geometry'] for e in main if e['tags'].get('highway') in MAJ and 'geometry' in e]
sec = [e['geometry'] for e in main if e['tags'].get('highway') not in MAJ and 'geometry' in e]
minor = [e['geometry'] for e in res if 'geometry' in e]
t = lambda e, k, v: e.get('tags', {}).get(k) == v
park = [e['geometry'] for e in nat if t(e, 'leisure', 'park') and 'geometry' in e]
water = [e['geometry'] for e in nat if t(e, 'natural', 'water') and 'geometry' in e]
beach = [e['geometry'] for e in nat if t(e, 'natural', 'beach') and 'geometry' in e]
river = [e['geometry'] for e in nat if e.get('tags', {}).get('waterway') in ('river', 'canal') and 'geometry' in e]
rail = [e['geometry'] for e in nat if t(e, 'railway', 'rail') and 'geometry' in e]
coast = [p for e in nat if t(e, 'natural', 'coastline') and 'geometry' in e for p in e['geometry']]
cp = sorted({(round(x), round(y)) for x, y in (P(p['lat'], p['lon']) for p in coast) if x > W * 0.55 and -50 < y < H + 50}, key=lambda q: q[1])
# keep the most-seaward point per 40px band so the shoreline is one clean line
band = {}
for x, y in cp:
    b = y // 40
    if b not in band or x > band[b][0]: band[b] = (x, y)
cp = [band[b] for b in sorted(band)]
sea = ('M' + 'L'.join(f'{x} {y}' for x, y in cp) + f'L{W + 400} {cp[-1][1]}L{W + 400} {cp[0][1]}Z') if cp else ''
# road labels: longest piece per named road
best = {}
for e in main:
    n = e['tags'].get('name:en') or e['tags'].get('name')
    if not n or 'geometry' not in e or not any(c.isascii() and c.isalpha() for c in n): continue
    g = [P(p['lat'], p['lon']) for p in e['geometry']]
    L = sum(math.hypot(g[k + 1][0] - g[k][0], g[k + 1][1] - g[k][1]) for k in range(len(g) - 1))
    kind = 'major' if e['tags'].get('highway') in MAJ else 'sec'
    best.setdefault(n, []).append((L, g, kind))
labels = []
for n, L in best.items():
    L.sort(key=lambda z: -z[0])
    for ln, g, kind in L[:2]:
        if ln < 220: continue
        m = len(g) // 2; a, b = g[max(0, m - 1)], g[min(len(g) - 1, m)]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        labels.append([n, round((a[0] + b[0]) / 2), round((a[1] + b[1]) / 2), round(ang, 1), kind])
M = dict(W=W, H=H, bbox=[LO0, LO1, LA0, LA1], sea=sea, major=path(major, 3), sec=path(sec, 3.5), minor=path(minor, 5),
         park=path(park, 4, True), water=path(water, 4, True), river=path(river, 4), rail=path(rail, 4), beach=path(beach, 4, True), labels=labels)
json.dump(M, open(f'{D}/../ev/map3_clean.json', 'w'), separators=(',', ':'))
print(W, H, {k: len(v) for k, v in M.items() if isinstance(v, (str, list))}, os.path.getsize(f'{D}/../ev/map3_clean.json') // 1024, 'KB')
