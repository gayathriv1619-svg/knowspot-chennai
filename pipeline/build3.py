import json, re, base64, math, os, html
os.chdir(os.path.dirname(os.path.abspath(__file__)))

AREAS = {
 'besant-nagar': ('Besant Nagar', 'பெசன்ட் நகர்', 13.0002, 80.2668),
 'adyar': ('Adyar', 'அடையார்', 13.0067, 80.2570),
 'mylapore': ('Mylapore', 'மயிலாப்பூர்', 13.0336, 80.2687),
 'alwarpet': ('Alwarpet', 'ஆழ்வார்பேட்டை', 13.0339, 80.2540),
 'teynampet': ('Teynampet', 'தேனாம்பேட்டை', 13.0405, 80.2503),
 'nungambakkam': ('Nungambakkam · KNK Rd', 'நுங்கம்பாக்கம்', 13.0604, 80.2420),
 't-nagar': ('T. Nagar', 'தி. நகர்', 13.0418, 80.2341),
 'anna-nagar': ('Anna Nagar', 'அண்ணா நகர்', 13.0850, 80.2101),
 'marina': ('Marina · Triplicane', 'மெரினா', 13.0500, 80.2824),
 'guindy': ('Guindy · IITM', 'கிண்டி', 13.0067, 80.2206),
}
def near(lat, lon):
    return min(AREAS, key=lambda k: math.hypot((lat-AREAS[k][2])*111, (lon-AREAS[k][3])*108))
def dist(lat, lon, k):
    return math.hypot((lat-AREAS[k][2])*111, (lon-AREAS[k][3])*108)


# ---------- all Chennai localities (OSM place nodes) ----------
import unicodedata
def slug(n): return re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-')
LOCS = json.load(open('../locs.json'))
_orig_names = {v[0].split(' · ')[0].lower() for v in AREAS.values()}
for n, la, lo, ta in LOCS:
    k = slug(n)
    if k in AREAS or n.lower() in _orig_names: continue
    AREAS[k] = (n, ta or '', round(la, 5), round(lo, 5))
_AK = list(AREAS)
def nearest_loc(lat, lon): return min(_AK, key=lambda k: (AREAS[k][2]-lat)**2 + ((AREAS[k][3]-lon)*.97)**2)

news = json.load(open('news.json'))
def nlink(sub):
    for k in news:
        for i in news[k]:
            if sub.lower() in i['title'].lower():
                return i
    raise SystemExit('missing news ' + sub)
def ndate(i):
    m = re.search(r'(\d{2}) (\w{3}) (\d{4})', i['date']); return f"{m.group(3)}-{ {'Oct':'10','Nov':'11','Sep':'09'}[m.group(2)] }-{m.group(1)}"
def nsrc(i):
    return i['src'] or i['title'].rsplit(' - ', 1)[-1]
def ntitle(i):
    return i['title'].rsplit(' - ', 1)[0]

ITEMS = []
APP = '/Users/gayathri/zocket-tech/knowspot-ai/app'
AEM = json.load(open('../ae_more.json'))
def dom(u): return u.split('/')[2].replace('www.', '')
EVIMG = {k: v for k, v in json.load(open('evimg/map.json')).items() if v and os.path.exists(v) and os.path.getsize(v) > 3000}
PLIMG = {k: v for k, v in json.load(open('plimg/map.json')).items() if v and os.path.exists(v) and os.path.getsize(v) > 3000}
POI_TAGS = {f"{e['type']}/{e['id']}": e.get('tags', {}) for e in json.load(open('pois.json'))['elements']}
EXTRA_IMG = {}
def add(**k):
    k.setdefault('moods', []); ITEMS.append(k)

# ---------- events: Meetup ----------
mu = json.load(open('meetup.json'))
mu_meta = {
 'Nexus AI Exchange: Chennai': ('tech', 'meetup', None, 'Venue to be announced', None),
 'The Autonomous Cloud Era': ('tech', 'meetup', None, 'See Meetup listing', None),
 'Grafana & Friends Chennai: In-Person Meetup': ('tech', 'meetup', None, 'ZoomInfo, Chennai (venue partner)', None),
 'Workshop: Become a Senior AI Engineer': ('tech', 'meetup', None, 'See Meetup listing', None),
 'TECHNOLOGY LEADERSHIP FORUM - 2026': ('tech', 'meetup', None, 'Invite-only · see listing', None),
 'THE FREELANCE BLUEPRINT – One Day Practical Freelancing Workshop': ('tech', 'meetup', None, 'IITM Research Park, Chennai', (12.9909, 80.2430)),
 'November meetup': ('tech', 'meetup', None, 'See Meetup listing', None),
 'A DATE WITH THE RAIN': ('wellness', 'semmozhi', None, 'See Meetup listing', None),
}
for i, e in enumerate(mu):
    cat, img, _, venue, geo = mu_meta[e['title']]
    fee = e['fee']
    price = f"₹{fee['amount']:,}" if fee else 'Free'
    desc = re.sub(r'\*\*|\\', '', e['desc'])
    desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)
    desc = re.split(r'\n\s*\n', desc.strip())
    desc = ' '.join(p.strip() for p in desc[:3])[:420]
    d = e['dt'][:10]; t = e['dt'][11:16]
    it = dict(id=f'mu{i}', type='event', cat=cat, title=e['title'].title() if e['title'].isupper() else e['title'],
              date=d, time=t, venue=venue, price=price, going=e['rsvps'], host=e['group'], url=e['url'],
              src='Meetup', desc=desc, img=img,
              moods=['nerdy'] if cat == 'tech' else ['chill'])
    if os.path.exists(f'{APP}/img/ev/mu{i}.jpg'): it['img'] = f'img/ev/mu{i}.jpg'; it['photo'] = dict(t='Event cover from the organiser', s='meetup.com', u=e['url'])
    else: it['img'] = None
    if geo:
        it.update(lat=geo[0], lon=geo[1], area=near(*geo))
    else:
        it['area'] = None
    ITEMS.append(it)

# ---------- events: allevents ----------
ae = json.load(open('allevents.json'))
DROP = ['Secure Your Spot', 'Study Abroad', 'Entrance Examination', 'Dubai Property', "Master's Fair", 'Inter School', 'Microsoft Ignite', 'Right to INR']
def classify(n):
    l = n.lower()
    if any(w in l for w in ['marathon', ' run ']) or l.endswith(' run 2026') or 'neon run' in l: return 'run', 'marathon', ['energetic']
    if ' fc' in l: return 'sport', 'football', ['energetic']
    if 'pickleball' in l: return 'sport', 'pickle', ['energetic']
    if 'bharat' in l: return 'dance', 'bharata', ['arty']
    if any(w in l for w in ['stand up', 'comedy', 'kahanibaaz', 'foodie dhaan', 'bunty', 'thinking & doing', 'munawar', 'retired not hurt']): return 'comedy', 'comedy', ['arty', 'chill']
    if re.search(r'\bai\b', l) or any(w in l for w in ['generative', 'networking', 'summit']): return 'tech', 'meetup', ['nerdy']
    if 'drawing' in l: return 'family', 'dakshina', ['chill']
    if any(w in l for w in ['epic', 'aadi anant', 'discourse']): return 'theatre', 'dakshina', ['arty']
    if any(w in l for w in ['classical', 'mandolin', 'devotional', 'hara hara', 'bharathikku', 'sruthi']): return 'music', 'concert', ['chill', 'arty']
    return 'music', 'gig', ['energetic']
for i, e in enumerate(ae):
    if any(x in e['name'] for x in DROP): continue
    lat = float(e['geo']['latitude']); lon = float(e['geo']['longitude'])
    cat, img, moods = classify(e['name'])
    name = e['name'].replace(' - Copy', '')
    if name.isupper() or sum(c.isupper() for c in name) > len(name) * .6:
        name = ' '.join(w if w in ('FC', 'AI', 'KYN', 'SPB', 'NCPA', 'VS', 'MJ', 'U', '25') else w.capitalize() for w in name.split())
        name = name.replace(' Vs ', ' vs ')
    venue = (e['venue'] or '').replace(': Chennai', '')
    k = near(lat, lon)
    st = (AEM.get(str(i)) or {}).get('start') or e['start']
    add(id=f'ae{i}', type='event', cat=cat, title=name, date=st[:10], time=st[11:16] if len(st) > 10 else None, end=((AEM.get(str(i)) or {}).get('end') or '')[:16], venue=venue or 'See listing',
        price='See listing', going=None, host=None, url=e['url'], src='allevents.in', desc='', img=img,
        lat=lat, lon=lon, area=k if dist(lat, lon, k) < 4 else None, moods=moods)
    ITEMS[-1]['img'] = f'img/ev/ae{i}.jpg' if os.path.exists(f'{APP}/img/ev/ae{i}.jpg') else None
    ITEMS[-1]['photo'] = dict(t='Event cover from the organiser', s='allevents.in', u=e['url'])

# ---------- extra events: district.in + allevents categories (17 Nov) ----------
for e in json.load(open('../new_events.json')):
    e = dict(e); e['area'] = near(e['lat'], e['lon']) if dist(e['lat'], e['lon'], near(e['lat'], e['lon'])) < 4 else None
    e['photo'] = dict(t='Event cover from the organiser', s=e['src'], u=e['url'])
    if not e.get('desc'): e['desc'] = ''
    ITEMS.append(e)

# ---------- new openings & food trends (from dated news) ----------
OPEN = [
 ('Romancham', 'Romancham', 'Open-air cafe for coffee, Kerala-inspired food and dessert.', None, 'cafe', ['foodie', 'chill']),
 ('Atlas House', 'Atlas House', 'A former home turned into a Mediterranean restaurant.', None, 'adyar', ['foodie']),
 ('beachfront lounge Soak', 'Soak', 'New beachfront lounge serving cocktails with a sea breeze.', None, 'besant', ['chill']),
 ('cat café finds a new home', 'Cat café, new Besant Nagar home', "A popular cat café has moved into a bigger space in Besant Nagar.", 'besant-nagar', 'cat', ['chill']),
 ('Sucre et Sale', 'Sucre et Sale', 'French cuisine arrives in Anna Nagar.', 'anna-nagar', 'cafe', ['foodie']),
 ('Mediterranean brunch awaits', 'Mediterranean brunch, Alwarpet', 'A leisurely Mediterranean brunch at an Alwarpet restaurant.', 'alwarpet', 'brunch', ['foodie', 'chill']),
 ('taste of the Himalayas', 'Himalayan kitchen', 'Himalayan food with generous servings and pocket-friendly prices.', None, 'food', ['foodie']),
 ('cosy Chennai spot', 'Cosy spot for slow days', 'A new cosy spot built for slow days and creative bites.', None, 'cafe', ['chill']),
 ('experimental gelato', 'Gelateria Ciacco', 'Teynampet gelateria pairing experimental gelato flavours with comfort food. DT Next reports scoops inspired by Dindigul biryani, maanga oorugai and Tirunelveli halwa.', 'teynampet', 'gelato', ['foodie']),
]
for j, (key, name, desc, area, img, moods) in enumerate(OPEN):
    n = nlink(key)
    pm = json.load(open(f'{APP}/img/op/op{j}.jpg.json')) if os.path.exists(f'{APP}/img/op/op{j}.jpg') else None
    it = dict(id=f'op{j}', type='opening', cat='new', title=name, date=ndate(n), area=area, desc=desc, img=f'img/op/op{j}.jpg' if pm else None,
              photo=dict(t='Photo from the report', s=dom(pm['page']), u=pm['page']) if pm else None,
              src=nsrc(n), url=n['link'], headline=ntitle(n), moods=moods)
    if area:
        it['lat'], it['lon'] = AREAS[area][2] + (0.002 if j % 2 else -0.002), AREAS[area][3] + 0.001
        it['approx'] = True
    if name == 'Gelateria Ciacco':
        it.update(lat=13.0422, lon=80.2494, approx=False, address='532, Anna Salai, Teynampet', site='https://www.ciacco.in/',
                  extra=[dict(t='DT Next: Biryani, pickle and halwa in a scoop', u='https://www.dtnext.in/news/chennai/biryani-pickle-and-halwa-in-a-scoop-ciaccos-twist-on-gelato')])
    ITEMS.append(it)

# ---------- places from OSM ----------
pois = json.load(open('pois_clean.json'))
AMAP = {'Besant Nagar': 'besant-nagar', 'Adyar': 'adyar', 'Nungambakkam': 'nungambakkam', 'Alwarpet': 'alwarpet', 'Teynampet': 'teynampet', 'T. Nagar': 't-nagar', 'Mylapore': 'mylapore'}
seen = set()
for j, p in enumerate(pois):
    kind = {'cafe': 'cafe', 'ice_cream': 'dessert', 'bakery': 'bakery', 'restaurant': 'restaurant'}.get(p['k'], 'shop')
    key = (p['n'].lower(), p['a'])
    if key in seen: continue
    seen.add(key)
    oid = p['osm'].split('.org/')[1]; tg = POI_TAGS.get(oid, {})
    if not os.path.exists(f'{APP}/img/pl/pl{j}.jpg'): continue
    pm = json.load(open(f'{APP}/img/pl/pl{j}.jpg.json')); img = f'img/pl/pl{j}.jpg'; photo = dict(t='Photo found on the web', s=dom(pm['page']), u=pm['page'])
    web = tg.get('website'); ig = tg.get('contact:instagram') or tg.get('instagram')
    add(id=f'pl{j}', type='place', cat=kind, title=p['n'], area=AMAP[p['a']], lat=p['lat'], lon=p['lon'],
        cuisine=p['cu'].replace(';', ', ').replace('_', ' '), hours=p['h'], street=p['st'], url=p['osm'], src='OpenStreetMap', img=img, photo=photo, site=web, ig=ig,
        moods=['foodie'] if kind in ('restaurant', 'dessert', 'bakery') else ['chill'] if kind == 'cafe' else [])

# ---------- every cafe / bakery / dessert spot in greater Chennai (OSM) ----------
for c in json.load(open('../cafes_new.json')):
    p = f"{APP}/img/cf/{c['id']}.jpg"; pm = json.load(open(p + '.json')) if os.path.exists(p) else None
    add(id=c['id'], type='place', cat=c['k'], title=c['n'], area=None, lat=c['lat'], lon=c['lon'], cuisine=c['cu'].replace(';', ', ').replace('_', ' '),
        hours=c['h'], street=c['st'], url='https://www.openstreetmap.org/' + c['osm'], src='OpenStreetMap', img=f"img/cf/{c['id']}.jpg" if pm else None,
        photo=dict(t='Photo found on the web', s=dom(pm['page']), u=pm['page']) if pm else None, site=c.get('web'), ig=c.get('ig'), phone=c.get('ph'),
        moods=['foodie'] if c['k'] != 'cafe' else ['chill'])

# ---------- landmarks ----------
pv = json.load(open('pageviews.json'))
LM = [
 ('Marina_Beach', 'Marina Beach', 13.0500, 80.2824, 'marina'), ('Theosophical_Society_Adyar', 'Theosophical Society', 13.0108, 80.2620, 'adyar'),
 ('Ripon_Building', 'Ripon Building', 13.0823, 80.2731, 'ripon'), ('Arignar_Anna_Zoological_Park', 'Vandalur Zoo', 12.8792, 80.0819, 'semmozhi'),
 ('Government_Museum,_Chennai', 'Government Museum', 13.0697, 80.2564, 'ripon'), ('Pondy_Bazaar', 'Pondy Bazaar', 13.0418, 80.2380, 'tnagar'),
 ('Madras_Music_Academy', 'Music Academy', 13.0459, 80.2595, 'musicacad'), ('DakshinaChitra', 'DakshinaChitra', 12.8255, 80.2414, 'dakshina'),
 ('VGP_Universal_Kingdom', 'VGP Universal Kingdom', 12.9196, 80.2537, 'ecr'), ('Parthasarathy_Temple', 'Parthasarathy Temple', 13.0539, 80.2768, 'kapali'),
]
for j, (t, name, lat, lon, img) in enumerate(LM):
    add(id=f'lm{j}', type='landmark', cat='landmark', title=name, lat=lat, lon=lon, area=near(lat, lon) if dist(lat, lon, near(lat, lon)) < 3 else None,
        views=pv.get(t), url='https://en.wikipedia.org/wiki/' + t, src='Wikipedia pageviews, 16 Oct–15 Nov', img=f'img/lm/{img}.jpg', cimg=img, moods=['chill'])
add(id='lm_elliot', type='landmark', cat='landmark', title="Elliot's Beach", lat=12.9989, lon=80.2723, area='besant-nagar', views=None,
    url="https://en.wikipedia.org/wiki/Elliot%27s_Beach", src='Wikipedia', img='img/lm/besant.jpg', cimg='besant', moods=['chill'])
add(id='lm_kapali', type='landmark', cat='landmark', title='Kapaleeshwarar Temple', lat=13.0337, lon=80.2697, area='mylapore', views=None,
    url='https://en.wikipedia.org/wiki/Kapaleeshwarar_Temple', src='Wikipedia', img='img/lm/kapali.jpg', cimg='kapali', moods=['chill', 'arty'])

add(id='lm_kus', type='landmark', cat='landmark', title='Kathipara Urban Square', lat=13.0079, lon=80.2048, area='guindy', views=None,
    url='https://magzter.com/stories/Newspaper/The-New-Indian-Express/KATHIPARA-URBAN-SQUARE-INAUGURATED', src='The New Indian Express', img='img/lm/kathipara.jpg', cimg='kathipara', moods=['chill'],
    desc='Open public square under the Kathipara flyover, opened in December 2021, with food stalls, play areas, shops and a screen. No events are listed for it this week on Meetup, allevents or District, so check its Instagram for pop-ups.')
# ---------- run clubs ----------
rc1 = 'https://www.dtnext.in/news/chennai/the-new-sunday-ritual'
CLUBS = [
 ('Vamos Run Club', 'Started by Sathish Ashwin with Keerthana Rajendran and Santhosh Gunasekaran. Makes fitness less intimidating with games and challenges. Co-hosting the KYN x Vamos Half Marathon on 13 Dec.', rc1, 'DT Next'),
 ('Voko Run Club', 'Founded by Kavin Bharathi and Vedhanthan. Known for Run & Karaoke and Run & Paint sessions.', rc1, 'DT Next'),
 ('Chennai Runners', "The city's biggest club: 16 chapters and close to 3,000 active members.", 'https://www.dtnext.in/news/sports/inspiring-the-city-to-take-up-an-active-lifestyle-747764', 'DT Next'),
 ('Dream Runners', 'Structured club with 14 chapters across Chennai, including Besant Nagar and Marina. Sessions twice a week, year-round. Hosts the Hexaware Dream Runners Half Marathon.', 'https://fatmarathoner.com/hexaware-dream-runners-half-marathon/', 'Fat Marathoner'),
 ('ASICS Running Club', 'Launched alongside the Freshworks Chennai Marathon partnership, with group runs and coaching.', 'https://www.outlookbusiness.com/spotlight/pr-wire/asics-deepens-chennai-market-presence-through-partnership-with-freshworks-chennai-marathon-launches-asics-running-club', 'Outlook Business'),
]
for j, (n, d, u, s) in enumerate(CLUBS):
    add(id=f'rc{j}', type='club', cat='run', title=n, desc=d, url=u, src=s, img='img/lm/marathon.jpg', cimg='marathon', area=None, moods=['energetic'])

# ---------- stories (real articles) ----------
STORIES = [
 ('run clubs are getting the city moving', 'marathon'), ('transformation of ECR and OMR', 'ecr'), ('50 Best Restaurants in India', 'brunch'),
 ("coastline shapes community and art", 'besant'), ('kachoris, tiramisu and modak at 5 am', 'marathon'), ('IIT study unravels', 'metro'),
 ('Saravanna Bhavan', 'food'), ('Adyar Ananda Bhavan sells majority stake', 'food'),
]
for j, (k, img) in enumerate(STORIES):
    n = nlink(k)
    add(id=f'st{j}', type='story', cat='story', title=ntitle(n), date=ndate(n), src=nsrc(n), url=n['link'], img=None, area=None)
add(id='st_ciacco', type='story', cat='story', title="Biryani, pickle and halwa in a scoop: Ciacco's twist on gelato", date=None, src='DT Next',
    url='https://www.dtnext.in/news/chennai/biryani-pickle-and-halwa-in-a-scoop-ciaccos-twist-on-gelato', img=None, area='teynampet')

# ---------- alerts ----------
ALERTS = []
for key, kind, title, sub in [
    ("Chennai faces very heavy rain on Nov 18-19", 'storm', 'Cyclone Akvan: very heavy rain likely 18–19 Nov', 'Outdoor plans midweek may change. Check organisers before you head out.'),
    ('Chennai may receive evening showers', 'rain', 'Evening showers possible today', 'Heavy rain forecast in 15 Tamil Nadu districts.'),
    ('Traffic Diversion in Adambakkam', 'traffic', 'Traffic diversion in Adambakkam (from 11 Nov)', '5-day diversion. Check whether it has been lifted before driving.'),
    ('Post-festival pollution', 'air', 'Air quality: worst post-festival levels in three years', 'Consider an indoor run if you are sensitive.'),
]:
    n = nlink(key)
    ALERTS.append(dict(kind=kind, title=title, sub=sub, src=nsrc(n), date=ndate(n), url=n['link']))

# ---------- reels / hashtag feeds ----------
REELS = [
 ('besant-nagar', '#besantnagar', 'besantnagar', 'besant'), ('besant-nagar', '#elliotsbeach', 'elliotsbeach', 'besant'),
 ('nungambakkam', '#khadernawazkhanroad', 'khadernawazkhanroad', 'knk'), ('teynampet', '#chennaigelato', 'chennaigelato', 'gelato'),
 (None, '#chennaicafes', 'chennaicafes', 'coffee'), (None, '#chennairunners', 'chennairunners', 'marathon'),
 ('mylapore', '#mylapore', 'mylapore', 'kapali'), ('t-nagar', '#pondybazaar', 'pondybazaar', 'tnagar'),
 (None, '#chennaifoodie', 'chennaifoodie', 'food'), ('anna-nagar', '#annanagar', 'annanagar', 'cafe'),
]
REELS = [dict(area=a, tag=t, url=f'https://www.instagram.com/explore/tags/{u}/', img=i) for a, t, u, i in REELS]

# ---------- weather ----------
snap = json.load(open('../ks/snapshot.json'))
wd = snap['weather']['daily']
WEATHER = [dict(d=d, t=t, p=p) for d, t, p in zip(wd['time'], wd['temperature_2m_max'], wd['precipitation_sum'])]
WEATHER_NOW = snap['weather'].get('current', {})

for i in ITEMS:
    if i.get('lat'): i['area'] = nearest_loc(i['lat'], i['lon'])
NEWSIMG = json.load(open('../news_img.json')) if os.path.exists('../news_img.json') else {}
NEWS = []; _seen = set()
for topic, L in news.items():
    for n in L:
        t = ntitle(n)
        if t in _seen: continue
        _seen.add(t); NI = NEWSIMG.get(t) or {}
        NEWS.append(dict(t=t, s=nsrc(n), d=ndate(n), u=NI.get('page') or n['link'], topic=topic, img=NI.get('img') if NI.get('img') and os.path.exists(APP + '/' + NI['img']) else None))
RSSN = [n for n in json.load(open('../rss_news.json')) if n['d'] >= '2026-10-27'] if os.path.exists('../rss_news.json') else []
if RSSN: NEWS = RSSN
NEWS.sort(key=lambda x: x['d'], reverse=True)
WIN = {'w_elliot': [[5.5, 7.5], [17, 20]], 'w_marina': [[5.75, 7.5]], 'w_pondy': [[19, 22]], 'w_knk': [[17, 22]], 'w_mylapore': [[6, 8.5]], 'w_georgetown': [[7, 10]], 'w_tower': [[5.5, 8], [16, 19]], 'w_semmozhi': [[14, 17]], 'w_ts': [[8.5, 10]], 'w_thiru': [[17, 20]]}
CM = json.load(open('../commons_meta.json')) if os.path.exists('../commons_meta.json') else {}
WALKS = json.load(open('../walks.json')) if os.path.exists('../walks.json') else []
for w in WALKS:
    w['win'] = WIN.get(w['id'], [])
    m = CM.get(w['img'] or '')
    if m and m.get('file') and os.path.exists(APP + '/' + m['file']): w['img'] = m['file']; w['cr'] = (re.sub(r'This Image was created by User:', '', m.get('a') or 'Wikimedia Commons')[:34]).strip() + ', ' + m.get('l', '')
    elif w['id'] == 'w_knk' and os.path.exists(APP + '/img/wk/knk1.jpg'): w['img'] = 'img/wk/knk1.jpg'; w['cr'] = 'SilverKris (Singapore Airlines) article photo'
    else: w['img'] = None
# ---------- images / credits ----------
meta = json.load(open('img/meta.json'))
CREDITS = {}
for i in ITEMS:
    k = i.pop('cimg', None)
    if k: m = meta[k]; CREDITS[k] = dict(t=m['title'].replace('File:', ''), a=m['artist'], l=m['license'], u=m['page']); i['photo'] = dict(t='Wikimedia Commons: ' + (m['artist'] or 'unknown') + ', ' + m['license'] + '. Shows the area', s='commons.wikimedia.org', u=m['page'])
# ---------- routes & signals ----------
R = json.load(open('../routes.json')) if os.path.exists('../routes.json') else {}
SIG = []
if os.path.exists('../signals.json'):
    try: SIG = [(e['lat'], e['lon']) for e in json.load(open('../signals.json'))['elements']]
    except Exception: SIG = []
def near_sig(lat, lon, r=0.5): return sum(1 for a, b in SIG if abs(a-lat) < .01 and math.hypot((a-lat)*111, (b-lon)*108) < r)
def route_sig(g):
    n = 0; seen = set()
    for idx, (a, b) in enumerate(SIG):
        if idx in seen: continue
        for x, y in g[::2]:
            if abs(b-x) < .0006 and abs(a-y) < .0006: n += 1; seen.add(idx); break
    return n
for i in ITEMS:
    if i['type'] == 'event' and i.get('lat'):
        i['sig'] = near_sig(i['lat'], i['lon']) if SIG else None
        rr = {}
        for a in AREAS:
            r = R.get(a + '|' + i['id'])
            if r: rr[a] = [round(r['d']/1000, 1), round(r['t']/60), route_sig(r['g']) if SIG else None]
        if rr: i['rt'] = rr
MAP = json.load(open('map3_clean.json')) if os.path.exists('map3_clean.json') else json.load(open('map2_clean.json'))
DATA = dict(asof='2026-11-16T17:30:00+05:30', today='2026-11-16', areas={k: dict(n=v[0], ta=v[1], lat=v[2], lon=v[3]) for k, v in AREAS.items()},
            items=ITEMS, news=NEWS, walks=WALKS, hero={k: ((CM[k].get('a') or '')[:30] + ', ' + CM[k].get('l', '')) for k in CM if k.startswith('h_')}, sounds={k: CM[k] for k in ('waves', 'koel', 'crow', 'bell') if k in CM}, alerts=ALERTS, reels=REELS, weather=WEATHER, now=WEATHER_NOW, map=MAP, credits=CREDITS, nsig=len(SIG))
js = 'const D=' + json.dumps(DATA, ensure_ascii=False, separators=(',', ':')) + ';'
open('data.js', 'w').write(js)
from collections import Counter
print(len(ITEMS), Counter(i['type'] for i in ITEMS), len(js)//1024, 'KB', 'noimg', [i['id'] for i in ITEMS if not i.get('img') and i['type'] not in ('story',)], 'routes', sum(1 for i in ITEMS if i.get('rt')), 'sig', len(SIG))
