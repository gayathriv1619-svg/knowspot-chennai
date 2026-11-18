import json,re,html,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fetch_imgs import get,save
from concurrent.futures import ThreadPoolExecutor
os.chdir(os.path.dirname(os.path.abspath(__file__)))
ae=json.load(open('ev/allevents.json'))
def one(a):
    i,e=a; out={}
    try:
        p=get(e['url']).decode('utf8','ignore')
        m=re.search(r'property="og:image"\s+content="([^"]+)"',p) or re.search(r'content="([^"]+)"\s+property="og:image"',p)
        sd=re.findall(r'"startDate"\s*:\s*"([^"]+)"',p); out['start']=sd[0] if sd else None
        ed=re.findall(r'"endDate"\s*:\s*"([^"]+)"',p); out['end']=ed[0] if ed else None
        if m:
            u=html.unescape(m.group(1)); out['img']=u; save(get(u),f'/Users/gayathri/zocket-tech/knowspot-ai/app/img/ev/ae{i}.jpg',1100)
    except Exception as ex: out['err']=str(ex)[:80]
    return i,out
res={}
with ThreadPoolExecutor(6) as ex:
    for i,o in ex.map(one,list(enumerate(ae))): res[i]=o; print(i,o.get('start'),'ERR '+o['err'] if 'err' in o else '',flush=True)
json.dump(res,open('ae_more.json','w'),indent=0)
