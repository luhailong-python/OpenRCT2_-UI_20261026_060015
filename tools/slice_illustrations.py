from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from collections import deque
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/masters/illustrations-native.png'
img=Image.open(SOURCE).convert('RGBA')
names=['dragon_coaster','celestial_wheel','gourd_carousel','bamboo_flume','cloud_train','hedge_maze','tea_keeper','mechanic','cleaner','mountain_scenario','lake_scenario','achievement_trophy']
w,h=img.size; alpha=img.getchannel('A'); bits=bytearray(v>40 for v in alpha.tobytes());parts=[]
for start in range(w*h):
    if not bits[start]: continue
    bits[start]=0;q=deque([start]);pixels=[];l=w;t=h;r=b=0
    while q:
        z=q.popleft();pixels.append(z);x=z%w;y=z//w;l=min(l,x);r=max(r,x);t=min(t,y);b=max(b,y)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx=x+dx;yy=y+dy
            if 0<=xx<w and 0<=yy<h:
                j=yy*w+xx
                if bits[j]: bits[j]=0;q.append(j)
    if len(pixels)>20000:parts.append({'rect':(max(0,l-4),max(0,t-4),min(w,r+5),min(h,b+5)),'pixels':pixels,'cx':(l+r)/2,'cy':(t+b)/2})
assert len(parts)==12,len(parts)
parts.sort(key=lambda p:p['cy']);parts=sum([sorted(parts[i:i+3],key=lambda p:p['cx']) for i in range(0,12,3)],[])
out=ROOT/'assets/illustrations';out.mkdir(exist_ok=True)
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest();manifest=[]
for name,part in zip(names,parts):
    rect=part['rect']
    crop=img.crop(rect)
    # Isolate the selected connected silhouette and its original antialiasing;
    # no new painting and no opaque-background color keying.
    maskBytes=bytearray(w*h)
    for z in part['pixels']:maskBytes[z]=255
    mask=Image.frombytes('L',(w,h),bytes(maskBytes)).filter(ImageFilter.MaxFilter(7)).crop(rect)
    crop.putalpha(ImageChops.multiply(crop.getchannel('A'),mask))
    canvas=Image.new('RGBA',(440,440),(0,0,0,0))
    pos=((440-crop.width)//2,(440-crop.height)//2)
    canvas.alpha_composite(crop,pos)
    file=out/(name+'.png');canvas.save(file)
    rec={'file':file.relative_to(ROOT).as_posix(),'width':440,'height':440,'mode':'RGBA','sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'sourceRectXYXY':list(rect),'pivot':[.5,.5],'borderLeftBottomRightTop':[0,0,0,0],'spriteType':'Simple','operation':'connected_alpha_silhouette_crop_seed_alpha_gt40_mask_dilate3_keep_original_alpha_equal_canvas_no_scaling','excluded':'邻格碎片及断开的微小装饰碎片；没有重绘内容','nativeContentSize':[crop.width,crop.height],'derivedFrom':[{'file':SOURCE.relative_to(ROOT).as_posix(),'sha256':sha,'generationRecord':SOURCE.relative_to(ROOT).as_posix()+'.generation.json'}],'reviewStatus':'produced_pending_visual_review','usage':'界面卡面/详情插画，不是可运行世界精灵或动画'}
    Path(str(file)+'.source.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8');manifest.append(rec)
(ROOT/'assets/illustration-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(1320,1880),'#e8e3d4');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for i,m in enumerate(manifest):
    x=i%3*440;y=i//3*470
    sheet.paste(Image.open(ROOT/m['file']),(x,y),Image.open(ROOT/m['file']))
    d.text((x+20,y+435),names[i],font=font,fill='#214c3e')
sheet.save(ROOT/'previews/illustrations-contact.jpg',quality=91)
print('12 illustration crops saved with native coordinates and Alpha preserved.')
