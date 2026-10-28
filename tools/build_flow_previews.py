"""Render explanatory flow diagrams from painted UI assets; no new generated art."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
BODY=ROOT/'assets/fonts/NotoSansCJKsc-Regular.otf';TITLE=ROOT/'assets/fonts/MaShanZheng-Regular.ttf'
font=lambda s,title=False:ImageFont.truetype(str(TITLE if title else BODY),s)
slice_data=json.loads((ROOT/'assets/slice-manifest.json').read_text(encoding='utf-8'));meta=slice_data['assets']+slice_data.get('icons',[]);entries={x['name']:x for x in meta}
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def nine(im,size,b):
 l,bt,r,t=b;w,h=size;sx=(0,l,im.width-r,im.width);sy=(0,t,im.height-bt,im.height);dx=(0,l,w-r,w);dy=(0,t,h-bt,h);out=Image.new('RGBA',size)
 for yy in range(3):
  for xx in range(3):
   p=im.crop((sx[xx],sy[yy],sx[xx+1],sy[yy+1]));tw=dx[xx+1]-dx[xx];th=dy[yy+1]-dy[yy]
   out.alpha_composite(p.resize((tw,th),Image.Resampling.LANCZOS),(dx[xx],dy[yy]))
 return out
flows=[
 ('01-core-loop','经营系统与反馈循环','玩法参考：OpenRCT2；道家名称为视觉设计样例。',[
 ('园区主界面','暂停/加速/视图/导航','park_gate'),('建设园区','土地 → 步道 → 设施','build'),('测试与营业','运行参数 → 测量 → 开放','roller_coaster'),('游客与员工','需求/消费/巡逻/维修','visitor'),('财务与研究','收支/贷款/营销/拨款','coins'),('目标与奖项','评分与目标 → 成功/失败','trophy')],[(0,1,'选择建设'),(1,2,'条件满足'),(2,3,'体验反馈'),(3,4,'经营收支'),(4,5,'持续经营'),(4,1,'研究解锁/预算反馈')]),
 ('02-ride-flow','设施建造与运营流程','商店/服务设施无须套用所有轨道测试条件；具体能力由设施类型决定。',[
 ('选择设施或蓝图','交通/温和/过山车/惊险等','track_blueprint'),('分段建设与连接','轨道/车站/入口/出口/步道','build'),('测试与测量','试车/模拟/评级/速度图表','research'),('开放营业','票价/客流/排队/收入','park_gate'),('维护处理','故障提醒 → 维修员定位','mechanic'),('关闭与处置','修改/翻新/拆除确认','demolish')],[(0,1,'开始建设'),(1,2,'校验通过'),(2,3,'选择开放'),(3,4,'故障/检查'),(4,3,'修复后营业'),(3,5,'主动关闭'),(5,1,'继续改建')]),
 ('03-editor-flow','场景编辑与保存流程','七步控制器存在前置校验；不能将所有步骤理解为可任意跳转。',[
 ('01 选择对象','设施/景观/步道/入口等','roller_coaster'),('02 地形与连通','土地/入口/道路/出生点','mountain'),('03 研究顺序','已研究/未研究/优先顺序','research'),('04 场景选项','财务/游客/限制/气候','settings'),('05/06 目标与资料','05目标参数 / 06标题说明','objective'),('07 保存场景','保存路径/名称/覆盖确认','save')],[(0,1,'必要对象齐备'),(1,2,'入口等校验通过'),(2,3,'下一步'),(3,4,'目标 → 资料'),(4,5,'通过保存检查')]),
 ('04-multiplayer-flow','多人协作与异常返回','协作服务器使用名称、版本与密码认证；无账号选角或RPG角色服。',[
 ('服务器列表','公开/收藏/直接连接','multiplayer'),('连接与认证','版本/名称/密码/容量','lock'),('下载与同步','显示进度；允许取消','open'),('协作经营','园区操作/聊天/玩家统计','chat'),('权限组与管理','组别/允许操作/踢出','security'),('异常反馈','错误版本/密码/断线/失同步','warning')],[(0,1,'连接'),(1,2,'认证成功'),(2,3,'同步完成'),(3,4,'查看权限'),(1,5,'认证失败'),(3,5,'连接异常'),(5,0,'返回列表')])
]
outdir=ROOT/'previews/flows';outdir.mkdir(parents=True,exist_ok=True);manifest=[]
for key,title,note,nodes,edges in flows:
 image=Image.new('RGBA',(W,H),'#f0e9d7');draw=ImageDraw.Draw(image);used=set();texts=[]
 def text(s,xy,size=24,color='#173e35',heading=False):
  draw.text(xy,s,font=font(size,heading),fill=color);texts.append({'text':s,'position':xy,'fontSize':size,'font':str(TITLE if heading else BODY),'color':color})
 text(title,(96,46),50,heading=True);text(note,(98,119),23,color='#6d6f5c')
 positions=[(100,220),(700,220),(1300,220),(1300,630),(700,630),(100,630)]
 # Arrow routes are data diagrams, distinct from decorative UI painting.
 for a,b,label in edges:
  ax,ay=positions[a];bx,by=positions[b]
  reverse=any(e[0]==b and e[1]==a for e in edges)
  short={'选择建设':'建设','条件满足':'测试','体验反馈':'运营','经营收支':'收支','持续经营':'目标','研究解锁/预算反馈':'解锁反馈','开始建设':'建设','校验通过':'校验','选择开放':'开放','故障/检查':'故障','修复后营业':'修复','主动关闭':'关闭','继续改建':'改建','必要对象齐备':'齐备','入口等校验通过':'校验','目标 → 资料':'资料','通过保存检查':'保存','认证成功':'认证','同步完成':'同步','查看权限':'权限','认证失败':'认证失败','连接异常':'异常','返回列表':'返回'}.get(label,label)
  if key=='04-multiplayer-flow' and a==1 and b==5:
   points=[(ax,ay+132),(660,ay+132),(660,560),(bx+260,560),(bx+260,by)];tx=(470,580)
  elif ay==by and abs(ax-bx)==600:
   yy=ay+(100 if ax>bx else 164) if reverse else ay+132
   x1=ax+520 if bx>ax else ax;x2=bx if bx>ax else bx+520;points=[(x1,yy),(x2,yy)];tx=(min(x1,x2)+10,yy-36)
  elif ax==bx:
   x=ax+260;starty=ay+264 if by>ay else ay;endy=by if by>ay else by+264;points=[(x,starty),(x,endy)];tx=(x+20,(starty+endy)//2-18)
  elif by<ay:
   lane=550-((a+b)%2)*32;points=[(ax+260,ay),(ax+260,lane),(bx+260,lane),(bx+260,by+264)];tx=(min(ax,bx)+330,lane-30)
  else:
   y=980-((a+b)%3)*24;points=[(ax+260,ay+264),(ax+260,y),(bx+260,y),(bx+260,by+264)];tx=(min(ax,bx)+330,y-28)
  draw.line(points,fill='#a68b53',width=4);px,py=points[-1];qx,qy=points[-2]
  if abs(px-qx)>abs(py-qy):sgn=1 if px>qx else -1;tri=[(px,py),(px-sgn*14,py-8),(px-sgn*14,py+8)]
  else:sgn=1 if py>qy else -1;tri=[(px,py),(px-8,py-sgn*14),(px+8,py-sgn*14)]
  draw.polygon(tri,fill='#a68b53');text(short,tx,20,color='#527364')
 for i,(head,body,icon) in enumerate(nodes):
  x,y=positions[i];p=entries['panel_card'];art=Image.open(ROOT/p['file']).convert('RGBA');image.alpha_composite(nine(art,(520,264),p['borderLeftBottomRightTop']),(x,y));used.add(p['file'])
  f=entries[icon]['file'];art=Image.open(ROOT/f).convert('RGBA');art=ImageOps.contain(art,(110,110),Image.Resampling.LANCZOS);image.alpha_composite(art,(x+36+(110-art.width)//2,y+47+(110-art.height)//2));used.add(f)
  text(head,(x+164,y+62),32,heading=True);text(body,(x+38,y+190),22)
 text('流程说明图 · 静态美术交付 · 操作与状态以源码合同为依据',(100,1030),21,color='#6d6f5c')
 file='previews/flows/'+key+'.png';image.convert('RGB').save(ROOT/file,optimize=True)
 source={'file':file,'sha256':sha(file),'operation':'diagram_typesetting_and_composition_from_handpainted_sprites_not_AI_generation','derivedFrom':[{'file':f,'sha256':sha(f),'sourceRecord':f+'.source.json'} for f in sorted(used)],'logicReference':'docs/workflows.md','fonts':'records/font-sources.json','nativeDetailIncreased':False}
 (ROOT/file).with_suffix('.source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/file).with_suffix('.layout.json').write_text(json.dumps({'file':file,'textLayers':texts,'nodes':nodes,'edges':edges,'canvas':[W,H]},ensure_ascii=False,indent=2),encoding='utf-8')
 manifest.append({'file':file,'title':title,'sourceRecord':str(Path(file).with_suffix('.source.json')),'layoutFile':str(Path(file).with_suffix('.layout.json'))})
(ROOT/'previews/flows/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'previews/flows/index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>流程预览</title><style>body{margin:30px;background:#eee8d8;color:#214e40;font-family:system-ui}img{width:100%;border:1px solid #c3a45f}a{color:inherit}</style><a href="../../index.html">返回整套预览</a>'+''.join('<h2>'+m['title']+'</h2><a href="'+Path(m['file']).name+'"><img src="'+Path(m['file']).name+'" alt="'+m['title']+'"></a>' for m in manifest),encoding='utf-8')
print('4 flow diagram PNGs with source/layout records saved.')
