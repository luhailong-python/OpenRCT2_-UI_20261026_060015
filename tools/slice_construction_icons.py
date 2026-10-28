from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
from slice_assets import components,export,ROOT
source='tracktools-native.png';im=Image.open(ROOT/'assets/masters'/source).convert('RGBA');a=np.asarray(im)
groups=components(a[:,:,3]>100);centers=[(x,y) for y in (180,480,790,1080) for x in (170,478,786,1098)];buckets=[[] for _ in centers]
names=['track_straight','track_curve_left','track_curve_right','track_s_bend','track_up','track_down','track_bank_left','track_bank_right','track_brake','track_booster','track_station','track_seat_angle','track_entrance','track_exit','track_previous','track_next']
for g in groups:
 if g['area']<30:continue
 l,t,r,b=g['bbox'];cx=(l+r)/2;cy=(t+b)/2
 k=min(range(16),key=lambda i:(cx-centers[i][0])**2+(cy-centers[i][1])**2)
 buckets[k].append(g)
manifest=[]
for i,name in enumerate(names):
 assert buckets[i],name
 rec=export(source,buckets[i],name,'construction-icons',canvas=(352,352))
 rec['targetWindow']='RideConstruction';rec['usage']='轨道建设工具按钮/特殊段列表/方向与角度选项；图标非世界轨道图块'
 rec['nativeDetailIncreased']=False;manifest.append(rec)
(ROOT/'assets/construction-icon-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(1408,1568),'#eee8d8');d=ImageDraw.Draw(sheet);f=ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKsc-Regular.otf'),18)
for i,m in enumerate(manifest):
 pic=Image.open(ROOT/m['file']);x=i%4*352;y=i//4*392;sheet.paste(pic,(x,y),pic);d.text((x+15,y+358),m['name'],font=f,fill='#173e35')
sheet.save(ROOT/'previews/construction-icons-contact.jpg',quality=93)
print('16 native-detail transparent construction UI icons exported.')
