from PIL import Image
from collections import deque
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);im=Image.open(p).convert('RGBA');w,h=im.size
a=bytearray(v>(int(sys.argv[2]) if len(sys.argv)>2 else 40) for v in im.getchannel('A').tobytes());parts=[]
for start in range(w*h):
 if not a[start]:continue
 a[start]=0;q=deque([start]);n=0;l=w;t=h;r=b=0
 while q:
  z=q.popleft();x=z%w;y=z//w;n+=1;l=min(l,x);r=max(r,x);t=min(t,y);b=max(b,y)
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   xx=x+dx;yy=y+dy
   if 0<=xx<w and 0<=yy<h:
    j=yy*w+xx
    if a[j]:a[j]=0;q.append(j)
 if n>100:parts.append({'n':n,'rect':[l,t,r+1,b+1]})
print(json.dumps(sorted(parts,key=lambda z:-z['n']),indent=2))
