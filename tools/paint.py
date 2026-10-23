# Painted detail layers per theme, masked to texture regions; outputs overlay RGBA + final skins.
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
m=np.load('m.npy')  # written by recolor.py; gold,robe,hair,lips,dark,skin=m
S=2; W=512*S
def canvas(): return Image.new('RGBA',(W,W),(0,0,0,0))
def inmask(mask,thr=.6):
    ys,xs=np.where(mask>thr); return list(zip(xs,ys))
def walk(d,x,y,n,step,turn,col,w0,w1,jag=0):
    a=random.uniform(0,2*math.pi); pts=[(x*S,y*S)]
    for i in range(n):
        a+=random.uniform(-turn,turn)+(random.choice([-1,1])*jag if random.random()<.3 else 0)
        x+=math.cos(a)*step; y+=math.sin(a)*step; pts.append((x*S,y*S))
    for i in range(len(pts)-1):
        t=i/max(1,len(pts)-2); w=max(1,int((w0+(w1-w0)*t)*S))
        d.line([pts[i],pts[i+1]],fill=col,width=w)
def finish(img,glow,mask,glowcol_mult=1.0):
    im=img.resize((512,512),Image.LANCZOS)
    a=np.asarray(im).astype(np.float32)/255
    g=np.asarray(im.filter(ImageFilter.GaussianBlur(glow))).astype(np.float32)/255 if glow else np.zeros_like(a)
    a[...,3]*=mask; g[...,3]*=np.clip(mask*1.3,0,1)*glowcol_mult
    return a,g
def compose(base,a,g,add=True):
    rgb=base[...,:3].copy()
    if add: rgb=1-(1-rgb)*(1-g[...,:3]*g[...,3:4])        # screen glow
    else:   rgb=rgb*(1-g[...,3:4]*.5)+g[...,:3]*g[...,3:4]*.5
    rgb=rgb*(1-a[...,3:4])+a[...,:3]*a[...,3:4]
    return np.concatenate([np.clip(rgb,0,1),base[...,3:]],-1)
random.seed(7)
def layer(name):
    img=canvas(); d=ImageDraw.Draw(img); R=inmask(robe); K=inmask(skin); T=inmask(gold,.5); H=inmask(hair)
    if name=='Ember':   # glowing cracks on robe + sparks
        for _ in range(70): x,y=random.choice(R); walk(d,x,y,random.randint(6,14),4,.5,(255,150,50,230),1.6,.4,jag=.9)
        for _ in range(160): x,y=random.choice(R+K); r=random.uniform(.6,1.6)*S; d.ellipse([x*S-r,y*S-r,x*S+r,y*S+r],fill=(255,210,120,255))
        return img,3,robe+skin*.5,True
    if name=='Frost':   # branching rime crystals
        def br(x,y,a,L,dep):
            if dep==0 or L<2: return
            x2,y2=x+math.cos(a)*L,y+math.sin(a)*L; d.line([(x*S,y*S),(x2*S,y2*S)],fill=(235,250,255,235),width=max(1,int(dep*.6*S)))
            br(x2,y2,a,L*.7,dep-1); br(x2,y2,a+1.05,L*.45,dep-1); br(x2,y2,a-1.05,L*.45,dep-1)
        for _ in range(45): x,y=random.choice(R); br(x,y,random.uniform(0,6.3),random.uniform(6,12),4)
        return img,2,robe+skin*.35,True
    if name=='Void':    # glyph runes
        for _ in range(55):
            x,y=random.choice(R+T); s=random.uniform(3,5); pts=[(x+random.randint(-1,1)*s,y+random.randint(-1,1)*s) for _ in range(4)]
            d.line([(px*S,py*S) for px,py in pts],fill=(200,140,255,240),width=int(1.2*S),joint='curve')
        for _ in range(40): x,y=random.choice(K); walk(d,x,y,10,3,.6,(150,90,255,170),1.2,.3)
        return img,4,robe+skin*.6+gold,True
    if name=='Radiant': # gold filigree curls
        for _ in range(55):
            x,y=random.choice(R); r0=random.uniform(4,9); a0=random.uniform(0,6.3); sgn=random.choice([-1,1]); pts=[]
            for i in range(40): t=i/39; r=r0*(1-t*.85); a=a0+sgn*t*4.5; pts.append(((x+math.cos(a)*r)*S,(y+math.sin(a)*r)*S))
            d.line(pts,fill=(255,220,130,235),width=int(1.1*S),joint='curve')
        return img,3,robe,True
    if name=='Blood':   # drips + veins
        for _ in range(60):
            x,y=random.choice(R); L=random.uniform(8,26); w=random.uniform(1,2.4)
            d.line([(x*S,y*S),(x*S,(y+L)*S)],fill=(70,0,8,235),width=int(w*S)); r=w*1.1*S; d.ellipse([x*S-r,(y+L)*S-r,x*S+r,(y+L)*S+r],fill=(90,0,10,240))
            d.line([((x-w*.25)*S,y*S),((x-w*.25)*S,(y+L*.6)*S)],fill=(200,60,60,120),width=max(1,int(.5*S)))
        for _ in range(50): x,y=random.choice(K); walk(d,x,y,9,3,.7,(120,20,30,150),1,.3)
        return img,0,robe+skin,False
    if name=='Spectral':# flowing wisps
        for _ in range(50):
            x,y=random.choice(R+K); a=random.uniform(0,6.3); f=random.uniform(.2,.4); A=random.uniform(2,4); pts=[]
            for i in range(30):
                u=i*1.3; px=x+math.cos(a)*u-math.sin(a)*math.sin(u*f)*A; py=y+math.sin(a)*u+math.cos(a)*math.sin(u*f)*A; pts.append((px*S,py*S))
            d.line(pts,fill=(190,255,240,200),width=int(1*S),joint='curve')
        return img,3,robe+skin*.7,True
out={}
for n in ['Ember','Frost','Void','Radiant','Blood','Spectral']:
    img,glow,mask,add=layer(n); mask=np.clip(mask,0,1)
    a,g=finish(img,glow,mask)
    base=np.asarray(Image.open(f'Banshee{n}.png').convert('RGBA')).astype(np.float32)/255
    res=compose(base,a,g,add)
    Image.fromarray((res*255+.5).astype(np.uint8)).save(f'Painted{n}.png')
    # overlay for viewer: premultiplied-ish single RGBA (glow+strokes over transparent)
    ov=np.zeros_like(a); 
    ga=g[...,3:4]*(1 if add else .5); ov[...,:3]=a[...,:3]*a[...,3:4]+g[...,:3]*ga*(1-a[...,3:4]); ov[...,3:4]=np.clip(a[...,3:4]+ga*(1-a[...,3:4]),0,1)
    ov[...,:3]=np.where(ov[...,3:4]>1e-4,ov[...,:3]/np.maximum(ov[...,3:4],1e-4),0)
    Image.fromarray((np.clip(ov,0,1)*255+.5).astype(np.uint8)).save(f'Overlay{n}.png')
sh=Image.new('RGB',(768,512),(30,30,34))
for i,n in enumerate(['Ember','Frost','Void','Radiant','Blood','Spectral']):
    im=Image.open(f'Painted{n}.png').resize((256,256)); bg=Image.new('RGBA',(256,256),(30,30,34,255)); bg.alpha_composite(im); sh.paste(bg.convert('RGB'),((i%3)*256,(i//3)*256))
sh.save('painted_sheet.png')
