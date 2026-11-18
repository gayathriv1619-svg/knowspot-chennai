import json,subprocess,re,urllib.parse,time,os,io
from PIL import Image
UA='KnowSpotPrototype/1.0 (prototype)'
def curl(u,out=None):
    a=['curl','-s','-A',UA,'--max-time','120',u]+(['-o',out] if out else [])
    r=subprocess.run(a,capture_output=True);return r.stdout
def info(t,w=None):
    p={'action':'query','titles':t,'prop':'imageinfo','iiprop':'url|extmetadata','format':'json'}
    if w: p['iiurlwidth']=w
    d=json.loads(curl('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)));ii=list(d['query']['pages'].values())[0]['imageinfo'][0];m=ii['extmetadata']
    return ii,dict(t=t.replace('File:',''),a=re.sub('<[^>]+>','',m.get('Artist',{}).get('value',''))[:80].strip(),l=m.get('LicenseShortName',{}).get('value',''),u=ii['descriptionurl'])
SND={'waves':'File:Sea waves.wav','koel':'File:Eudynamys scolopaceus - Asian Koel XC476378.mp3','crow':'File:House Crow From Kuniyan Wetlands, Kerala 220507-000.wav','bell':'File:Bell-ring.flac'}
IMG={'pondy':'File:Pondy Bazaar 01.jpg','pondy2':'File:Diwali Urban Shopping, Thiyagaraja Nagar, Chennai.jpg','jasmine':'File:Chennai jasmine vendor.jpg','mylapore':'File:Mylapore tank at dawn panorama.jpg','mylapore2':'File:Kabalieswarar East Tank Street, Mylapore.jpg','elliot':'File:Elliots Beach at Besant Nagar, Chennai.JPG','besantroad':'File:Besant Nagar Beach Road.JPG','marina':'File:Marina Beach in Chennai.jpg','semmozhi':'File:Semmozhi poonga.jpg','ts':'File:Adyar TG.jpg','tower':'File:Anna Nagar Tower Park Night View from Lake.JPG','nrp':'File:Nageswara Rao Park 1.jpg','georgetown':'File:India - Chennai - Georgetown area 1 (3058689547).jpg'}
meta={}
for k,t in list(SND.items())+list(IMG.items()):
    try:
        ii,m=info(t,1280 if k in IMG else None)
        if k in IMG:
            raw=curl((ii.get('thumburl') or ii['url']).split('?')[0])
            im=Image.open(io.BytesIO(raw)).convert('RGB')
            if im.width>1280: im=im.resize((1280,round(im.height*1280/im.width)))
            im.save(f'/Users/gayathri/zocket-tech/knowspot-ai/app/img/wk/{k}.jpg','JPEG',quality=80,optimize=True,progressive=True);m['file']=f'img/wk/{k}.jpg'
        else:
            url=ii['url'].split('?')[0];ext=url.rsplit('.',1)[1]
            if not os.path.exists(f'snd/{k}.{ext}') or os.path.getsize(f'snd/{k}.{ext}')<1000: curl(url,f'snd/{k}.{ext}')
            m['raw']=f'snd/{k}.{ext}'
        meta[k]=m;print('ok',k,flush=True);time.sleep(1)
    except Exception as e: print('fail',k,str(e)[:80],flush=True);time.sleep(3)
json.dump(meta,open('commons_meta.json','w'),indent=1);print('done',len(meta))
