import json, re, os, sys, html, io, time, hashlib, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import ssl
try:
    import certifi; CTX=ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX=ssl._create_unverified_context()
EV='ev'; OUT='/Users/gayathri/zocket-tech/knowspot-ai/app/img'
UA={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36','Accept-Language':'en-IN,en;q=0.9'}
BAD=('gettyimages','shutterstock','alamy','dreamstime','istockphoto','123rf','depositphotos','vectorstock','freepik','stock.adobe','pngtree','clipart','logo','vecteezy','wikimedia','pinimg','youtube','ytimg','magicbricks','housing.com','indiamart','tradeindia','slideserve','hexahealth','cornucopia.ie','behance','kabilaifarm','msn.com','exportersindia','hervoguelife','hidubai','shriramfinance','chintamanialchemi','timesofindia','gettonews','shopee','realestate','happybumco','reebok.com')
def get(u,t=20):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=t,context=CTX).read()
def save(data,path,w=960):
    im=Image.open(io.BytesIO(data)); im=im.convert('RGB')
    if im.width<380 or im.height<240: raise ValueError('small %s'%(im.size,))
    r=im.width/im.height
    if r<0.55 or r>2.4: raise ValueError('ratio')
    if im.width>w: im=im.resize((w,int(w/r)),Image.LANCZOS)
    im.save(path,'JPEG',quality=78,optimize=True,progressive=True); return im.size
def bing(q):
    h=get('https://www.bing.com/images/search?'+urllib.parse.urlencode({'q':q,'form':'HDRSC2','first':1,'qft':'+filterui:imagesize-medium'})).decode('utf8','ignore')
    out=[]
    for m in re.finditer(r'class="iusc"[^>]*m="([^"]+)"',h):
        try: j=json.loads(html.unescape(m.group(1)))
        except Exception: continue
        mu,pu=j.get('murl',''),j.get('purl','')
        if any(b in (mu+pu).lower() for b in BAD): continue
        out.append((mu,pu,j.get('t','')))
    return out
def one(job):
    key,q,path=job[:3]
    must=job[3] if len(job)>3 else []
    if os.path.exists(path): return key,json.load(open(path+'.json'))
    try: cands=bing(q)
    except Exception as e: return key,{'err':str(e)}
    tried=[]
    def norm(x): return re.sub(r'[^a-z0-9]','',urllib.parse.unquote(x).lower())
    def score(c):
        blob=norm(c[1]+' '+c[2]+' '+c[0])
        nm=all(norm(w) in blob for w in must) if must else True
        loc=any(w in blob for w in ('chennai','madras','tamilnadu','besant','adyar','mylapore','nungambakkam','alwarpet','teynampet','tnagar','annanagar','zomato','magicpin','justdial','foursquare','instagram','facebook','fbsbx','swiggy','tripadvisor','dineout','eazydiner'))
        return (2 if nm and loc else 1 if nm else 0)
    cands=sorted([c for c in cands if score(c)>0],key=lambda c:-score(c))
    for mu,pu,t in cands[:8]:
        try:
            sz=save(get(mu,15),path)
            meta={'murl':mu,'page':pu,'title':t,'q':q,'size':sz,'alts':[c[:2] for c in cands[:8] if c[0]!=mu][:4]}
            json.dump(meta,open(path+'.json','w')); return key,meta
        except Exception as e: tried.append(str(e)[:40])
    return key,{'err':'none ok','tried':tried,'n':len(cands)}
if __name__=='__main__':
    jobs=json.load(open(sys.argv[1]))
    res={}
    with ThreadPoolExecutor(6) as ex:
        for k,m in ex.map(one,jobs):
            res[k]=m; print(k,'ERR' if 'err' in m else m['page'][:80],flush=True)
    json.dump(res,open(sys.argv[2],'w'),indent=0)
