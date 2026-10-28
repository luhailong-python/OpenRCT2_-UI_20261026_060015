"""Deterministic crop/alpha isolation of native generated UI sheets; no painting."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'assets' / 'masters'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ranges(a):
    d = np.diff(np.r_[False, a, False].astype(np.int8))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))

def components(mask):
    """8-connected components via scanline union; returns runs and component bounds."""
    parents=[]; run_rows=[]; previous=[]
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    def union(a,b):
        a,b=find(a),find(b)
        if a != b: parents[b]=a
    for y,row in enumerate(mask):
        current=[]
        for x0,x1 in ranges(row):
            i=len(parents);parents.append(i);current.append((int(x0),int(x1),i))
            for a,b,j in previous:
                if b < x0: continue
                if a > x1: break
                union(i,j)
            run_rows.append((y,int(x0),int(x1),i))
        previous=current
    groups={}
    for y,x0,x1,i in run_rows:
        key=find(i)
        if key not in groups: groups[key]={'bbox':[x0,y,x1,y+1], 'area':0,'runs':[]}
        g=groups[key];b=g['bbox'];b[0]=min(b[0],x0);b[1]=min(b[1],y);b[2]=max(b[2],x1);b[3]=max(b[3],y+1)
        g['area']+=x1-x0;g['runs'].append((y,x0,x1))
    return sorted(groups.values(), key=lambda g:-g['area'])

def inspect():
    for filename in ('surfaces-native.png','controls-native.png','icons-native.png'):
        a=np.asarray(Image.open(MASTER/filename).convert('RGBA'))
        groups=components(a[:,:,3]>100)
        print(filename, [(g['bbox'],g['area']) for g in groups if g['area']>200])

NAMES = [
    'park_gate','roller_coaster','ferris_wheel','carousel','water_flume','miniature_train','hedge_maze','pirate_ship',
    'dumpling_shop','tea_shop','souvenir_shop','toilet','first_aid','information','cash_machine','trash_bin',
    'mountain','water','path','queue','pine_tree','peach_flowers','lantern','bench',
    'visitor','cleaner','mechanic','security','entertainer','happiness','noodles','tea_cup',
    'coins','loan','research','marketing','rating','objective','trophy','clock',
    'save','open','settings','news','display','mouse','multiplayer','chat',
    'rotate','zoom_in','zoom_out','pause','play','fast_forward','build','demolish',
    'warning','lock','success','error','track_blueprint','map','eyedropper','cursor',
]

def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def export(source, groups, name, folder, canvas=None, border=(0,0,0,0), axes='none', icon_index=None):
    """Copy original color pixels only; isolate alpha to selected connected silhouettes."""
    a=np.array(Image.open(MASTER/source).convert('RGBA'))
    mask=np.zeros(a.shape[:2],dtype=np.uint8)
    for g in groups:
        for y,x0,x1 in g['runs']:mask[y,x0:x1]=255
    # Two-pixel edge support retains original antialiasing but discards unrelated matte speckles.
    support=np.array(Image.fromarray(mask).filter(ImageFilter.MaxFilter(5)))>0
    aa=np.where(support & (a[:,:,3]>=16),a[:,:,3],0).astype(np.uint8)
    a[:,:,3]=aa
    bbox=Image.fromarray(aa).getbbox()
    if not bbox:raise RuntimeError('No pixels '+name)
    crop=Image.fromarray(a).crop(bbox)
    if canvas is None:canvas=(crop.width+8,crop.height+8)
    if crop.width>canvas[0] or crop.height>canvas[1]:raise RuntimeError(f'{name} crop {crop.size} > canvas {canvas}')
    output=Image.new('RGBA',canvas)
    offset=((canvas[0]-crop.width)//2,(canvas[1]-crop.height)//2)
    output.paste(crop,offset)
    target=ROOT/'assets'/folder/(name+'.png');target.parent.mkdir(parents=True,exist_ok=True)
    output.save(target)
    alpha=np.asarray(output)[:,:,3]
    record={
        'name':name,'file':target.relative_to(ROOT).as_posix(),
        'width':output.width,'height':output.height,'format':'PNG','mode':'RGBA',
        'sha256':digest(target),'borderLeftBottomRightTop':list(border),
        'resizeAxes':axes,'minimumSize':[border[0]+border[2]+1,border[1]+border[3]+1] if axes!='none' else list(canvas),
        'pivot':[.5,.5],'pixelsPerUnit':100,'containsDynamicText':False,
        'source':(MASTER/source).relative_to(ROOT).as_posix(),
        'sourceSha256':digest(MASTER/source),'sourceNativeSize':[a.shape[1],a.shape[0]],
        'sourceRectTopLeftXYXY':list(bbox),'pasteOffset':list(offset),
        'operation':'Original-pixel crop; isolate specified alpha>100 connected silhouettes, retain original alpha>=16 within 2px edge support; center on padded canvas. No recoloring, painting, AI call or upscaling.',
        'derivedFrom':{'file':(MASTER/source).relative_to(ROOT).as_posix(),'sha256':digest(MASTER/source),'generationRecord':(MASTER/(source+'.generation.json')).relative_to(ROOT).as_posix()},
        'alpha':{'minimum':int(alpha.min()),'maximum':int(alpha.max()),'transparentPixels':int((alpha==0).sum()),'visiblePixels':int((alpha>0).sum())},
        'isolatedForegroundComponents':len(groups),
        'qualityStatus':'slice_checked_pending_sheet_visual_review',
        'nativeDetailIncreased':False,'processedAt':datetime.now().astimezone().isoformat(),
    }
    if icon_index is not None:record['rowMajorIndex']=icon_index
    write_json(str(target)+'.source.json',record)
    return record

def main():
    common=[];icons=[]
    surface_groups=[g for g in components(np.asarray(Image.open(MASTER/'surfaces-native.png'))[:,:,3]>100) if g['area']>1000]
    for name,cx,cy,border,axes in [
        ('panel_main',320,390,(94,91,94,252),'both'),
        ('panel_card',943,395,(48,48,48,48),'both'),
        ('title_plate',320,985,(0,0,0,0),'none'),
        ('toolbar',943,1000,(45,23,45,23),'horizontal'),
    ]:
        g=min(surface_groups,key=lambda g:((g['bbox'][0]+g['bbox'][2])/2-cx)**2+((g['bbox'][1]+g['bbox'][3])/2-cy)**2)
        common.append(export('surfaces-native.png',[g],name,'common',border=border,axes=axes))
    control_groups=[g for g in components(np.asarray(Image.open(MASTER/'controls-native.png'))[:,:,3]>100) if g['area']>1000]
    for family,cy,canvas,border in [
        ('primary',248,(256,120),(56,30,56,30)),
        ('secondary',457,(256,112),(48,27,48,27)),
        ('tab',668,(256,128),(36,28,36,28)),
    ]:
        for cx,state in zip((139,389,638,887),('normal','pressed','selected','disabled')):
            g=min(control_groups,key=lambda g:((g['bbox'][0]+g['bbox'][2])/2-cx)**2+((g['bbox'][1]+g['bbox'][3])/2-cy)**2)
            common.append(export('controls-native.png',[g],family+'_'+state,'common',canvas,border,'horizontal'))
    for name,cx,cy,canvas,border,axes in [
        ('checkbox_off',138,887,(128,128),(0,0,0,0),'none'),
        ('checkbox_on',380,887,(128,128),(0,0,0,0),'none'),
        ('toggle_off',633,891,(208,112),(0,0,0,0),'none'),
        ('toggle_on',883,891,(208,112),(0,0,0,0),'none'),
        ('close',137,1127,(184,184),(0,0,0,0),'none'),
        ('back',387,1127,(184,184),(0,0,0,0),'none'),
        ('plus',637,1127,(184,184),(0,0,0,0),'none'),
        ('minus',887,1127,(184,184),(0,0,0,0),'none'),
        ('slider_track',164,1369,(296,64),(27,18,27,18),'horizontal'),
        ('slider_thumb',393,1367,(112,112),(0,0,0,0),'none'),
        ('progress_track',610,1368,(280,64),(35,18,35,18),'horizontal'),
        ('progress_fill',881,1368,(280,64),(28,18,28,18),'horizontal'),
    ]:
        g=min(control_groups,key=lambda g:((g['bbox'][0]+g['bbox'][2])/2-cx)**2+((g['bbox'][1]+g['bbox'][3])/2-cy)**2)
        common.append(export('controls-native.png',[g],name,'common',canvas,border,axes))
    manifest={'schemaVersion':1,'generatedAt':datetime.now().astimezone().isoformat(),'sourcePixelPolicy':'deterministic original-pixel cropping, alpha isolation and canvas padding only','assets':common,'icons':icons,'gaps':[]}
    write_json(ROOT/'assets'/'slice-manifest.json',manifest)
    print('Common assets ready:',len(common),flush=True)
    icon_a=np.asarray(Image.open(MASTER/'icons-native.png'))
    icon_groups=[g for g in components(icon_a[:,:,3]>100) if g['area']>=20]
    xs=[85,246,402,553,710,875,1026,1180]
    ys=[113,300,465,620,770,920,1050,1175]
    assigned=[[] for _ in NAMES]
    for g in icon_groups:
        b=g['bbox'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
        i=min(range(64),key=lambda i:((cx-xs[i%8])/156)**2+((cy-ys[i//8])/155)**2)
        assigned[i].append(g)
    for i,(name,groups) in enumerate(zip(NAMES,assigned)):
        if sum(g['area'] for g in groups)<2000:
            manifest['gaps'].append({'name':name,'reason':'No sufficiently large separate silhouette found'});continue
        icons.append(export('icons-native.png',groups,name,'icons',canvas=(192,192),icon_index=i+1))
    manifest['icons']=icons
    write_json(ROOT/'assets'/'slice-manifest.json',manifest)
    contact(manifest)
    print('Icon assets ready:',len(icons),'gaps:',len(manifest['gaps']),flush=True)

def contact(manifest):
    items=manifest['assets']+manifest['icons']
    cellw,cellh=230,198;cols=8;rows=(len(items)+cols-1)//cols
    sheet=Image.new('RGB',(cols*cellw,rows*cellh),(226,226,216));d=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    except OSError:font=ImageFont.load_default()
    for i,item in enumerate(items):
        x=(i%cols)*cellw;y=(i//cols)*cellh
        d.rectangle((x+3,y+3,x+cellw-3,y+cellh-3),fill=(29,60,51) if i%2 else (249,243,224))
        sprite=Image.open(ROOT/item['file']).convert('RGBA');sprite.thumbnail((cellw-16,cellh-38),Image.Resampling.LANCZOS)
        sheet.paste(sprite,(x+(cellw-sprite.width)//2,y+5+(cellh-38-sprite.height)//2),sprite)
        d.text((x+8,y+cellh-26),item['name'],font=font,fill=(246,238,210) if i%2 else (20,52,41))
    target=ROOT/'previews'/'sprites-contact.jpg';target.parent.mkdir(exist_ok=True);sheet.save(target,quality=94)
    write_json(str(target)+'.source.json',{
        'file':target.relative_to(ROOT).as_posix(),'sha256':digest(target),'width':sheet.width,'height':sheet.height,
        'operation':'QA contact sheet: thumbnail downsample of all final slices, alternate ivory/jade matte composite, ASCII labels. Not a newly generated model image.',
        'derivedFrom':[{'file':r['file'],'sha256':r['sha256'],'sourceRecord':r['file']+'.source.json'} for r in items],
        'processedAt':datetime.now().astimezone().isoformat(),
    })

def nine_slice(sprite,size,border):
    l,b,r,t=border;w,h=sprite.size;dw,dh=size
    if dw<=l+r or dh<=b+t:raise ValueError('Target below fixed borders')
    sx=[0,l,w-r,w];sy=[0,t,h-b,h];dx=[0,l,dw-r,dw];dy=[0,t,dh-b,dh]
    output=Image.new('RGBA',size)
    for row in range(3):
        for col in range(3):
            piece=sprite.crop((sx[col],sy[row],sx[col+1],sy[row+1]))
            target_size=(dx[col+1]-dx[col],dy[row+1]-dy[row])
            if piece.size!=target_size:piece=piece.resize(target_size,Image.Resampling.BILINEAR)
            output.paste(piece,(dx[col],dy[row]))
    return output

def nine_slice_qa():
    manifest=json.loads((ROOT/'assets'/'slice-manifest.json').read_text(encoding='utf-8'))
    # A side tassel belongs entirely to the fixed upper region of the large frame.
    for item in manifest['assets']:
        if item['name']=='panel_main':
            item['borderLeftBottomRightTop']=[94,91,94,252];item['minimumSize']=[189,344]
            write_json(ROOT/(item['file']+'.source.json'),item)
    write_json(ROOT/'assets'/'slice-manifest.json',manifest)
    checks=[];preview_rows=[]
    shown={'panel_main','panel_card','primary_normal','primary_selected','secondary_normal','tab_selected','toolbar','progress_track'}
    for item in manifest['assets']:
        if item['resizeAxes']=='none':continue
        sprite=Image.open(ROOT/item['file']).convert('RGBA');w,h=sprite.size;l,b,r,t=item['borderLeftBottomRightTop']
        sizes=[(384,384),(960,640),(1440,800)] if item['name']=='panel_main' else ([(256,256),(720,480),(1200,720)] if item['name']=='panel_card' else [(max(l+r+16,180),h),(w,h),(max(w*2,520),h)])
        rendered=[]
        for size in sizes:
            out=nine_slice(sprite,size,item['borderLeftBottomRightTop']);dw,dh=size
            source_boxes=[(0,0,l,t),(w-r,0,w,t),(0,h-b,l,h),(w-r,h-b,w,h)]
            dest_boxes=[(0,0,l,t),(dw-r,0,dw,t),(0,dh-b,l,dh),(dw-r,dh-b,dw,dh)]
            equal=[sprite.crop(sb).tobytes()==out.crop(db).tobytes() for sb,db in zip(source_boxes,dest_boxes)]
            checks.append({'name':item['name'],'file':item['file'],'sha256':item['sha256'],'sourceSize':[w,h],'targetSize':list(size),'borderLeftBottomRightTop':item['borderLeftBottomRightTop'],'cornerPixelEquality':equal,'allCornersPreserved':all(equal),'fixedHeightMaintained':dh==h if item['resizeAxes']=='horizontal' else None})
            rendered.append((out,size))
        if item['name'] in shown:preview_rows.append((item,rendered))
    cellw,cellh=520,350
    sheet=Image.new('RGB',(cellw*3,cellh*len(preview_rows)),(227,225,211));d=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    except OSError:font=ImageFont.load_default()
    for ri,(item,rendered) in enumerate(preview_rows):
        for col,(out,size) in enumerate(rendered):
            x=col*cellw;y=ri*cellh;d.rectangle((x+3,y+3,x+cellw-3,y+cellh-3),fill=(30,59,48))
            out.thumbnail((cellw-24,cellh-50),Image.Resampling.LANCZOS)
            sheet.paste(out,(x+(cellw-out.width)//2,y+5+(cellh-50-out.height)//2),out)
            d.text((x+12,y+cellh-35),f"{item['name']} {size[0]}x{size[1]}",fill=(250,241,214),font=font)
    target=ROOT/'previews'/'nine-slice-contact.jpg';sheet.save(target,quality=95)
    report={'processedAt':datetime.now().astimezone().isoformat(),'operation':'Offline Pillow nine-slice raster proof from final PNGs. Source corner pixels copied without resampling; only edge middles/center resized. Contact thumbnails downsampled for review. Not a Unity screenshot.','unityValidated':False,'titlePlatePolicy':'Not sliced. Preserve aspect and Taiji shape.','panelMainCorrection':'Top border 252px keeps side jade beads and red tassels inside the fixed top corners; 384x256 is below valid fixed height and is not used.','checks':checks,'totalTests':len(checks),'allCornerChecksPassed':all(c['allCornersPreserved'] for c in checks),'contactSheet':target.relative_to(ROOT).as_posix(),'contactSha256':digest(target),'sourceManifestSha256':digest(ROOT/'assets'/'slice-manifest.json')}
    write_json(ROOT/'records'/'nine-slice-qa.json',report)
    write_json(str(target)+'.source.json',{'file':target.relative_to(ROOT).as_posix(),'sha256':digest(target),'width':sheet.width,'height':sheet.height,'operation':report['operation'],'derivedFrom':[{'file':r['file'],'sha256':r['sha256'],'sourceRecord':r['file']+'.source.json'} for r in manifest['assets'] if r['name'] in shown],'qaRecord':'records/nine-slice-qa.json','processedAt':report['processedAt']})
    print('Nine-slice tests:',len(checks),'all corners preserved:',report['allCornerChecksPassed'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inspect',action='store_true');ap.add_argument('--nine-slice-qa',action='store_true');args=ap.parse_args()
    if args.inspect: inspect()
    elif args.nine_slice_qa:nine_slice_qa()
    else: main()
