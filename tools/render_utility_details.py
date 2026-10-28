"""Player-facing utility layouts using the approved painted kit, not source boards.

Source IDs are metadata only. No generation, Git, F-drive writes or Unity calls.
"""
import json
from datetime import datetime
from pathlib import Path
import render_management_details as m
from render_screens import ROOT, rel, write_json, JADE, DEEP, MUTED, CREAM, GOLD

m.OUT = ROOT / 'designs/details/utility'
m.SCREENS = []


class Detail(m.Detail):
    def __init__(self, unit, slug, title, tab=None, condition=''):
        original=m.REC[unit]['title']
        m.REC[unit]['title']={'GuestList':'游客列表','NewRide':'新建设施','RideList':'设施总览','LoadSave':'保存与读取','StaffList':'员工管理'}[unit]
        super().__init__(unit, slug, title, tab, condition)
        m.REC[unit]['title']=original
        self.c.identity = 'utility-detail:' + slug

    def button(self,cid,label,box,primary=False,state='normal'):
        has_arrow='▼'in label
        super().button(cid,label.replace('▼','').strip(),box,primary,state)
        if has_arrow:
            x,y,w,h=box
            self.c.text('▼',(x+w-44,y+14,30,h-25),21,family='body',minimum=19,align='center')

    def menu(self, cid, choices, box, checked=None):
        x,y,w,h=box
        self.c.panel(box)
        rh=h/len(choices)
        for i,label in enumerate(choices):
            b=(x+24,y+i*rh+8,w-48,rh-16)
            if i==checked:self.c.place('secondary_selected',b,mode='nine',role='menu-selected-item')
            self.c.text(label,(b[0]+35,b[1]+1,b[2]-70,b[3]-2),24,minimum=21)
            self.bind(cid,b,'opened-menu-item',{'optionLabel':label})

    def table(self,cid,headers,rows,box):
        x,y,w,h=box;self.c.panel(box);self.bind(cid,box,'selectable-data-list')
        widths=[w*.38]+[w*.62/(len(headers)-1)]*(len(headers)-1)
        px=x+35
        for head,cw in zip(headers,widths):
            self.c.text(head,(px,y+20,cw-45,44),25,family='title',minimum=22);px+=cw
        rh=min(78,(h-95)/max(len(rows),1))
        for i,row in enumerate(rows):
            px=x+35;yy=y+83+i*rh
            if i==0:self.c.place('secondary_selected',(x+20,yy-3,w-40,rh-7),mode='nine',role='selected-data-row')
            for text,cw in zip(row,widths):
                self.c.text(str(text),(px,yy+8,cw-48,rh-19),23,minimum=20);px+=cw


def new_ride():
    for slug,tab,disabled in [('newride-search-group','温和',False),('newride-shop-group-disabled','商店摊位',True)]:
        d=Detail('NewRide',slug,'设施目录搜索与分类',tab,'商店与服务类不支持按轨道类型分组；研发页不显示搜索工具。'if disabled else'按设施类型分组可将同类载具归到一类；清除按钮重置名称搜索。')
        x,y,w,h=d.box
        d.input('WIDX_FILTER_TEXT_BOX','搜索设施','',(x,y,w-330,68),'text')
        d.button('WIDX_FILTER_CLEAR_BUTTON','清除搜索',(x+w-300,y+2,285,63))
        d.check('WIDX_GROUP_BY_TRACK_TYPE','按设施类型分类'+(' · 不适用于本类别'if disabled else''),(x+5,y+82,w-10,68),not disabled)
        if disabled:
            # Keep a true disabled art state over the control, not an active toggle.
            d.c.place('secondary_disabled',(x+5,y+94,42,42),role='disabled-grouping-control')
        b=(x,y+173,w,h-173);d.c.panel(b);d.bind('WIDX_RIDE_LIST',b,'selectable-facility-catalog')
        entries=[('云纹茶摊','tea_kiosk'),('玉露饮品','tea_kiosk'),('竹影茶亭','tea_kiosk')]if disabled else[('葫芦旋转木马','gourd_carousel'),('玉轮观景轮','celestial_wheel'),('云台升降塔','observation_lift')]
        for i,(name,icon)in enumerate(entries):
            bx=x+22+i*w/3;d.c.illustration(0,(bx+20,y+199,150,150),icon)
            d.c.text(name,(bx+183,y+231,w/3-210,80),27,minimum=23)
        d.c.actions(['返回园区']);d.save()
    d=Detail('NewRide','newride-research-shortcuts','新设施研发入口','研发','有金钱模式显示研发资金入口；无金钱模式隐藏资金入口。')
    x,y,w,h=d.box
    d.c.panel((x,y,w*.54,h));d.c.text('当前研发：竹影水上设施',(x+45,y+40,w*.49,60),30,family='title')
    d.c.text('进度 68% · 正在设计\n预计完成：六月下旬',(x+45,y+153,w*.48,150),28,minimum=24)
    d.button('WIDX_LAST_DEVELOPMENT_BUTTON','查看上一项研发详情',(x+w*.59,y+92,w*.39,82))
    d.button('WIDX_RESEARCH_FUNDING_BUTTON','研发资金与优先项目',(x+w*.59,y+242,w*.39,82),primary=True)
    d.c.actions(['返回园区']);d.save()


def guest_list():
    d=Detail('GuestList','guestlist-individual-tools','查找、追踪与信息切换','个体','当前是从汇总项进入的游客筛选列表，故显示地图高亮入口；分页仅在超过一页时出现。')
    x,y,w,h=d.box
    d.input('WIDX_INFO_TYPE_DROPDOWN','列表信息','游客行动',(x,y,760,66),'dropdown',arrow='WIDX_INFO_TYPE_DROPDOWN_BUTTON')
    d.input('WIDX_PAGE_DROPDOWN','页码','第 1 页',(x+800,y,w-800,66),'dropdown',arrow='WIDX_PAGE_DROPDOWN_BUTTON')
    for i,(cid,label)in enumerate([('WIDX_FILTER_BY_NAME','按姓名查找'),('WIDX_TRACKING','仅追踪中的游客'),('WIDX_MAP','在地图高亮游客')]):d.button(cid,label,(x+i*(w/3)+4,y+83,w/3-22,65),state='selected'if i==1 else'normal')
    d.table('WIDX_GUEST_LIST',['游客','当前行动','追踪'],[['小云','正在排队','已追踪'],['阿青','在步道上闲逛','已追踪'],['圆圆','前往游龙飞车','已追踪']],(x,y+170,w,h-170))
    d.c.actions(['返回游客汇总']);d.save()
    d=Detail('GuestList','guestlist-information-menu','游客列表的信息类别','个体','源功能只提供“行动”和“想法”两种列表信息；姓名筛选按钮再次点击会清除筛选。')
    x,y,w,h=d.box
    d.input('WIDX_INFO_TYPE_DROPDOWN','列表信息','游客想法',(x,y,760,66),'dropdown',arrow='WIDX_INFO_TYPE_DROPDOWN_BUTTON')
    d.menu('WIDX_INFO_TYPE_DROPDOWN_BUTTON',['游客行动','游客想法'],(x+275,y+78,480,180),1)
    d.button('WIDX_FILTER_BY_NAME','清除姓名筛选：小云',(x+850,y+12,w-880,73),state='selected')
    d.table('WIDX_GUEST_LIST',['游客','最新想法'],[['小云','这里的景色真好！'],['小云仙','我想乘坐游龙飞车']],(x+850,y+127,w-850,h-127))
    d.c.text('查找游客\n输入姓名片段可筛选列表，最多 32 个字符。',(x+30,y+310,735,160),28,minimum=24)
    d.c.actions(['返回游客列表']);d.save()
    d=Detail('GuestList','guestlist-summarised-tools','游客行动与想法汇总','汇总','汇总页不显示姓名筛选、追踪或地图按钮；点选一行进入对应的个体筛选列表。')
    x,y,w,h=d.box
    d.input('WIDX_INFO_TYPE_DROPDOWN','汇总内容','游客想法',(x,y,900,67),'dropdown',arrow='WIDX_INFO_TYPE_DROPDOWN_BUTTON')
    d.table('WIDX_GUEST_LIST',['想法分组','游客数量'],[['这里的景色真好！','126'],['我想喝点东西','42'],['我正在找出口','9']],(x,y+95,w,h-95))
    d.c.actions(['返回园区']);d.save()


def ride_list():
    for mode in ['menu','lights','client']:
        condition={'menu':'默认主题使用“全部开关”菜单；点击列标题切换排序方向。','lights':'启用经典设施指示灯样式，分别使用全部关闭和全部开放按钮。','client':'多人客户端隐藏快速拆除入口；批量开关仍按权限处理。'}[mode]
        d=Detail('RideList','ridelist-'+mode,'设施列表、列选择与批量管理','游乐设施',condition)
        x,y,w,h=d.box
        d.input('WIDX_SEARCH_TEXT_BOX','搜索设施','',(x,y,w-760,66),'text')
        d.button('WIDX_SEARCH_CLEAR_BUTTON','清除',(x+w-735,y+2,180,62))
        if mode=='lights':
            d.button('WIDX_CLOSE_LIGHT','全部关闭',(x+w-525,y+2,240,62))
            d.button('WIDX_OPEN_LIGHT','全部开放',(x+w-265,y+2,245,62),primary=True)
        else:d.button('WIDX_OPEN_CLOSE_ALL','全部开关 ▼',(x+w-525,y+2,505,62),primary=True)
        listbox=(x,y+92,w-425,h-92)
        d.table('WIDX_LIST',['设施名称（升序）','营业状态'],[['游龙飞车','开放'],['云游小火车','试车'],['竹影水道','关闭']],listbox)
        d.bind('WIDX_HEADER_NAME',(x+35,y+112,(w-425)*.38-45,44),'sort-name-header')
        d.bind('WIDX_HEADER_OTHER',(x+35+(w-425)*.38,y+112,(w-425)*.62-100,44),'sort-information-header')
        d.button('WIDX_HEADER_CUSTOMISE','显示信息 ▼',(x+w-393,y+93,370,61))
        if mode=='menu':d.menu('WIDX_OPEN_CLOSE_ALL',['全部关闭','全部开放'],(x+w-393,y+177,370,180))
        else:d.menu('WIDX_HEADER_CUSTOMISE',['营业状态','受欢迎程度','满意度','每小时利润'],(x+w-393,y+177,370,220),0)
        if mode!='client':d.button('WIDX_QUICK_DEMOLISH','快速拆除模式',(x+w-393,y+h-76,370,65))
        d.c.actions(['返回园区']);d.save()


def file_browser():
    for mode in ['save','read','drives','customise']:
        condition={'save':'保存模式显示文件名和保存按钮；选择现有文件时会进入覆盖确认。','read':'读取模式点选文件载入，不显示文件名输入或保存按钮。','drives':'当前位于 Windows 驱动器列表；上一级和新建文件夹按钮禁用。','customise':'文件列表列与预览方式可即时切换；列名始终保留。'}[mode]
        d=Detail('LoadSave','filebrowser-'+mode,'文件导航与'+('保存'if mode=='save'else'读取'), '写入'if mode=='save'else'读取',condition)
        x,y,w,h=d.box
        acts=[('WIDX_PARENT_FOLDER','上一级'),('WIDX_NEW_FOLDER','新建文件夹'),('WIDX_DEFAULT_FOLDER','默认文件夹'),('WIDX_SYSTEM_BROWSER','系统文件浏览器')]
        for i,(cid,label)in enumerate(acts):d.button(cid,label,(x+i*w/4+3,y,w/4-23,63),state='disabled'if mode=='drives'and i<2 else'normal')
        d.c.text('当前位置：此电脑'if mode=='drives'else'当前位置：存档 / 云游仙苑',(x+18,y+78,w-50,36),22,color=MUTED,minimum=21)
        bw=w-435;bh=h-205 if mode=='save'else h-130
        rows=[['C: 驱动器','—','—'],['E: 驱动器','—','—']]if mode=='drives'else[['云游仙苑_春日.park','1.8 MB','2026-10-26'],['云游仙苑_初夏.park','2.1 MB','2026-10-25'],['自动存档','文件夹','2026-10-26']]
        d.table('WIDX_SCROLL',['文件名称（升序）','大小','修改时间'],rows,(x,y+128,bw,bh))
        colw=[bw*.38,bw*.31,bw*.31];hx=x+35
        for cid,cw in zip(['WIDX_SORT_NAME','WIDX_SORT_SIZE','WIDX_SORT_DATE'],colw):d.bind(cid,(hx,y+148,cw-45,44),'sortable-column-heading');hx+=cw
        d.button('WIDX_SORT_CUSTOMISE','列与预览 ▼',(x+w-400,y+130,375,63))
        if mode=='customise':d.menu('WIDX_SORT_CUSTOMISE',['显示文件名','显示大小','显示修改时间','不显示预览','显示小地图预览','显示截图预览'],(x+w-400,y+215,375,336),5)
        elif mode=='drives':d.c.text('请选择一个驱动器\n再进入存档所在文件夹。',(x+w-380,y+245,330,150),26,minimum=23)
        else:d.c.viewport((x+w-400,y+215,375,220),'云游仙苑（暂名）')
        if mode=='save':
            d.input('WIDX_FILENAME_TEXTBOX','文件名','云游仙苑_春日',(x,y+h-66,w-390,66),'text')
            d.button('WIDX_SAVE','保存',(x+w-365,y+h-64,340,62),primary=True)
        d.c.actions(['取消']);d.save()


def staff_list():
    for mode,tab in [('normal','清洁'),('quickfire','维修'),('entertainer','演员')]:
        cond={'normal':'制服配色作用于当前员工类别；在园区点击可选择最近的员工并进入其巡逻区域。','quickfire':'快速解雇模式已开启：点击列表中的员工直接执行解雇；再点此按钮退出模式。','entertainer':'演员类别使用服装，不提供全类别制服颜色按钮；其他管理入口仍可使用。'}[mode]
        d=Detail('StaffList','stafflist-'+mode,'员工类别管理与园区工具',tab,cond)
        x,y,w,h=d.box
        rows={'清洁':[['清风','清扫步道','¥50 / 月'],['小竹','浇花','¥50 / 月'],['云团','清理垃圾箱','¥50 / 月']],
              '维修':[['小竹','修理游龙飞车','¥80 / 月'],['阿岩','检查云游小火车','¥80 / 月'],['青玉','在巡逻','¥80 / 月']],
              '演员':[['云团','巡游表演','¥55 / 月'],['圆圆','巡游表演','¥55 / 月'],['桃桃','在步道上散步','¥55 / 月']]}[tab]
        d.table('WIDX_STAFF_LIST_LIST',['员工','当前行动','薪资'],rows,(x,y,w-485,h))
        rx=x+w-450;ww=425
        d.button('WIDX_STAFF_LIST_HIRE_BUTTON','雇用'+{'清洁':'清洁工','维修':'维修员','演员':'演员'}[tab],(rx,y+5,ww,65),primary=True)
        d.button('WIDX_STAFF_LIST_QUICK_FIRE','退出快速解雇'if mode=='quickfire'else'快速解雇模式',(rx,y+91,ww,65),state='selected'if mode=='quickfire'else'normal')
        d.button('WIDX_STAFF_LIST_SHOW_PATROL_AREA_BUTTON','巡逻区域与最近员工',(rx,y+177,ww,65))
        d.button('WIDX_STAFF_LIST_MAP','在地图高亮员工',(rx,y+263,ww,65))
        if mode!='entertainer':
            d.c.text('本类别制服颜色',(rx+15,y+359,ww-30,43),25,minimum=22)
            d.color('WIDX_STAFF_LIST_UNIFORM_COLOUR_PICKER','',(rx+21,y+415,ww-42,63),'#397D60'if mode=='normal'else'#D6AA58')
        d.c.actions(['返回园区']);d.save()


def main():
    m.OUT.mkdir(parents=True,exist_ok=True)
    new_ride();guest_list();ride_list();file_browser();staff_list()
    coverage={}
    for e in m.SCREENS:
        for b in e['sourceControlBindings']:coverage.setdefault(b['sourceControlKey'],[]).append({'file':e['file'],'layoutFile':e['layoutFile'],'rectTopLeftXYWH':b['rectTopLeftXYWH'],'role':b['role'],'condition':b['condition']})
    owned=['NewRide','GuestList','RideList','LoadSave','StaffList']
    remaining=[c['unit']+':'+c['controlId']for c in m.MAP['controls']if c['unit']in owned and not c['excludedFromInteractiveCount']and c['unit']+':'+c['controlId']not in coverage]
    manifest={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(),'scope':'additional_actual_product_ui_not_style_contract_boards','referenceCommit':m.MAP['referenceCommit'],'screens':m.SCREENS,'images':m.SCREENS,'screenCount':len(m.SCREENS),'sourceControlCoverage':coverage,'explicitSourceSymbolCount':len(coverage),'explicitInteractiveSourceCount':sum(not m.CS[tuple(k.split(':',1))]['excludedFromInteractiveCount']for k in coverage),'ownedUnits':owned,'remainingOwnedInteractiveControls':remaining,'layoutIssueCount':sum(len(e['layoutIssues'])for e in m.SCREENS),'nativeArtClaim':False,'unityStatus':'not_integrated_not_runtime_validated','redesignPolicy':'Native operations with localized text and sample content. Source IDs are metadata only. System file browser is an OS handoff, not a game-drawn replacement.'}
    write_json(ROOT/'docs/utility-detail-manifest.json',manifest)
    print('DONE',len(m.SCREENS),'screens',len(coverage),'symbols','remaining',remaining,'issues',manifest['layoutIssueCount'],flush=True)


if __name__=='__main__':main()
