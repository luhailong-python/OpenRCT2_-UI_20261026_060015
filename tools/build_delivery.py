"""Assemble a local review gallery and verifiable art delivery metadata. No Unity/Git."""
from pathlib import Path
import json,csv,hashlib,html,collections,datetime,zipfile,re
from zoneinfo import ZoneInfo
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
NOW=datetime.datetime.now(ZoneInfo('America/New_York')).isoformat()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def write(p,obj):
 q=ROOT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def fileof(r):return r.get('file') or r.get('path') or r.get('screenPath')
prod=read('docs/ui-production-manifest.json')
base_screens=prod['screens'];states=prod['states']
inventory=read('docs/repo-ui-inventory.json');statecontract=read('docs/state-contracts.json')
unitmap={r['key']:r for r in inventory}
unitkeys={r['windowUnit']:r['key'] for r in inventory}
detail_screens=[]
for mp in ['docs/detail-ui-production-manifest.json','docs/management-detail-manifest.json','docs/operations-detail-manifest.json','docs/utility-detail-manifest.json']:
 if not (ROOT/mp).exists():continue
 for original in read(mp)['screens']:
  r=dict(original);r['id']=r.get('id') or r.get('screenId');r['key']=r.get('key') or r.get('windowKey') or unitkeys.get(r.get('unit',r.get('sourceUnit')))
  r['system']=r.get('system') or unitmap.get(r['key'],{}).get('system','补充详页')
  r['detailManifest']=mp;r['category']='product-detail';detail_screens.append(r)
screens=base_screens+detail_screens;allrows=screens+states
write('docs/all-ui-production-manifest.json',{'createdAt':NOW,'baseScreenCount':len(base_screens),'detailScreenCount':len(detail_screens),'screenCount':len(screens),'stateCount':len(states),'screens':screens,'states':states,'unityVerified':False})
slice_manifest=read('assets/slice-manifest.json')
assets=slice_manifest['assets']+slice_manifest.get('icons',[])+read('assets/illustration-manifest.json')+read('assets/supplement-manifest.json')+read('assets/construction-icon-manifest.json')
bg=read('assets/backgrounds/park-day-native.png.generation.json')
assets.append({'name':'park_day_background','file':bg['file'],'width':bg['width'],'height':bg['height'],'sha256':bg['sha256'],'mode':bg['mode'],'spriteType':'Simple','pivot':[.5,.5],'borderLeftBottomRightTop':[0,0,0,0],'generationRecord':bg['file']+'.generation.json','operation':'native_AI_background','usage':'UI背景及设计预览；非可交互模拟地图'})
assetUse=collections.defaultdict(list)
for r in allrows:
 for p in r.get('assetPaths',[]):assetUse[p].append(r['id'])
for a in assets:
 a.setdefault('name',Path(a['file']).stem);a.setdefault('spriteType','Sliced' if a.get('resizeAxes','none')!='none' else 'Simple')
 a.setdefault('pivot',[.5,.5]);a.setdefault('pixelsPerUnit',100);a['usedBy']=assetUse.get(a['file'],[])
 a['unityImportStatus']='suggested_not_imported';a.setdefault('nativeDetailIncreased',False)
manifest={'schemaVersion':1,'createdAt':NOW,'formalSpriteCount':len(assets),'referenceCanvas':[1920,1080],'targetPlatform':'desktop_landscape_assumption','unityVerified':False,'assets':assets,'sourceMasterBoards':[p.relative_to(ROOT).as_posix() for p in (ROOT/'assets/masters').glob('*.png')],'fonts':'../records/font-sources.json'}
write('assets/manifest.json',manifest)
control_data=read('docs/control-display-evidence.json')
control_boards=control_data['sourceBoards']
dynamic=control_data.get('dynamicSharedBoard')
if isinstance(dynamic,dict):control_boards=control_boards+[dynamic]
elif isinstance(dynamic,str):control_boards=control_boards+[{'file':dynamic}]
control_html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>源码控件样式合同</title><style>body{background:#eee8d8;color:#173e35;margin:30px;font:16px system-ui}img{width:100%;max-width:1500px;display:block;border:1px solid #c3ad70;margin:16px 0}a{color:inherit}</style><a href="../../index.html">返回整套预览</a><h1>源码控件样式核对板</h1><p>覆盖1,438个源码控件符号的皮肤/动态区域合同。核对板坐标用于美术检查，不等于这些控件已逐件排入产品页面或接入Unity。</p>'
for i,b in enumerate(control_boards):
 if b.get('file'):control_html+=f'<h2>核对板 {i+1}</h2><a href="../../{b["file"]}"><img loading="lazy" src="../../{b["file"]}" alt="核对板{i+1}"></a>'
(ROOT/'previews/control-contracts/index.html').write_text(control_html,encoding='utf-8')
for u in inventory:
 rows=[r for r in screens if r.get('key')==u['key']]
 u['screenPaths']=[fileof(r) for r in rows];u['assetPaths']=sorted(set(p for r in rows for p in r.get('assetPaths',[])))
 u['productionStatus']='produced' if len(rows)>=len(u['tabs']) else 'incomplete'
 u['acceptanceStatus']='offline_static_checks_and_sample_visual_review_recorded_pending_user_acceptance'
write('docs/ui-coverage-final.json',inventory)

# Image provenance is indexed for every task-created raster (the reference clone is excluded).
def collect_provenance():
 prov=[]
 contact_sources={
  'previews/sprites-contact.jpg':[a['file'] for a in slice_manifest['assets']+slice_manifest.get('icons',[])],
  'previews/illustrations-contact.jpg':[a['file'] for a in read('assets/illustration-manifest.json')],
  'previews/supplement-contact.jpg':[a['file'] for a in read('assets/supplement-manifest.json')],
  'previews/construction-icons-contact.jpg':[a['file'] for a in read('assets/construction-icon-manifest.json')],
  'previews/nine-slice-contact.jpg':[a['file'] for a in slice_manifest['assets'] if a.get('resizeAxes')!='none']}
 for folder in ('reference-art','assets','designs','previews'):
  for p in (ROOT/folder).rglob('*'):
   if p.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
   rel=p.relative_to(ROOT).as_posix(); im=Image.open(p)
   candidates=[Path(str(p)+'.generation.json'),Path(str(p)+'.source.json'),p.with_suffix('.source.json')]
   record=next((q.relative_to(ROOT).as_posix() for q in candidates if q.exists()),None)
   item={'file':rel,'sha256':sha(rel),'width':im.width,'height':im.height,'mode':im.mode,'record':record,'operation':'reference_copy' if folder=='reference-art' else 'see_sidecar' if record else 'review_contact_sheet_derived_from_registered_assets_or_screen_previews','actualModel':'see_generation_chain' if folder!='reference-art' else None}
   if rel in contact_sources:item['derivedFrom']=[{'file':q,'sha256':sha(q),'sourceRecord':q+'.source.json'} for q in contact_sources[rel]]
   if folder=='reference-art':item['sourceAssociation']='docs/image-reference-associations.md';item['modelEvidence']='historical_style_reference_no_new_model_claim'
   prov.append(item)
 return prov

qa={'createdAt':NOW,'checks':[],'failures':[],'unityVerified':False,'scope':'offline_static_art_and_metadata'}
def check(name,condition,detail):
 qa['checks'].append({'name':name,'passed':bool(condition),'detail':detail})
 if not condition:qa['failures'].append({'name':name,'detail':detail})
check('all_source_windows_mapped',len(inventory)==82 and all(any(r.get('key')==u['key'] for r in screens) for u in inventory),'79窗口源码单元+Chat/Console/CustomWindow')
check('tab_mode_counts',len(base_screens)==sum(len(u['tabs']) for u in inventory),{'base':len(base_screens),'expected':sum(len(u['tabs']) for u in inventory),'additionalProductDetails':len(detail_screens)})
check('business_state_counts',len(states)==sum(len(s['states']) for s in statecontract['systems']),{'actual':len(states),'expected':sum(len(s['states']) for s in statecontract['systems'])})
overflow_count=sum(len(r.get('layoutIssues',[])) for r in allrows)
check('preview_text_layout_no_reported_overflow',overflow_count==0,{'reported':overflow_count})
missing=[];badsize=[];badlayout=[]
for r in allrows:
 f=fileof(r)
 if not f or not (ROOT/f).exists():missing.append(f);continue
 im=Image.open(ROOT/f);im.verify(); im=Image.open(ROOT/f)
 if im.size!=(1920,1080):badsize.append({'file':f,'size':im.size})
 for prop in ('layoutFile','sourceRecord'):
  if not r.get(prop) or not (ROOT/r[prop]).exists():missing.append({'file':f,'field':prop,'path':r.get(prop)})
check('all_preview_files_and_records_exist',not missing,missing)
check('screen_dimensions_1920_1080',not badsize,badsize)
alphaissues=[];borderissues=[];hashissues=[]
for a in assets:
 p=ROOT/a['file'];im=Image.open(p);im.verify();im=Image.open(p)
 if list(im.size)!=[a['width'],a['height']] or sha(a['file'])!=a['sha256']:hashissues.append(a['file'])
 if a['file'].startswith(('assets/common/','assets/icons/','assets/illustrations/','assets/construction-icons/')):
  if im.mode!='RGBA' or im.getchannel('A').getextrema()[0]!=0 or im.getchannel('A').getextrema()[1]<200:alphaissues.append(a['file'])
 l,b,r,t=a.get('borderLeftBottomRightTop',[0,0,0,0])
 if min(l,b,r,t)<0 or l+r>=im.width or b+t>=im.height:borderissues.append(a['file'])
check('formal_asset_sizes_hashes',not hashissues,hashissues)
check('formal_sprites_real_alpha',not alphaissues,alphaissues)
check('sprite_border_ranges',not borderissues,borderissues)
check('font_license_record_exists',(ROOT/'records/font-sources.json').exists(),'正式字体及许可证记录')
qa['status']='machine_checks_passed_visual_review_recorded_separately' if not qa['failures'] else 'incomplete'
write('records/delivery-qa.json',qa)

# Human-readable item-by-item production/acceptance spreadsheet.
with (ROOT/'docs/UI功能与资源总清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['ID','系统','功能/界面','页签/状态','类别','功能依据','整屏或状态图','独立资源','布局/文案','来源记录','制作状态','验收状态','待接入事项'])
 for kind,rows in [('screen',screens),('state',states)]:
  for r in rows:
   unit=unitmap.get(r.get('key'),{})
   evidence=';'.join(unit.get('sourceFiles',[])) or 'docs/state-contracts.json'
   writer.writerow([r['id'],r.get('system',''),r.get('title',''),r.get('tab',r.get('stateId','')),kind,evidence,fileof(r),';'.join(r.get('assetPaths',[])),r.get('layoutFile',''),r.get('sourceRecord',''),'已制作','静态验收见records/visual-review.json','Unity未导入；动态文字/交互/运行验证待下一阶段'])
lines=['# UI 功能与资源总清单','',f'固定功能版本 `52a55c3e8da5972460642bdfed61d091fe9cabfd`；核验日期 {NOW[:10]}。共 {len(inventory)} 项源码界面单元、{len(base_screens)} 张基础页签/模式整屏、{len(detail_screens)} 张产品操作详页、{len(states)} 张业务状态图。页签/模式不等同于原作窗口数量。','', '[逐屏CSV](UI功能与资源总清单.csv) · [源码证据](repo-ui-inventory.json) · [状态合同](state-contracts.json) · [资源清单](../assets/manifest.json) · [本地预览](../index.html)','', '| 系统 | 界面 | 基础分组 | 含补充成图 | 图片目录 |','|---|---|---:|---:|---|']
for u in inventory:
 rows=[r for r in screens if r.get('key')==u['key']]
 first=fileof(rows[0]) if rows else ''
 lines.append(f'| {u["system"]} | {u["title"]} | {len(u["tabs"])} | {len(rows)} | [{u["key"]}](../{first}) |')
lines+=['','业务状态覆盖21系统，逐项见CSV及状态合同；普通/按下/选中/禁用和锁定叠层由通用资源及状态预览映射。建议补充/视觉改编与原有机制按合同分别记录。任意第三方插件内容不可能预先枚举，交付的是原生插件窗口控件皮肤合同。','', '验收数量与限制见 [验收结果](acceptance-results.md)。']
(ROOT/'docs/UI功能与资源总清单.md').write_text('\n'.join(lines),encoding='utf-8')

# Gallery thumbnails and overview sheets are deterministic derivatives, not new model images.
thumbDir=ROOT/'previews/thumbnails';thumbDir.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
gallery=[]
for i,r in enumerate(allrows):
 f=fileof(r);im=Image.open(ROOT/f).convert('RGB');im.thumbnail((480,270),Image.Resampling.LANCZOS)
 safeid=re.sub(r'[^\w-]','_',r['id'])
 out='previews/thumbnails/'+safeid+'.jpg';im.save(ROOT/out,quality=83,optimize=True)
 tr={'file':out,'sha256':sha(out),'derivedFrom':[{'file':f,'sha256':sha(f),'sourceRecord':r.get('sourceRecord')}],'operation':'thumbnail_resample_480x270_no_new_model_generation'}
 write(out+'.source.json',tr)
 gallery.append({'id':r['id'],'key':r.get('key',r.get('systemKey','')),'title':r.get('title',''),'system':r.get('system',''),'tab':r.get('tab',r.get('stateId','')),'kind':'detail' if r.get('category')=='product-detail' else 'screen' if i<len(screens) else 'state','file':f,'thumb':out,'layout':r.get('layoutFile'),'sources':r.get('sourceRecord')})
write('previews/gallery.json',gallery)
contacts=ROOT/'previews/contact-sheets';contacts.mkdir(exist_ok=True)
for start in range(0,len(gallery),32):
 group=gallery[start:start+32];sheet=Image.new('RGB',(1600,1728),'#f1ead7');draw=ImageDraw.Draw(sheet)
 for j,g in enumerate(group):
  x=j%4*400;y=j//4*216;tile=Image.open(ROOT/g['thumb']);tile.thumbnail((400,180),Image.Resampling.LANCZOS);sheet.paste(tile,(x,y))
  label=f'{g["title"]} · {g["tab"]}'
  while draw.textlength(label,font=small)>390:label=label[:-2]+'…'
  draw.text((x+8,y+185),label,font=small,fill='#234e40')
 file=f'previews/contact-sheets/{start//32+1:02d}.jpg';sheet.save(ROOT/file,quality=87)
 write(file+'.source.json',{'file':file,'sha256':sha(file),'derivedFrom':[{'file':g['file'],'sha256':sha(g['file'])} for g in group],'operation':'review_contact_sheet_thumbnail_composition_no_new_model_generation'})
keys=['title-menu','main','new-ride','ride-construction','ride','finances','guest','staff-list','editor-scenario-options','multiplayer','options','park']
picks=[]
for k in keys:
 candidates=[g for g in gallery if g['kind']=='screen' and g['key']==k]
 if candidates:picks.append(candidates[0])
sheet=Image.new('RGB',(1920,1212),'#e8e0c9');draw=ImageDraw.Draw(sheet)
for j,g in enumerate(picks):
 x=j%4*480;y=j//4*404;tile=Image.open(ROOT/g['file']);tile.thumbnail((480,270),Image.Resampling.LANCZOS);sheet.paste(tile,(x,y+50));draw.text((x+18,y+17),g['title'],font=font,fill='#214f3e')
 draw.text((x+18,y+335),g['tab'],font=font,fill='#6b715d')
sheet.save(ROOT/'previews/overview.jpg',quality=94)
write('previews/overview.jpg.source.json',{'file':'previews/overview.jpg','sha256':sha('previews/overview.jpg'),'derivedFrom':[{'file':g['file'],'sha256':sha(g['file'])} for g in picks],'operation':'12_screen_review_contact_sheet_no_new_model_generation'})

data=json.dumps(gallery,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>云游仙苑（暂名）· UI美术审阅</title><style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#eee8d8;color:#173e35;font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif}header{background:#164f40;color:#fff4d8;padding:24px 4vw;border-bottom:3px solid #cba665}h1{font-size:27px;margin:0}header p{margin:6px 0 0;opacity:.85}nav{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px}a{color:inherit}main{padding:22px 4vw}aside{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:22px}input,select,button{font:inherit;padding:10px 15px;border:1px solid #b89c62;border-radius:8px;background:#fffaf0;color:#173e35}input{min-width:240px}button{cursor:pointer}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:20px}.tile{border:1px solid #c3ae7b;border-radius:10px;background:#faf5e7;overflow:hidden;box-shadow:0 4px 14px #193c3212}.tile button{display:block;padding:0;border:0;border-radius:0;width:100%;background:#d5ddcb}.tile img{width:100%;display:block;aspect-ratio:16/9;object-fit:contain}.info{padding:12px 16px}.info strong{display:block;font-size:18px}.meta{font-size:13px;color:#667264}.links{display:flex;gap:16px;margin-top:6px}dialog{border:1px solid #cba665;border-radius:10px;background:#f8f1df;max-width:96vw;width:1600px;padding:16px;color:#173e35}dialog::backdrop{background:#071d17dd}dialog img{display:block;width:100%;max-height:80vh;object-fit:contain}dialog footer{display:flex;gap:12px;justify-content:space-between;align-items:center;margin-top:10px}dialog button{padding:7px 15px}#count{margin-left:auto}small{display:block;margin-top:10px;color:#657365} @media(max-width:600px){main{padding:16px}h1{font-size:23px}#grid{grid-template-columns:1fr}}
</style><header><h1>云游仙苑（暂名） · 道家 Q 版 UI 美术</h1><p>OpenRCT2 功能研究 · 本地图片审阅 · 1920×1080桌面参考 · 名称与数据为设计样例</p><nav><a href="docs/UI功能与资源总清单.md">覆盖清单</a><a href="docs/UI功能与资源总清单.csv">逐项CSV</a><a href="assets/manifest.json">正式资源</a><a href="docs/unity-import-guide.md">Unity导入建议</a><a href="docs/acceptance-results.md">验收结果</a><a href="previews/sprites-contact.jpg">控件/图标总览</a><a href="previews/illustrations-contact.jpg">插画总览</a></nav></header><main><aside><input id="q" aria-label="搜索" placeholder="搜索界面、系统或状态"><select id="kind" aria-label="类型"><option value="">全部图片</option value="screen">整屏/页签/模式</option><option value="state">业务状态</option></select><select id="system" aria-label="系统"><option value="">全部系统</option></select><button id="reset">清除筛选</button><span id="count"></span></aside><div id="grid"></div><small>图片展示布局与操作反馈；不代表原游戏运行截图或已接入Unity。所有正式底图无动态文案，文字与布局记录可逐屏打开。</small></main><dialog id="viewer"><img id="large" alt=""><footer><button id="prev">← 上一张</button><span id="caption"></span><a id="original" target="_blank">打开原图</a><button id="next">下一张 →</button><button id="close">关闭 Esc</button></footer></dialog><script>const rows=GALLERY_DATA;const $=x=>document.getElementById(x);let shown=rows,active=0;const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));[...new Set(rows.map(x=>x.system))].sort().forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;$('system').append(o)});function render(){let q=$('q').value.trim().toLowerCase();shown=rows.filter(r=>(!q||[r.title,r.tab,r.system,r.id].join(' ').toLowerCase().includes(q))&&(!$('kind').value||r.kind===$('kind').value)&&(!$('system').value||r.system===$('system').value));$('count').textContent=shown.length+' / '+rows.length+' 张';$('grid').innerHTML=shown.map((r,i)=>`<article class="tile"><button onclick="openImage(${i})" aria-label="查看${esc(r.title)}"><img src="${esc(r.thumb)}" alt="${esc(r.title+' '+r.tab)}" loading="lazy"></button><div class="info"><strong>${esc(r.title)}</strong><div>${esc(r.tab)}</div><div class="meta">${esc(r.system)} · ${r.kind==='screen'?'整屏/模式':'业务状态'} · ${esc(r.id)}</div><div class="links"><a href="${esc(r.layout)}">文案/布局</a><a href="${esc(r.sources)}">图片来源</a><a href="${esc(r.file)}" target="_blank">原图</a></div></div></article>`).join('')}function openImage(i){if(!shown.length)return;active=(i+shown.length)%shown.length;const r=shown[active];$('large').src=r.file;$('large').alt=r.title+' '+r.tab;$('caption').textContent=r.title+' · '+r.tab;$('original').href=r.file;if(!$('viewer').open)$('viewer').showModal()}$('prev').onclick=()=>openImage(active-1);$('next').onclick=()=>openImage(active+1);$('close').onclick=()=>$('viewer').close();$('q').oninput=render;$('kind').onchange=render;$('system').onchange=render;$('reset').onclick=()=>{$('q').value='';$('kind').value='';$('system').value='';render()};document.onkeydown=e=>{if($('viewer').open&&e.key==='ArrowRight')openImage(active+1);if($('viewer').open&&e.key==='ArrowLeft')openImage(active-1)};render();</script></html>'''.replace('GALLERY_DATA',data)
page=page.replace('<option value="state">业务状态</option>','<option value="detail">产品操作详页</option><option value="state">业务状态</option>')
page=page.replace("r.kind==='screen'?'整屏/模式':'业务状态'","r.kind==='screen'?'整屏/模式':r.kind==='detail'?'产品操作详页':'业务状态'")
page=page.replace('<a href="previews/sprites-contact.jpg">','<a href="previews/flows/index.html">四张流程图</a><a href="previews/control-contracts/index.html">控件样式合同</a><a href="previews/sprites-contact.jpg">')
(ROOT/'index.html').write_text(page,encoding='utf-8')

genIndex=[{'file':p.relative_to(ROOT).as_posix().removesuffix('.generation.json'),'record':p.relative_to(ROOT).as_posix()} for p in (ROOT/'assets').rglob('*.generation.json')]
write('records/generation-index.json',genIndex)
write('records/image-provenance-index.json',{'createdAt':NOW,'index':collect_provenance(),'reviewDerivatives':'previews/thumbnails/*.source.json、previews/contact-sheets/*.source.json、previews/overview.jpg.source.json均逐件保存来源链；原生模型见generation-index.json'})
print(json.dumps({'screens':len(screens),'states':len(states),'formalAssets':len(assets),'gallery':len(gallery),'machineFailures':qa['failures']},ensure_ascii=False))
