import numpy as np, colorsys, sys
SRC=sys.argv[1] if len(sys.argv)>1 else 'src/BansheeSkin.png'  # extract from your own client
from PIL import Image
src=np.asarray(Image.open(SRC).convert('RGBA')).astype(np.float32)/255
rgb,a=src[...,:3],src[...,3:]
mx=rgb.max(-1); mn=rgb.min(-1); v=mx; s=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]; d=np.maximum(mx-mn,1e-6)
h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
L=(0.2126*r+0.7152*g+0.0722*b)
def band(x,lo,hi,soft=12):
    return np.clip(np.minimum((x-lo)/soft+1,(hi-x)/soft+1),0,1)
def ss(x,e0,e1): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)
gold = band(h,20,60)*ss(s,0.25,0.45)
robe = band(h,250,345,20)*ss(s,0.06,0.16)
hair = band(h,165,215)*ss(s,0.35,0.55)*(1-ss(v,0.75,0.9))
lips = band(h,330,360,10)*ss(s,0.3,0.5)+band(h,-20,10,10)*ss(s,0.3,0.5)*(1-gold)
dark = (1-ss(v,0.18,0.35))*(1-gold)
skin = np.clip(1-gold-robe-hair-lips-dark,0,1)
np.save("m.npy",np.stack([gold,robe,hair,lips,dark,skin]))
masks=dict(gold=gold,robe=robe,hair=hair,lips=lips,dark=dark,skin=skin)
def hx(c): return np.array([int(c[i:i+2],16) for i in (1,3,5)],np.float32)/255
def gmap(Lx,stops):
    xs=[p for p,_ in stops]; cs=np.stack([hx(c) for _,c in stops])
    return np.stack([np.interp(Lx,xs,cs[:,k]) for k in range(3)],-1)
# per-region relative luminance so each region spans its gradient fully
def norm(m):
    w=m>0.5; 
    if w.sum()<10: return L
    lo,hi=np.percentile(L[w],2),np.percentile(L[w],99.5); return np.clip((L-lo)/(hi-lo),0,1)
NL={k:norm(m) for k,m in masks.items()}
THEMES={
 'Ember':  dict(skin=[(0,'#1e100c'),(.45,'#6a4034'),(.8,'#d9a98a'),(1,'#fff0d8')], robe=[(0,'#120404'),(.5,'#4a0e0a'),(.85,'#a3260f'),(1,'#ff8a3c')],
                hair=[(0,'#200300'),(.5,'#c2300a'),(1,'#ffcf4a')], gold=[(0,'#2b1205'),(.6,'#c6611c'),(1,'#ffe39a')], lips=[(0,'#1a0000'),(1,'#ff5a1a')], dark=[(0,'#050101'),(1,'#3a1208')]),
 'Frost':  dict(skin=[(0,'#0d2a44'),(.5,'#5d9cc7'),(.85,'#c6ecff'),(1,'#ffffff')], robe=[(0,'#06142b'),(.5,'#1f4f8a'),(.85,'#6fb3e8'),(1,'#e6f7ff')],
                hair=[(0,'#e9f8ff'),(.4,'#9fd8f5'),(1,'#ffffff')], gold=[(0,'#2d3a48'),(.6,'#a9bccc'),(1,'#ffffff')], lips=[(0,'#13325a'),(1,'#7fc7ff')], dark=[(0,'#02060d'),(1,'#1c3350')]),
 'Void':   dict(skin=[(0,'#06030c'),(.5,'#2a1a44'),(.85,'#6e4fa3'),(1,'#c4a8ff')], robe=[(0,'#030106'),(.5,'#14082a'),(.85,'#3d1a70'),(1,'#9b5cff')],
                hair=[(0,'#0a0014'),(.5,'#6a1fd0'),(1,'#e2c2ff')], gold=[(0,'#120a1e'),(.6,'#5a3e86'),(1,'#d7c2ff')], lips=[(0,'#0a0012'),(1,'#b84dff')], dark=[(0,'#000000'),(1,'#1a0f2a')]),
 'Radiant':dict(skin=[(0,'#4a3a22'),(.5,'#c8b38a'),(.85,'#fff2d2'),(1,'#ffffff')], robe=[(0,'#3a2a12'),(.5,'#d9c9a3'),(.85,'#fbf4e2'),(1,'#ffffff')],
                hair=[(0,'#6b4a12'),(.5,'#e8b84a'),(1,'#fff6c8')], gold=[(0,'#4a2e08'),(.6,'#f0b93a'),(1,'#fffbe0')], lips=[(0,'#5a2a10'),(1,'#f2a46a')], dark=[(0,'#2a1e10'),(1,'#7a5a2a')]),
 'Blood':  dict(skin=[(0,'#14080a'),(.5,'#5a3a40'),(.85,'#c8a4a6'),(1,'#f6e6e4')], robe=[(0,'#050001'),(.5,'#1c0306'),(.85,'#4a0a10'),(1,'#8a1a22')],
                hair=[(0,'#050102'),(.5,'#1e0a0e'),(1,'#5a2a30')], gold=[(0,'#1e0b06'),(.6,'#8a3a1a'),(1,'#e8a070')], lips=[(0,'#000000'),(1,'#3a0006')], dark=[(0,'#000000'),(1,'#2a0408')]),
 'Spectral':dict(skin=[(0,'#0a2a26'),(.5,'#48a89a'),(.85,'#b8fff0'),(1,'#ffffff')], robe=[(0,'#05201c'),(.5,'#2e8a7c'),(.85,'#9df5e2'),(1,'#f0fffb')],
                hair=[(0,'#d8fff6'),(.5,'#7ef0d8'),(1,'#ffffff')], gold=[(0,'#1a3a36'),(.6,'#7ac9bc'),(1,'#f4fffd')], lips=[(0,'#0a3a34'),(1,'#5effd8')], dark=[(0,'#00100e'),(1,'#16443e')]),
}
out={}
for name,t in THEMES.items():
    acc=np.zeros_like(rgb); wsum=np.zeros(L.shape)
    for k,m in masks.items():
        acc+=m[...,None]*gmap(NL[k],t[k]); wsum+=m
    wsum=np.clip(wsum,0,None)
    res=np.where(wsum[...,None]>1e-3, acc/np.maximum(wsum,1)[...,None]*np.minimum(wsum,1)[...,None] + (1-np.minimum(wsum,1))[...,None]*rgb, rgb)
    # keep a touch of original texture detail
    res=np.clip(res+0.25*(L-np.clip(L,0,1))[...,None],0,1)
    o=np.concatenate([res,a],-1); out[name]=o
    Image.fromarray((o*255+.5).astype(np.uint8),'RGBA').save(f'Banshee{name}.png')
# contact sheet incl original, on dark bg
names=['Original']+list(THEMES)
W=256; sheet=Image.new('RGB',(W*4,W*2),(30,30,34))
for i,n in enumerate(names):
    im=Image.open(SRC if n=='Original' else f'Banshee{n}.png').convert('RGBA').resize((W,W))
    bg=Image.new('RGBA',(W,W),(30,30,34,255)); bg.alpha_composite(im); sheet.paste(bg.convert('RGB'),((i%4)*W,(i//4)*W))
sheet.save('sheet.png')
# mask debug
Image.fromarray((np.stack([robe,gold,hair],-1)*255).astype(np.uint8)).resize((256,256)).save('masks.png')
