import re,html,json,hashlib,os,sys,email.utils
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fetch_imgs import get,save
from concurrent.futures import ThreadPoolExecutor
B=os.path.dirname(os.path.abspath(__file__))
F={'hindu':'The Hindu','toi':'Times of India','nie':'The New Indian Express','dtnext':'DT Next','hindufood':'The Hindu','indulge':'Indulge Express'}
NEEDCHN={'hindufood','indulge','dtnext'}
out=[]
for k,src in F.items():
    x=open(f'{B}/rss/{k}.xml',encoding='utf8',errors='ignore').read()
    for it in re.findall(r'<item>(.*?)</item>',x,re.S):
        g=lambda t:(re.search(rf'<{t}[^>]*>(.*?)</{t}>',it,re.S) or [None,''])[1]
        T=html.unescape(re.sub(r'<!\[CDATA\[|\]\]>','',g('title'))).strip()
        L=html.unescape(re.sub(r'<!\[CDATA\[|\]\]>','',g('link'))).strip()
        D=re.sub(r'<!\[CDATA\[|\]\]>','',g('description'))
        im=(re.search(r'<media:content[^>]*url="([^"]+)"',it) or re.search(r'<enclosure[^>]*url="([^"]+)"',it) or re.search(r'<media:thumbnail[^>]*url="([^"]+)"',it) or re.search(r'<img[^>]*src="([^"]+)"',html.unescape(D)) or [None,None])[1]
        pd=g('pubDate')
        try: d=email.utils.parsedate_to_datetime(pd.strip()).strftime('%Y-%m-%d')
        except Exception: d=None
        blob=(T+' '+html.unescape(re.sub('<[^>]+>','',D))+' '+L).lower()
        if k in NEEDCHN and 'chennai' not in blob: continue
        if not T or not L or not im or not d: continue
        tl=T.lower()
        topic='traffic' if re.search(r'traffic|diversion|road|flyover|bus|mtc|signal',tl) else 'metro' if re.search(r'metro|rain|cyclone|weather|flood|imd|monsoon|power cut|water',tl) else 'runs' if re.search(r'marathon|\brun\b|runners|fitness|cycl',tl) else 'openings' if re.search(r'new (cafe|restaurant|outlet|store)|opens|launch|opening',tl) else 'food' if re.search(r'food|cafe|café|restaurant|dish|menu|chef|biryani|dessert|coffee',tl) else 'city'
        out.append(dict(t=T,s=src,d=d,u=L,topic=topic,_im=html.unescape(im)))
seen=set();U=[]
for n in sorted(out,key=lambda n:n['d'],reverse=True):
    key=re.sub('[^a-z]','',n['t'].lower())[:50]
    if key in seen: continue
    seen.add(key);U.append(n)
def dl(n):
    h=hashlib.md5(n['u'].encode()).hexdigest()[:10];p=f'/Users/gayathri/zocket-tech/knowspot-ai/app/img/nw/{h}.jpg'
    try:
        if not os.path.exists(p): save(get(n['_im']),p,560)
        n['img']=f'img/nw/{h}.jpg'
    except Exception as e: n['img']=None
    n.pop('_im');return n
with ThreadPoolExecutor(6) as ex: U=[n for n in ex.map(dl,U) if n['img']]
json.dump(U,open(f'{B}/rss_news.json','w'),ensure_ascii=False,indent=0)
from collections import Counter
print(len(U),Counter(n['topic'] for n in U),Counter(n['s'] for n in U),U[0]['d'],U[-1]['d'])
