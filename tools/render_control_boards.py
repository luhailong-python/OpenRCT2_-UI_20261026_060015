"""Render source-bound UI skin contract sheets, NOT product screen placement.

Every source WIDX symbol receives a labelled style sample with actual shared
painted PNGs. Technical IDs are intentionally confined to these QA sheets.
No original game sprites, AI calls, Unity project or Git operations are used.
"""
from pathlib import Path
import hashlib
import json
import math
import re
from datetime import datetime
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews/control-contracts'
W,H=1920,1080
FONT=ROOT/'assets/fonts/NotoSansCJKsc-Regular.otf'
if not FONT.exists():raise FileNotFoundError('Task-local OFL Chinese font required')
FC={}
IM={}
META=json.loads((ROOT/'assets/slice-manifest.json').read_text(encoding='utf-8'))
ASSETS={e['file']:e for e in META['assets']+META.get('icons',[])}
C='assets/common/'


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def font(n):
    if n not in FC:FC[n]=ImageFont.truetype(str(FONT),n)
    return FC[n]
def load(p):
    if p not in IM:IM[p]=Image.open(ROOT/p).convert('RGBA')
    return IM[p]
def clean(s):
    s=re.sub(r'\{[^}]*\}','',str(s))
    return re.sub(r'\s+',' ',s).strip(' :：\n')
def fit_text(draw,s,xy,width,size=20,color='#254E43',lines=1):
    s=clean(s);buf='';out=[]
    for ch in s:
        if draw.textlength(buf+ch,font=font(size))>width and buf:
            out.append(buf);buf=ch
        else:buf+=ch
    if buf:out.append(buf)
    if len(out)>lines:
        out=out[:lines];v=out[-1]
        while v and draw.textlength(v+'…',font=font(size))>width:v=v[:-1]
        out[-1]=v+'…'
    for i,line in enumerate(out):draw.text((xy[0],xy[1]+i*(size+4)),line,font=font(size),fill=color)
    return len(out)


def nine(src,size,border):
    width,height=size;l,b,r,t=border
    if width<l+r+1 or height<t+b+1:
        # Contract thumbnail only; no claim of valid under-minimum nine-slice.
        return ImageOps.contain(src,size,Image.Resampling.LANCZOS)
    sw,sh=src.size;xs=[0,l,sw-r,sw];ys=[0,t,sh-b,sh]
    tx=[0,l,width-r,width];ty=[0,t,height-b,height]
    out=Image.new('RGBA',size)
    for j in range(3):
        for i in range(3):
            patch=src.crop((xs[i],ys[j],xs[i+1],ys[j+1]))
            out.alpha_composite(patch.resize((tx[i+1]-tx[i],ty[j+1]-ty[j]),Image.Resampling.LANCZOS),(tx[i],ty[j]))
    return out


class Board:
    def __init__(self,title,subtitle):
        self.im=Image.new('RGBA',(W,H),'#F7F3E8');self.draw=ImageDraw.Draw(self.im)
        self.used=set();self.layout=[]
        self.draw.rectangle((0,0,W,12),fill='#2D6755')
        self.draw.text((58,30),title,font=font(36),fill='#174F43')
        fit_text(self.draw,subtitle,(60,86),1800,20,'#746B55',2)
        self.draw.text((60,1044),'美术皮肤检查图 · 技术标识仅供复核 · 产品整屏中的实际位置与 Unity 接入仍待验证',font=font(17),fill='#756C55')

    def asset(self,p,box,rotate=0):
        x,y,w,h=map(int,box);src=load(p);entry=ASSETS.get(p,{})
        border=entry.get('borderLeftBottomRightTop',[0,0,0,0])
        if rotate:
            out=ImageOps.contain(src.rotate(rotate,expand=True),(w,h),Image.Resampling.LANCZOS)
        elif any(border)and w>=border[0]+border[2]+1 and h>=border[1]+border[3]+1:
            out=nine(src,(w,h),border)
        else:out=ImageOps.contain(src,(w,h),Image.Resampling.LANCZOS)
        self.im.alpha_composite(out,(x+(w-out.width)//2,y+(h-out.height)//2));self.used.add(p)

    def button(self,label,box,state='normal'):
        self.asset(C+'secondary_'+state+'.png',box)
        x,y,w,h=box
        tw=self.draw.textlength(label,font=font(17))
        self.draw.text((x+(w-tw)/2,y+(h-22)//2-2),label,font=font(17),fill='#284E41')

    def sample(self,c,box):
        x,y,w,h=box;typ=c['sourceWidgetType'];cid=c['controlId']
        title=next((clean(a.get('zhCN'))for a in c.get('sourceLabels',[])if clean(a.get('zhCN')or'')and a.get('zhCN')),None)
        fallback={'spinner':'数值调节','scroll':'列表 / 图表 / 音量等动态区域','viewport':'运行时视口','frame':'窗口框板','caption':'动态标题','closeBox':'关闭','tab':'标签页','checkbox':'勾选项','button':'操作按钮','imgBtn':'图像按钮','flatBtn':'工具按钮','trnBtn':'透明工具按钮','colourBtn':'颜色选择','textBox':'文字输入','dropdownMenu':'下拉选择','progressBar':'进度 / 状态条','label':'动态文字','labelCentred':'居中文字','hiddenButton':'无底图交互热区','placeholder':'运行时替换内容','enum-index-marker':'索引别名：复用对应控件','context-menu-action':'上下文菜单项','external-text-input':'共享密码输入框','resize':'可伸缩区域','groupbox':'分组框板','tableHeader':'表头','empty':'布局占位','horizontalSeparator':'内容分隔'}
        title=title or fallback.get(typ,'共享控件')
        self.draw.rounded_rectangle((x,y,x+w,y+h),radius=14,fill='#FFFDF6',outline='#C8B98C',width=2)
        fit_text(self.draw,c['unit']+' · '+cid,(x+14,y+8),w-28,12,'#79715E',2)
        fit_text(self.draw,title,(x+15,y+43),w-30,21,'#174F43',1)
        bx,by,bw,bh=x+18,y+83,w-36,98
        if typ in ('button','flatBtn','imgBtn','trnBtn','context-menu-action'):
            if re.search(r'(?:^|_)MOVE_(?:UP|DOWN)$',cid):
                self.button('↑'if cid.endswith('UP')else'↓',(bx,by+8,bw,66))
            elif re.search(r'(INCREASE|INCREMENT|_UP$)',cid):
                self.asset(C+'plus.png',(bx,by,70,70));fit_text(self.draw,'增加数值 / 上移（按原控件含义）',(bx+94,by+15),bw-100,18,lines=2)
            elif re.search(r'(DECREASE|DECREMENT|_DOWN$)',cid):
                self.asset(C+'minus.png',(bx,by,70,70));fit_text(self.draw,'减少数值 / 下移（按原控件含义）',(bx+94,by+15),bw-100,18,lines=2)
            else:
                cw=(bw-24)//3
                for j,s in enumerate(['normal','pressed','disabled']):self.button(['普通','按下','禁用'][j],(bx+j*(cw+12),by+8,cw,64),s)
        elif typ=='checkbox':
            for j,s in enumerate(['off','on']):
                self.asset(C+'checkbox_'+s+'.png',(bx+j*190,by,58,58));fit_text(self.draw,'未选中'if s=='off'else'已选中',(bx+67+j*190,by+17),115,18)
        elif typ=='tab':
            cw=(bw-24)//3
            for j,s in enumerate(['normal','selected','disabled']):
                self.asset(C+'tab_'+s+'.png',(bx+j*(cw+12),by,cw,70));fit_text(self.draw,['普通','选中','禁用'][j],(bx+23+j*(cw+12),by+22),cw-46,18)
        elif typ=='spinner':
            self.asset(C+'secondary_normal.png',(bx,by,bw-152,66));fit_text(self.draw,'128  示例值',(bx+24,by+20),bw-200,20)
            self.asset(C+'minus.png',(bx+bw-142,by,66,66));self.asset(C+'plus.png',(bx+bw-66,by,66,66))
        elif typ in ('textBox','dropdownMenu','external-text-input'):
            self.asset(C+'secondary_normal.png',(bx,by,bw,67));fit_text(self.draw,'••••••'if typ=='external-text-input'else'动态文字 / 当前选项',(bx+27,by+20),bw-80,20)
            if typ=='dropdownMenu':self.draw.text((bx+bw-42,by+19),'▾',font=font(22),fill='#285641')
        elif typ=='colourBtn':
            for j,col in enumerate(['#397D60','#F4EACD','#BF994F','#B55745']):
                self.asset(C+'secondary_normal.png',(bx+j*112,by,90,66));self.draw.ellipse((bx+27+j*112,by+16,bx+61+j*112,by+50),fill=col,outline='#665C43',width=1)
        elif typ=='progressBar':
            self.asset(C+'progress_track.png',(bx,by+18,bw,36));self.asset(C+'progress_fill.png',(bx,by+18,int(bw*.64),36));fit_text(self.draw,'64%（动态填充示例）',(bx+15,by-5),bw-30,15)
        elif typ=='scroll':
            self.asset(C+'panel_card.png',(bx,by-1,bw,98))
            for j in range(2):fit_text(self.draw,'动态内容行 '+str(j+1)+'    名称 / 数值 / 状态',(bx+29,by+7+j*30),bw-65,17)
            self.asset(C+'slider_track.png',(bx+bw-22,by+8,17,70),rotate=90);self.asset(C+'slider_thumb.png',(bx+bw-35,by+24,40,40))
        elif typ=='viewport':
            self.asset(C+'panel_card.png',(bx,by-1,bw,98))
            self.asset('assets/backgrounds/park-day-native.png',(bx+15,by+4,150,66))
            fit_text(self.draw,'运行时地图 / 设施 / 实体画面',(bx+184,by+9),bw-207,18,lines=2)
        elif typ=='closeBox':self.asset(C+'close.png',(bx,by,70,70));fit_text(self.draw,'共享关闭控件',(bx+100,by+21),bw-120,20)
        elif typ in ('frame','resize','groupbox','tableHeader'):
            self.asset(C+'panel_card.png',(bx,by-1,bw,98));fit_text(self.draw,'可伸缩内容区 / 分组标题',(bx+45,by+30),bw-90,19)
        elif typ=='caption':
            self.asset(C+'title_plate.png',(bx,by-16,bw,100));fit_text(self.draw,'动态窗口标题',(bx+bw*.30,by+18),bw*.40,21,'#FFF4CD')
        elif typ=='horizontalSeparator':self.draw.line((bx,by+35,bx+bw,by+35),fill='#B89A5E',width=2)
        else:
            fit_text(self.draw,'动态文本 / 布局 / 热区；复用公共框板',(bx+10,by+13),bw-20,19,lines=2)
            if typ in ('label','labelCentred','hiddenButton','placeholder'):fit_text(self.draw,'示例文字  128  玉绿 / 米白',(bx+10,by+46),bw-20,17,'#817452')
        fit_text(self.draw,'目标：'+' / '.join(c['existingPageGroups'])+' · 实际产品位置待接入',(x+15,y+h-25),w-30,12,'#857A65')
        e={'unit':c['unit'],'controlId':cid,'rectTopLeftXYWH':[x,y,w,h],'componentSampleRectTopLeftXYWH':[bx,by,bw,bh],
           'sourceWidgetType':typ,'sourceLabelDisplayed':title,'existingTargetScreenGroups':c['existingPageGroups'],
           'formalAssets':c['artMapping']['formalSpritePaths'],'spriteReuse':True,
           'presence':'displayed_style_contract_only','productScreenshotPlacement':'pending_unverified','unityPlacement':'待接入验证'}
        self.layout.append(e)

    def save(self,path,source_mapping_hash):
        self.im.convert('RGB').save(path)
        refs=[]
        for p in sorted(self.used):
            sp=ROOT/p
            refs.append({'file':p,'sha256':digest(sp),'sourceRecord':p+'.source.json'if Path(str(sp)+'.source.json').exists()else p+'.generation.json'})
        source={'file':path.relative_to(ROOT).as_posix(),'sha256':digest(path),'width':W,'height':H,'format':'PNG','operation':'Deterministic QA contract composition from existing painted shared sprites, native text and technical grid; resizing, valid nine-slice and rotated scrollbar-track review samples. Review thumbnails are not new native AI detail or product placement.',
                'processedAt':datetime.now().astimezone().isoformat(),'route':'deterministic_postprocess_no_AI_call',
                'derivedFrom':refs,'sourceControlMapping':{'file':'docs/control-resource-mapping.json','sha256BeforeDisplayEvidence':source_mapping_hash},
                'font':{'file':FONT.relative_to(ROOT).as_posix(),'license':'OFL-1.1'},'scope':'source control skin contract review only','nativeDetailIncreased':False,
                'unityStatus':'not_imported_not_runtime_validated'}
        write(Path(str(path)+'.source.json'),source)
        write(Path(str(path)+'.layout.json'),{'referenceResolution':[W,H],'purpose':'technical_style_contract_not_product_screen','controls':self.layout})
        return {'file':path.relative_to(ROOT).as_posix(),'sha256':source['sha256'],'sourceRecord':path.relative_to(ROOT).as_posix()+'.source.json','layoutRecord':path.relative_to(ROOT).as_posix()+'.layout.json','controls':self.layout,'usedAssets':sorted(self.used)}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mp=ROOT/'docs/control-resource-mapping.json';mh=digest(mp);m=json.loads(mp.read_text(encoding='utf-8'));cs=m['controls'];boards=[]
    count=math.ceil(len(cs)/12)
    for k in range(count):
        batch=cs[k*12:(k+1)*12]
        b=Board(f'源控件皮肤合同  {k+1:03} / {count:03}',f'云游仙苑（暂名） · OpenRCT2 固定提交 52a55c3e8da5 · 第 {k*12+1}–{k*12+len(batch)} 项 / {len(cs)} · 同一美术资源复用')
        for j,c in enumerate(batch):b.sample(c,(58+(j%3)*607,146+(j//3)*222,590,210))
        path=OUT/f'{k+1:03}-source-controls.png';out=b.save(path,mh);boards.append(out)
        if (k+1)%20==0:print('CONTROL BOARD',k+1,'/',count,flush=True)
    lookup={(c['unit'],c['controlId']):c for c in cs}
    for board in boards:
        for entry in board['controls']:
            c=lookup[entry['unit'],entry['controlId']];c['presence']='displayed_style_contract_only'
            c['productScreenshotPlacement']='pending_unverified'
            c['displayEvidence']=[{'file':board['file'],'sha256':board['sha256'],'layoutRecord':board['layoutRecord'],'rectTopLeftXYWH':entry['rectTopLeftXYWH'],'kind':'technical_style_contract_not_product_screen'}]
            c['presenceNote']='Actual skin sample is bound to this source control on a technical contract board; this does not prove placement on any product screen or runtime behavior.'
    # The three non-WIDX mechanisms have explicit shared-skin contracts too.
    b=Board('动态界面公共皮肤合同','聊天 / 控制台 / 插件自定义窗口 · 内容随运行数据和已安装插件变化，不能枚举任意第三方插件业务')
    dyn=[]
    for i,(unit,typ,label,pages)in enumerate([('Chat','textBox','聊天输入与消息滚动区',['服务器聊天']),('Console','scroll','控制台输入、历史与输出',['调试控制台']),('CustomWindow','tab','插件标签、文字、列表与按钮',['自定义插件窗口'])]):
        c={'unit':unit,'controlId':'DYNAMIC_SHARED_SKIN_ROLE','sourceWidgetType':typ,'sourceLabels':[{'zhCN':label}],'existingPageGroups':pages,'artMapping':{'formalSpritePaths':[C+'panel_card.png',C+'secondary_normal.png']}}
        b.sample(c,(58+i*607,210,590,210));dyn.append({'unit':unit,'sourceFile':m['otherUiUnits'][i],'contentScope':'shared_skin_only; arbitrary plugin content is not enumerated'})
    dpath=OUT/'121-dynamic-shared-roles.png';dout=b.save(dpath,mh)
    for item,entry in zip(dyn,dout['controls']):item.update(displayEvidence={'file':dout['file'],'rectTopLeftXYWH':entry['rectTopLeftXYWH']},productScreenshotPlacement='pending_unverified')
    evidence={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(),'scope':'source_control_style_contract_only','sourceReferenceCommit':m['referenceCommit'],'sourceMappingInputSha256':mh,
              'sourceControlCount':len(cs),'interactiveCandidateCount':m['counts']['interactiveCandidatesExcludingSourceResolvedStructureAndLexicalMarkers'],'sourceBoards':boards,'dynamicSharedBoard':dout,'dynamicRoles':dyn,
              'counts':{'sourceControlSheets':len(boards),'dynamicRoleSheets':1,'sourceStyleBindings':sum(len(b['controls'])for b in boards),'productScreenBindingsVerified':0},
              'acceptanceBoundary':'Every source control has an actual painted skin style sample and shared-resource mapping. This contract does not assert exact product-screen placement, source pixel equivalence, full functional UI implementation, Unity import or engine verification.'}
    write(ROOT/'docs/control-display-evidence.json',evidence)
    m['counts']['presence']=dict(Counter(c['presence']for c in cs));m['styleContractEvidence']='docs/control-display-evidence.json';m['productScreenshotPlacement']='pending_unverified'
    write(mp,m)
    print('DONE',len(boards),'source boards + 1 dynamic board,',len(cs),'source style bindings. Product-screen placement remains unverified.',flush=True)


if __name__=='__main__':main()
