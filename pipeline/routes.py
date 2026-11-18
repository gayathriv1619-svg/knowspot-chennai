import json,time,urllib.request,ssl,certifi,os
from concurrent.futures import ThreadPoolExecutor
CTX=ssl.create_default_context(cafile=certifi.where())
B=os.path.dirname(os.path.abspath(__file__))
AREAS={'besant-nagar':(13.0002,80.2668),'adyar':(13.0067,80.2570),'mylapore':(13.0336,80.2687),'alwarpet':(13.0339,80.2540),'teynampet':(13.0405,80.2503),'nungambakkam':(13.0604,80.2420),'t-nagar':(13.0418,80.2341),'anna-nagar':(13.0850,80.2101),'marina':(13.0500,80.2824),'guindy':(13.0067,80.2206)}
ae=json.load(open(B+'/ev/allevents.json'))
dests={f'ae{i}':(float(e['geo']['latitude']),float(e['geo']['longitude'])) for i,e in enumerate(ae)}
dests['mu5']=(12.9909,80.2430)
P=B+'/routes.json'
out=json.load(open(P)) if os.path.exists(P) else {}
def job(a):
    area,(lat,lon),k,(dl,dn)=a
    u=f'https://router.project-osrm.org/route/v1/driving/{lon},{lat};{dn},{dl}?overview=full&geometries=geojson'
    for t in range(4):
        try:
            r=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'knowspot-prototype'}),timeout=30,context=CTX).read())
            rt=r['routes'][0]; return area+'|'+k,dict(d=round(rt['distance']),t=round(rt['duration']),g=[[round(x,5),round(y,5)] for x,y in rt['geometry']['coordinates']])
        except Exception: time.sleep(2+t*2)
    return area+'|'+k,None
todo=[(a,v,k,d) for a,v in AREAS.items() for k,d in dests.items() if a+'|'+k not in out]
with ThreadPoolExecutor(5) as ex:
    for key,v in ex.map(job,todo):
        if v: out[key]=v
json.dump(out,open(P,'w')); print('done',len(out),'of',len(AREAS)*len(dests),flush=True)
