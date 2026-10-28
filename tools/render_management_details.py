"""Additional actual product UI layouts for management/editor native controls.

Uses the existing painted art kit and OFL fonts. Every displayed native control
is explicitly bound to its source unit/ID and actual product rectangle. No
technical IDs are printed on the player-facing images. No AI or Unity calls.
"""
from pathlib import Path
import sys
import re
import json
import math
from collections import Counter
from datetime import datetime

from render_screens import Canvas, AssetStore, ROOT, rel, write_json, digest, JADE, DEEP, MUTED, CREAM, GOLD

sys.path.insert(0,str(ROOT/'docs'))
from control_mapping_builder import localization

MAP=json.loads((ROOT/'docs/control-resource-mapping.json').read_text(encoding='utf-8'))
INV=json.loads((ROOT/'docs/repo-ui-inventory.json').read_text(encoding='utf-8'))
REC={r['windowUnit']:r for r in INV}
CS={(c['unit'],c['controlId']):c for c in MAP['controls']}
REPO=ROOT/'reference/OpenRCT2'
OUT=ROOT/'designs/details/management'
LOC=localization()
SCREENS=[]
STORE=AssetStore(ROOT)


def cleaned(v):
    return re.sub(r'\s+',' ',re.sub(r'\{[^}]*\}','',str(v))).strip(' :：')


def label_for(unit,cid):
    overrides={
      'WIDX_MONEY_SPINNER':'目标金额','WIDX_YEAR_BOX':'年份','WIDX_MONTH_BOX':'月份','WIDX_DAY_BOX':'日期',
      'WIDX_GIVE_GUESTS_MONEY':'向全部游客发放现金','WIDX_STAFF_SPEED':'员工速度',
      'WIDX_DISABLE_GRASS_GROWING':'停止草地生长','WIDX_PARK_RATING_SPINNER':'固定公园评分',
      'WIDX_GUEST_RIDE_INTENSITY_MORE_THAN_1':'游客强度偏好：大于 1',
      'WIDX_GUEST_RIDE_INTENSITY_LESS_THAN_15':'游客强度偏好：小于 15',
      'WIDX_THEMES_RCT1_BOTTOM_TOOLBAR':'经典版底部状态栏','WIDX_THEMES_USE_3D_IMAGE_BUTTONS':'立体图像按钮样式',
    }
    if cid in overrides:return overrides[cid]
    c=CS[unit,cid]
    for a in c['sourceLabels']:
        if a.get('zhCN'):
            s=cleaned(a['zhCN'])
            if s and s not in ['▼','▲']:return s
    raise ValueError('Untranslated source control '+unit+' '+cid)


class Detail:
    def __init__(self,unit,slug,subheading,active_tab=None,condition=''):
        self.unit=unit;self.slug=slug;self.bindings=[];self.condition=condition
        r=REC[unit];self.c=Canvas(STORE,'management-detail:'+slug,r['title']+' · '+subheading)
        active_tab=active_tab or r['tabs'][0]
        idx=r['tabs'].index(active_tab)if active_tab in r['tabs']else 0
        self.box=self.c.frame(r,active_tab,idx)
        self.c.text(subheading,(self.box[0]+5,865,self.box[2]-10,36),23,color=MUTED,minimum=21)
        if condition:self.c.text(condition,(116,1002,1660,30),18,color=DEEP,minimum=18,align='center')
        # Source-window frame/title/close are real drawn controls too.
        roles={'frame':'panel','caption':'title-plaque','closeBox':'close'}
        for cid in r['controlIds']:
            s=CS.get((unit,cid))
            if not s:continue
            if s['sourceWidgetType']in roles and re.search(r'BACKGROUND|TITLE$|CLOSE$',cid):
                candidates=[w for w in self.c.widgets if w['role']==roles[s['sourceWidgetType']]]
                if candidates:self.bind(cid,candidates[0]['region'],'window-structure')
        tabs=[c for c in MAP['controls']if c['unit']==unit and c['sourceWidgetType']=='tab']
        nav=[w for w in self.c.widgets if w['role']=='navigation-tab']
        if len(tabs)==len(r['tabs'])and len(nav)==len(tabs):
            for c,w in zip(sorted(tabs,key=lambda v:v['enumValue']),nav):self.bind(c['controlId'],w['region'],'source-navigation')

    def bind(self,cid,rect,role,subpart=None):
        if (self.unit,cid)not in CS:raise KeyError((self.unit,cid))
        e={'unit':self.unit,'controlId':cid,'sourceControlKey':self.unit+':'+cid,
           'rectTopLeftXYWH':list(map(int,rect)),'role':role,'sourcePageGroups':CS[self.unit,cid]['existingPageGroups'],
           'sourceEvidence':CS[self.unit,cid]['sourceEvidence']['definition'],'sourceWidgetType':CS[self.unit,cid]['sourceWidgetType'],
           'condition':self.condition,'productPlacement':'explicit_source_bound_product_layout','unityStatus':'not_integrated'}
        if subpart:e['subpart']=subpart
        self.bindings.append(e)
        return e

    def button(self,cid,label,box,primary=False,state='normal'):
        self.c.button(label,box,primary=primary,state=state)
        self.c.widgets[-1]['sourceControlKey']=self.unit+':'+cid
        self.bind(cid,box,'button')

    def check(self,cid,label,box,checked=False):
        x,y,w,h=box
        self.c.place('checkbox_on'if checked else'checkbox_off',(x,y+12,40,40),role='detail-checkbox')
        self.c.widgets[-1]['sourceControlKey']=self.unit+':'+cid
        self.c.text(label,(x+57,y+7,w-62,h-8),22,minimum=19)
        self.bind(cid,box,'checkbox')

    def input(self,cid,label,value,box,kind='input',arrow=None,minus=None,plus=None):
        x,y,w,h=box;lw=min(285,w*.43);cx=x+lw+12;cw=w-lw-12
        self.c.text(label,(x+5,y+8,lw-10,h-10),23,minimum=20)
        self.c.place('secondary_normal',(cx,y+1,cw,h-4),mode='nine',role='detail-'+kind)
        self.c.widgets[-1]['sourceControlKey']=self.unit+':'+cid
        self.bind(cid,(cx,y+1,cw,h-4),kind)
        right_reserved=115 if plus else 46 if arrow else 14
        self.c.text(value,(cx+43,y+12,cw-50-right_reserved,h-22),22,minimum=19,valign='center')
        if plus:
            for n,glyph,cid2 in [(0,'minus',minus),(1,'plus',plus)]:
                b=(cx+cw-111+n*54,y+5,49,49)
                self.c.place(glyph,b,role='numeric-stepper')
                self.c.widgets[-1]['sourceControlKey']=self.unit+':'+cid2;self.bind(cid2,b,'numeric-stepper')
        if arrow:
            ab=(cx+cw-47,y+5,40,h-12)
            self.c.text('▼',ab,25,align='center',minimum=22)
            self.bind(arrow,ab,'dropdown-arrow')

    def color(self,cid,label,box,color='#397D60',subpart=None):
        x,y,w,h=box;self.c.place('secondary_normal',box,mode='nine',role='detail-color-button')
        self.c.draw.ellipse((x+w/2-14,y+h/2-14,x+w/2+14,y+h/2+14),fill=color,outline='#9B7C3F',width=2)
        self.c.shapes.append({'role':'dynamic-color-swatch','rect':[int(x+w/2-14),int(y+h/2-14),28,28],'color':color})
        self.bind(cid,box,'color-button',subpart)

    def save(self):
        path=OUT/(self.slug+'.png');r=REC[self.unit]
        meta={'referenceCommit':MAP['referenceCommit'],'sourceFiles':r['sourceFiles'],'unit':self.unit,
              'purpose':'additional_actual_product_ui_layout','condition':self.condition,
              'copyAndValues':'Localized design copy and sample values; no source code IDs printed on product image',
              'redesignAssumptions':'Dense source options may be split into coherent additional pages; this changes layout/navigation organization, not business mechanics.'}
        out=self.c.save(path,meta)
        lp=path.with_suffix('.layout.json');d=json.loads(lp.read_text(encoding='utf-8'));d['sourceControlBindings']=self.bindings;d['productDetailPurpose']=meta['purpose'];write_json(lp,d)
        entry={'screenId':self.c.identity,'category':'product-detail','unit':self.unit,'windowKey':r['key'],'title':self.c.title,
               'tab':self.slug,'sourceControlBindings':self.bindings,'sourceControlKeys':sorted(set(b['sourceControlKey']for b in self.bindings)),
               'sourceFiles':r['sourceFiles'],'condition':self.condition,**out}
        SCREENS.append(entry);print('DETAIL',self.slug,'bindings',len(self.bindings),'issues',len(self.c.issues),flush=True)


def rows_for(d,items):
    x,y,w,h=d.box;cw=(w-36)/2;gap=min(78,h/7)
    for i,item in enumerate(items):
        bx=x+(i%2)*(cw+36)+4;by=y+(i//2)*gap
        c=item['control'];cid=c['controlId'];kind=c['sourceWidgetType'];box=(bx,by,cw-8,68)
        label=item.get('label')or label_for(d.unit,cid)
        if kind=='checkbox':d.check(cid,label,box,checked=False)
        elif kind=='spinner':d.input(cid,label,item.get('value','128'),box,'spinner',minus=item['minus'],plus=item['plus'])
        elif kind=='dropdownMenu':d.input(cid,label,item.get('value','普通'),box,'dropdown',arrow=item['arrow'])
        else:d.button(cid,label,(bx,by+2,cw-8,62),primary=False)


def source_items(unit,tab):
    cs=[c for c in MAP['controls']if c['unit']==unit and not c['excludedFromInteractiveCount']and tab in c['existingPageGroups']]
    used=set();out=[]
    for c in cs:
        cid=c['controlId']
        if cid in used:continue
        it={'control':c}
        if c['sourceWidgetType']in('spinner','dropdownMenu'):
            siblings={s['enumValue']:s for s in cs if s['sourceWidgetArray']==c['sourceWidgetArray']}
            if c['sourceWidgetType']=='spinner':
                up=siblings[c['enumValue']+1];down=siblings[c['enumValue']+2]
                it.update(plus=up['controlId'],minus=down['controlId']);used.update([up['controlId'],down['controlId']])
            else:
                ar=siblings[c['enumValue']+1];it['arrow']=ar['controlId'];used.add(ar['controlId'])
        out.append(it);used.add(cid)
    return out


def cheats():
    values={'WIDX_MONEY_SPINNER':'500000','WIDX_YEAR_BOX':'3','WIDX_MONTH_BOX':'6','WIDX_DAY_BOX':'15','WIDX_PARK_RATING_SPINNER':'820'}
    for tab in REC['Cheats']['tabs']:
        items=source_items('Cheats',tab)
        if tab=='游客':
            # The original min/max buttons refer to seven distinct needs; keep
            # that meaning explicit instead of showing fourteen unlabeled max/mins.
            pairs=[('HAPPINESS','幸福感'),('ENERGY','体力'),('HUNGER','饥饿'),('THIRST','口渴'),('NAUSEA','眩晕'),('NAUSEA_TOLERANCE','耐眩晕程度'),('TOILET','如厕需求')]
            d=Detail('Cheats','cheats-guests-needs','游客需求与强度偏好','游客','沙盒工具已启用；这些按钮直接修改当前游客数据。')
            x,y,w,h=d.box
            for i,(stem,label)in enumerate(pairs):
                by=y+i*75;d.c.text(label,(x+18,by+11,520,54),26,minimum=23)
                d.button('WIDX_GUEST_'+stem+'_MIN','设为最小',(x+650,by+2,275,62))
                d.button('WIDX_GUEST_'+stem+'_MAX','设为最大',(x+955,by+2,275,62))
            d.c.actions(['返回游客工具']);d.save()
            items=[a for a in items if not re.search(r'WIDX_GUEST_(?:HAPPINESS|ENERGY|HUNGER|THIRST|NAUSEA|NAUSEA_TOLERANCE|TOILET)_(?:MAX|MIN)$',a['control']['controlId'])]
        for it in items:
            if it['control']['controlId']in values:it['value']=values[it['control']['controlId']]
            if it['control']['controlId']=='WIDX_WEATHER':it['value']='晴朗'
        for page in range(math.ceil(len(items)/14)):
            group=items[page*14:(page+1)*14]
            name='沙盒'+tab+'工具'+(' · '+str(page+1)if len(items)>14 else'')
            d=Detail('Cheats','cheats-'+str(REC['Cheats']['tabs'].index(tab)+1)+'-'+str(page+1),name,tab,'沙盒工具已启用；当前示例具有操作权限，变更即时生效。')
            rows_for(d,group);d.c.actions(['返回园区']);d.save()


def scenery():
    d=Detail('Scenery','scenery-complete-tools','景观搜索、取色与布置','主题','当前对象支持三种配色；对象可用颜色以其定义为准。')
    x,y,w,h=d.box;left=760
    d.input('WIDX_FILTER_TEXT_BOX','搜索景物','', (x,y,left-130,66),'text')
    d.button('WIDX_FILTER_CLEAR_BUTTON','清除',(x+left-120,y+3,145,62))
    d.c.panel((x,y+86,left,h-86));d.bind('WIDX_SCENERY_LIST',(x,y+86,left,h-86),'object-catalog-list')
    for i,(name,icon)in enumerate([('流云路灯','lantern'),('桃花树','peach_flowers'),('休憩长椅','bench')]):
        yy=y+108+i*104;d.c.icon(0,(x+47,yy,88,88),icon);d.c.text(name,(x+162,yy+24,370,46),27,minimum=24)
    rx=x+left+45
    for i,(cid,label)in enumerate([('WIDX_SCENERY_ROTATE_OBJECTS_BUTTON','旋转 90°'),('WIDX_SCENERY_REPAINT_SCENERY_BUTTON','重涂景物'),('WIDX_SCENERY_EYEDROPPER_BUTTON','吸取景物'),('WIDX_SCENERY_BUILD_CLUSTER_BUTTON','随机成簇摆放')]):
        d.button(cid,label,(rx+(i%2)*400,y+(i//2)*94,375,66))
    d.c.text('主色 / 第二色 / 第三色',(rx+5,y+205,730,40),25)
    for i,cid in enumerate(['WIDX_SCENERY_PRIMARY_COLOUR_BUTTON','WIDX_SCENERY_SECONDARY_COLOUR_BUTTON','WIDX_SCENERY_TERTIARY_COLOUR_BUTTON']):d.color(cid,'',(rx+i*245,y+258,215,76),['#397D60','#E4D8B3','#C09048'][i])
    d.c.text('点击园区中的景物，可重涂或选取同种景物。',(rx+8,y+367,750,77),23,color=MUTED,minimum=21)
    d.c.actions(['返回园区']);d.save()
    d=Detail('Scenery','scenery-editor-restriction','场景编辑器 · 景物限制','重涂','仅在场景编辑器或具备沙盒权限的模式中使用。')
    x,y,w,h=d.box;d.c.viewport((x,y,w*.48,h),'已选景物：流云路灯')
    d.c.text('限制对象',(x+w*.53,y+25,w*.43,50),30,family='title')
    d.c.text('将所选景物限制为仅在场景编辑器和沙盒中可用。',(x+w*.53,y+100,w*.43,130),27,minimum=24)
    d.button('WIDX_RESTRICT_SCENERY','限制所选对象',(x+w*.53,y+285,w*.42,74),primary=True)
    d.c.actions(['返回景观']);d.save()


def editor_objects():
    for expanded in [False,True]:
        d=Detail('EditorObjectSelection','editor-object-'+('source-filter-open'if expanded else'complete-selection'),'设施对象 · 分类与来源筛选','设施车辆','重载按钮仅在已开启调试工具时显示；此图为已开启状态。')
        x,y,w,h=d.box
        d.input('WIDX_FILTER_DROPDOWN','素材来源','全部来源',(x,y,610,64),'dropdown',arrow='WIDX_FILTER_DROPDOWN_BTN')
        d.input('WIDX_FILTER_TEXT_BOX','搜索','过山车',(x+635,y,560,64),'text')
        d.button('WIDX_FILTER_CLEAR_BUTTON','清除',(x+1215,y+2,180,60))
        subtabs=['全部','交通','温和','过山车','惊险','水上','商店摊位']
        for i,name in enumerate(subtabs):
            box=(x+i*200,y+80,190,58);d.c.place('tab_selected'if i==3 else'tab_normal',box,mode='nine',role='object-subcategory')
            d.c.text(name,(box[0]+18,box[1]+12,154,36),22,family='title',align='center',minimum=21,color=CREAM if i==3 else DEEP)
            d.bind('WIDX_SUB_TAB_'+str(i),box,'source-subcategory-tab')
        listbox=(x,y+154,870,h-154);d.c.panel(listbox);d.bind('WIDX_LIST',listbox,'object-selection-list')
        d.button('WIDX_LIST_SORT_TYPE','按设施类型排序',(x+50,y+166,365,58))
        d.button('WIDX_LIST_SORT_RIDE','按名称排序',(x+440,y+166,380,58))
        for i,name in enumerate(['木质过山车','钢制过山车','悬挂过山车','发射过山车']):
            yy=y+240+i*65;d.c.place('checkbox_on'if i<2 else'checkbox_off',(x+60,yy,38,38),role='object-selection-checkbox');d.c.text(name,(x+118,yy+3,630,46),25,minimum=23)
        pb=(x+910,y+155,w-910,h-155);d.c.panel(pb);d.bind('WIDX_PREVIEW',pb,'selected-object-preview')
        d.c.illustration(0,(pb[0]+30,pb[1]+22,pb[2]-60,220),'dragon_coaster');d.c.text('钢制过山车 · 已选择',(pb[0]+28,pb[1]+255,pb[2]-56,80),25,minimum=22,align='center')
        d.button('WIDX_INSTALL_TRACK','安装轨道设计',(1080,916,310,70))
        d.button('WIDX_RELOAD_OBJECT','重载所选对象',(1415,916,350,70))
        if expanded:
            popup=(1020,285,735,570);d.c.panel(popup);d.bind('WIDX_FILTER_DROPDOWN',popup,'expanded-source-filter-options')
            d.c.text('素材来源与选择状态',(1054,310,666,55),30,family='title')
            labels=['RCT1 基础','RCT1 AA 扩展','RCT1 LL 扩展','RCT2 基础','RCT2 WW 扩展','RCT2 TT 扩展','官方扩展对象','自定义对象','已选择对象','未选择对象']
            for i,name in enumerate(labels):
                d.c.checkbox(name,(1054+(i%2)*340,382+(i//2)*76,320,62),i in(3,4,5,7,8,9))
            d.c.text('选项即时切换；再次点击来源选择器关闭。',(1056,800,650,38),20,color=MUTED,minimum=19)
        d.save()


def theme_descriptors():
    t=(REPO/'src/openrct2-ui/interface/Theme.cpp').read_text(encoding='utf-8-sig');out={}
    for line in t.splitlines():
        m=re.search(r'\{ WindowClass::(\w+),\s*"WC_[^"]+",\s*(STR_\w+),\s*\{(.*?)\}\s*\}',line)
        if m:
            wc,sid,cols=m.groups()
            names={'gameStatusBar':'游戏状态栏','newsTicker':'经营消息条','parkInfoPanel':'公园信息面板','dateInfoPanel':'日期天气面板','editorStepControlScenario':'场景步骤导航','editorStepControlTrack':'轨道工具导航'}
            out[wc]=(cleaned(LOC.get(sid,{}).get('zhCN')or names.get(wc,wc)),len(re.findall(r'(?:opaque|translucent)\(',cols)))
    return out


def themes():
    d=Detail('Themes','themes-custom-management','自定义主题管理','主题','当前选择为自定义主题；颜色与透明变化即时生效。')
    x,y,w,h=d.box;d.input('WIDX_THEMES_PRESETS','当前主题','玉绿游园 · 自定义',(x+10,y+10,w-20,70),'dropdown',arrow='WIDX_THEMES_PRESETS_DROPDOWN')
    d.c.illustration(11,(x+70,y+128,530,340),'mountain_scenario')
    for i,(cid,lab)in enumerate([('WIDX_THEMES_DUPLICATE_BUTTON','复制当前主题'),('WIDX_THEMES_RENAME_BUTTON','重命名主题'),('WIDX_THEMES_DELETE_BUTTON','删除当前主题')]):d.button(cid,lab,(x+710,y+145+i*115,550,76),primary=i==0)
    d.c.actions(['返回设置']);d.save()
    desc=theme_descriptors();t=(REPO/'src/openrct2-ui/windows/Themes.cpp').read_text(encoding='utf-8-sig')
    class_arrays=dict((m.group(1),re.findall(r'WindowClass::(\w+)',m.group(2)))for m in re.finditer(r'kThemesTab(\w+)Classes\s*=\s*std::to_array<WindowClass>\(\{([\s\S]*?)\}\)',t))
    array_tabs={'Main':'主界面','Park':'公园','Tools':'工具','RidesGuests':'设施游客','Editors':'编辑器','Misc':'杂项','Prompts':'弹窗'}
    for arr,tab in array_tabs.items():
        classes=class_arrays[arr]
        for page in range(math.ceil(len(classes)/6)):
            d=Detail('Themes','themes-'+arr.lower()+'-'+str(page+1),tab+' · 窗口配色 '+str(page+1),tab,'每个颜色槽可独立设色与透明；未出现的颜色槽表示该窗口没有此槽。')
            x,y,w,h=d.box
            for cid,lab,b in [('WIDX_THEMES_HEADER_WINDOW','窗口',(x+25,y,w*.37,48)),('WIDX_THEMES_HEADER_PALETTE','调色板',(x+w*.40,y,350,48)),('WIDX_THEMES_HEADER_TRANSPARENCY','逐色透明',(x+w*.73,y,w*.24,48))]:d.c.text(lab,b,27,family='title');d.bind(cid,b,'table-header')
            region=(x,y+56,w,h-56);d.c.panel(region);d.bind('WIDX_THEMES_LIST',region,'per-window-theme-editing-table')
            for i,wc in enumerate(classes[page*6:(page+1)*6]):
                name,n=desc[wc];yy=y+68+i*76;d.c.text(name,(x+60,yy+12,w*.34-36,50),24,minimum=21)
                for j in range(n):
                    cb=(x+w*.40+j*73,yy+8,64,48);d.color('WIDX_THEMES_COLOURBTN_MASK','',cb,['#397D60','#F3E8CC','#BF994F','#6D958A'][j%4],{'windowClass':wc,'paletteIndex':j})
                    b=(x+w*.73+j*56,yy+14,34,34);d.c.place('checkbox_on'if i==1 and j==0 else'checkbox_off',b,role='per-color-transparency')
                    d.bind('WIDX_THEMES_LIST',b,'per-color-transparency',{'windowClass':wc,'paletteIndex':j})
            d.c.actions(['返回设置']);d.save()
    d=Detail('Themes','themes-feature-options','经典样式与显示特性','特性','样式开关只改变界面表现；当前为自定义主题。')
    ids=['WIDX_THEMES_RCT1_RIDE_LIGHTS','WIDX_THEMES_RCT1_PARK_LIGHTS','WIDX_THEMES_RCT1_SCENARIO_FONT','WIDX_THEMES_RCT1_BOTTOM_TOOLBAR','WIDX_THEMES_USE_3D_IMAGE_BUTTONS']
    labels=['经典版设施开关指示灯','经典版公园开关指示灯','经典版场景选择字体','经典版底部状态栏','立体图像按钮样式']
    x,y,w,h=d.box
    for i,(cid,lab)in enumerate(zip(ids,labels)):d.check(cid,lab,(x+25,y+i*90,w-60,76),i==4)
    d.c.actions(['返回设置']);d.save()


def inventions():
    d=Detail('EditorInventionsList','editor-inventions-complete-tools','研究顺序与对象预览','已研究','拖动可在两栏间移动并重排；场景中已使用的设施保持已研究。')
    x,y,w,h=d.box;col=550
    for i,(cid,title)in enumerate([('WIDX_PRE_RESEARCHED_SCROLL','已研究'),('WIDX_RESEARCH_ORDER_SCROLL','待研究顺序')]):
        b=(x+i*(col+30),y,col,h);d.c.panel(b);d.bind(cid,b,'research-order-list')
        d.c.text(title,(b[0]+30,y+25,col-60,50),28,family='title')
        for j,name in enumerate(['云游小火车','旋转木马','游龙飞车','竹影水道']):d.c.text(str(j+1)+'  '+name,(b[0]+30,y+104+j*76,col-60,52),26,minimum=23)
    px=x+2*(col+30);pb=(px,y,w-2*(col+30),240);d.c.panel(pb);d.bind('WIDX_PREVIEW',pb,'selected-research-object-preview');d.c.illustration(0,(px+15,y+15,pb[2]-30,210),'dragon_coaster')
    for i,(cid,label)in enumerate([('WIDX_MOVE_ITEMS_TO_TOP','全部移至已研究'),('WIDX_MOVE_ITEMS_TO_BOTTOM','全部移至待研究'),('WIDX_RANDOM_SHUFFLE','随机待研究顺序')]):d.button(cid,label,(px,y+267+i*78,pb[2],66))
    d.c.actions(['下一步','返回']);d.save()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cheats();scenery();editor_objects();themes();inventions()
    coverage={}
    for e in SCREENS:
        for b in e['sourceControlBindings']:coverage.setdefault(b['sourceControlKey'],[]).append({'file':e['file'],'layoutFile':e['layoutFile'],'rectTopLeftXYWH':b['rectTopLeftXYWH'],'role':b['role'],'condition':b['condition']})
    owned=['Cheats','Scenery','EditorObjectSelection','Themes','EditorInventionsList']
    remaining=[c['unit']+':'+c['controlId']for c in MAP['controls']if c['unit']in owned and not c['excludedFromInteractiveCount']and c['unit']+':'+c['controlId']not in coverage]
    manifest={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(),'scope':'additional_actual_product_ui_not_style_contract_boards','referenceCommit':MAP['referenceCommit'],
              'screens':SCREENS,'images':SCREENS,'screenCount':len(SCREENS),'sourceControlCoverage':coverage,'explicitSourceSymbolCount':len(coverage),
              'explicitInteractiveSourceCount':sum(not CS[tuple(k.split(':',1))]['excludedFromInteractiveCount']for k in coverage),'ownedUnits':owned,
              'remainingOwnedInteractiveControls':remaining,'layoutIssueCount':sum(len(e['layoutIssues'])for e in SCREENS),
              'nativeArtClaim':False,'unityStatus':'not_integrated_not_runtime_validated','redesignPolicy':'Same source operations; dense original windows may use additional coherent product pages. All IDs are metadata only.'}
    write_json(ROOT/'docs/management-detail-manifest.json',manifest)
    print('DONE screens',len(SCREENS),'source symbols',len(coverage),'remaining interactive',remaining,'layout issues',manifest['layoutIssueCount'],flush=True)


if __name__=='__main__':main()
