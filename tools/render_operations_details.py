"""Source-backed Ride/Guest/Park product art proposals; no Unity or game logic."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import render_screens as ui
from render_detail_screens import DetailCanvas, item, CONTROL_MAP, INVENTORY

ROOT=Path(__file__).resolve().parents[1]
SCREENS=[]
COVERAGE=[]

def control(c, unit, spec, box):
    old=c.unit;c.unit=unit
    c.control(spec,box)
    c.unit=old

def mark(c, unit, ids, box, kind, label, state='normal', parent=None):
    old=c.unit;c.unit=unit;c.mark(ids,box,kind,label,state,parent);c.unit=old

def frame(store, key, unit, slug, title, tab, condition):
    c=DetailCanvas(store,f'operations:{key}:{slug}',title,unit,condition)
    record=dict(INVENTORY[key]);record['title']=title
    index=record['tabs'].index(tab)
    content=c.frame(record,tab,index)
    mark(c,unit,'WIDX_CLOSE',(1776,110,68,68),'close','关闭窗口')
    # The original tabs are actually drawn by Canvas.frame, so their geometry is
    # evidence rather than a source-only mapping.
    tabs=[w for w in c.widgets if w.get('role')=='navigation-tab']
    for i,w in enumerate(tabs):
        cid=f'WIDX_TAB_{i+1}'
        if (unit,cid) in CONTROL_MAP:mark(c,unit,cid,w['region'],'navigation-tab',record['tabs'][i],'selected' if i==index else 'normal')
    return c,content

def save(c, key, group, slug, tab, condition, extra=None):
    path=ROOT/'designs/details'/group/(slug+'.png')
    metadata={'functionalRepository':'https://github.com/OpenRCT2/OpenRCT2.git',
              'commit':INVENTORY[key]['functionalReferenceCommit'],'sourceUnit':c.unit,
              'sourceFiles':INVENTORY[key]['sourceFiles'],'condition':condition,
              'sourceControls':c.coverage,'scope':'Functional product layout proposal, not a technical styleboard or runtime result.',
              'decorativeArtPolicy':'Existing painted assets and separate text; lines/graphs are data overlays.',
              **(extra or {})}
    result=c.save(path,metadata)
    entry={'id':c.identity,'screenId':c.identity,'key':key,'title':c.title,'system':INVENTORY[key]['system'],
           'tab':tab,'condition':condition,'file':result['file'],'layoutFile':result['layoutFile'],
           'sourceRecord':result['sourceRecord'],'assetPaths':result['assetPaths'],'layoutIssues':result['layoutIssues'],
           'sourceUnit':c.unit,'sourceControlKeys':sorted({k for v in c.coverage for k in v['sourceControlKeys']}),
           'productionStatus':result['productionStatus'],'acceptanceStatus':'pending_independent_visual_review'}
    SCREENS.append(entry)
    for cov in c.coverage:COVERAGE.append({**cov,'file':result['file'],'layoutFile':result['layoutFile']})
    print(c.identity,'controls',len(c.coverage),'issues',len(c.issues),flush=True)

def footer_action(c,text,unit,source='WIDX_CLOSE'):
    c.button(text,(1568,916,220,70),primary=False)
    mark(c,unit,source,(1568,916,220,70),'button',text)

def ride_overview(store, mode, expanded=False, protected=False):
    name={'closed':'已关闭','testing':'试车中','open':'营业中','simulating':'模拟中'}[mode]
    slug=('05-protected' if protected else {'closed':'01-overview-closed','testing':'02-overview-testing','open':'03-overview-open','simulating':'04-overview-simulating'}[mode])
    condition='A steel coaster supports testing; sample status '+mode
    if mode=='simulating':condition+='; simulation-capable ride and simulation UI build enabled (Ride.cpp __SIMULATE_IN_RIDE_WINDOW__)'
    if protected:condition+='; ride has indestructible flag and makeAllDestructible cheat is off'
    c,box=frame(store,'ride','Ride',slug,'设施经营','概览',condition)
    c.viewport((404,388,735,427),'游龙飞车',selection=True)
    mark(c,'Ride','WIDX_VIEWPORT',(404,388,735,427),'viewport','游龙飞车视图')
    control(c,'Ride',item('VIEW','观察位置','整体设施',kind='dropdown'),(404,292,735,92))
    c.text('当前状态：'+name,(425,825,690,40),25,color=ui.GREEN if mode=='open' else ui.DEEP)
    mark(c,'Ride','WIDX_STATUS',(425,825,690,40),'status','当前状态：'+name)
    control(c,'Ride',item('OPEN','设施运行状态',name,kind='dropdown'),(1162,292,624,92))
    # Redesign: equivalent status-light actions are placed in the expanded status
    # menu. They are aliases/alternative source skins, not simultaneous native UI.
    statuses=[('CLOSE_LIGHT','关闭','closed'),('TEST_LIGHT','试车','testing'),('OPEN_LIGHT','开放','open')]
    if mode=='simulating':statuses.append(('SIMULATE_LIGHT','模拟','simulating'))
    for i,(cid,label,value) in enumerate(statuses):
        row,col=divmod(i,2)
        control(c,'Ride',item(cid,label,kind='button',state='selected' if value==mode else 'normal'),(1162+col*315,395+row*82,303,88))
        c.coverage[-1]['representationMerge']='Equivalent source status lights drawn as expanded WIDX_OPEN menu choices; condition retained.'
    for i,(cid,label) in enumerate([('CONSTRUCTION','继续建造'),('RENAME','重新命名'),('LOCATE','定位设施'),('DEMOLISH','拆除设施')]):
        row,col=divmod(i,2)
        control(c,'Ride',item(cid,label,kind='button',state='disabled' if protected and cid=='DEMOLISH' else 'normal'),(1162+col*315,584+row*88,303,90))
    text='此设施受保护，当前不能拆除。' if protected else ('模拟模式只在支持此功能的设施中提供。' if mode=='simulating' else '修改轨道、命名与拆除均有独立后续步骤。')
    c.text(text,(1170,785,605,68),23,color=ui.RED if protected else ui.MUTED,minimum=22)
    footer_action(c,'返回园区','Ride')
    save(c,'ride','ride-ops',slug,'概览',condition,{'sourceEvidenceNotes':['Ride.cpp:1671-1740 construction/status actions','Ride.cpp:1907-1922 status dropdown and conditional simulation','Ride.cpp:2403-2409 protected demolition'],'mergedAlternativeControls':'WIDX_OPEN and status-light controls represent the same status intents. This proposed expanded menu replaces their alternative native skins.'})

def chart(c, box, values, unit):
    x,y,w,h=box;c.panel(box)
    left,top,right,bottom=x+74,y+68,x+w-35,y+h-90
    lo=min(0,min(values));hi=max(values)
    if hi==lo:hi=lo+1
    for i in range(5):
        yy=top+(bottom-top)*i/4
        c.lines([(left,yy),(right,yy)],color='#D9C9A7',width=1)
        val=hi-(hi-lo)*i/4
        c.text(f'{val:.1f}',(x+12,yy-15,54,32),19,align='right',minimum=18)
    points=[(left+(right-left)*i/(len(values)-1),bottom-(v-lo)/(hi-lo)*(bottom-top)) for i,v in enumerate(values)]
    c.lines(points,color=ui.GREEN,width=4,role='trial-data-graph')
    for i in range(5):c.text(str(i*15),(left+(right-left)*i/4-25,bottom+12,60,34),20,align='center',minimum=18)
    c.text('时间 / 秒',(right-150,bottom+51,145,30),19,align='right',minimum=18)
    c.text(unit,(left,top-31,250,30),19,color=ui.MUTED,minimum=18)

def ride_graphs(store):
    choices=[('VELOCITY','速度','千米/时',[0,10,35,64,82,58,34,47,22,8,0]),('ALTITUDE','高度','米',[2,5,16,30,42,35,27,20,15,4,2]),('VERTICAL','垂直加速度','G',[1,1.1,2.5,3.2,2.4,.5,-.2,1.5,2,1,1]),('LATERAL','水平加速度','G',[0,.1,.2,.8,.4,-.6,-.2,.3,.8,.2,0])]
    for j,(cid,label,unit,values) in enumerate(choices):
        slug=f'{6+j:02}-graph-{cid.lower()}';condition='Ride has test measurements; graph type '+cid.lower()
        c,box=frame(store,'ride','Ride',slug,'设施试车记录','图表',condition)
        for i,(other,lab,_,_) in enumerate(choices):
            control(c,'Ride',item('GRAPH_'+other,lab,kind='button',state='selected' if i==j else 'normal'),(404+i*347,292,332,88))
        graphbox=(404,399,1380,420);chart(c,graphbox,values,unit)
        mark(c,'Ride','WIDX_GRAPH',graphbox,'data-graph',label+'与时间的关系')
        c.text('游龙飞车  第1列车  本次试车数据样例',(425,832,1325,40),23,color=ui.MUTED)
        footer_action(c,'返回设施','Ride')
        save(c,'ride','ride-ops',slug,'图表',condition,{'sourceEvidenceNotes':['Ride.cpp WIDX_GRAPH_VELOCITY/ALTITUDE/VERTICAL/LATERAL and GraphsMouseUp'],'dataStatus':'Illustrative measurements, no simulation executed.'})

def ride_prices(store,locked=False):
    slug='11-admission-price-locked' if locked else '10-shop-prices'
    condition='RidePricesUnlocked is false; admission ride price locked; on-ride photo is present' if locked else 'Shop ride entry has primary and secondary sale items; same-price flags may differ by item'
    c,box=frame(store,'ride','Ride',slug,'设施收入与定价','收入',condition)
    c.text('游龙飞车' if locked else '清风茶点铺',(414,296,1320,44),31,family='title')
    specs=[item('PRIMARY_PRICE','设施票价' if locked else '荷香茶价格','免费' if locked else '6 铜钱',kind='spinner',state='disabled' if locked else 'normal'),
           item('SECONDARY_PRICE','留影价格' if locked else '桂花糕价格','8 铜钱' if locked else '5 铜钱',kind='spinner')]
    for i,spec in enumerate(specs):
        b=(414+i*700,370,665,112);control(c,'Ride',spec,b)
        mark(c,'Ride','WIDX_PRIMARY_PRICE_LABEL' if i==0 else 'WIDX_SECONDARY_PRICE_LABEL',(b[0]+8,b[1],b[2]-16,34),'price-label',spec['label'])
    if not locked:control(c,'Ride',item('PRIMARY_PRICE_SAME_THROUGHOUT_PARK','同种荷香茶在全园统一价格',kind='checkbox',checked=True),(414,505,665,104))
    control(c,'Ride',item('SECONDARY_PRICE_SAME_THROUGHOUT_PARK','同种留影在全园统一价格' if locked else '同种桂花糕在全园统一价格',kind='checkbox',checked=False),(1114,505,665,104))
    c.panel((414,644,1365,172));c.text('门票制下此设施票价不可修改，留影项目单独定价。' if locked else '勾选后，同种商品在园内各摊位使用相同价格。不同商品分别设置。',(451,674,1287,104),27,minimum=24)
    footer_action(c,'返回设施','Ride')
    save(c,'ride','ride-ops',slug,'收入',condition,{'sourceEvidenceNotes':['Ride.cpp:6851 primaryPriceLocked','Ride.cpp:6875-6906 primary/secondary item visibility and common price'],'conditionalOmissions':['PRIMARY_PRICE_SAME_THROUGHOUT_PARK hidden for regular admission ride'] if locked else []})

def ride_blueprint_pages(store):
    for disabled in (False,True):
        slug='14-blueprint-entry-locked' if disabled else '13-blueprint-entry'
        condition='Not in design save mode; canSaveTrackDesign = tested flag and non-null ratings; '+('condition not met' if disabled else 'condition met; hasTrack ride')
        c,box=frame(store,'ride','Ride',slug,'设施试车与蓝图','测试',condition)
        c.panel((414,323,1365,230))
        c.text('尚未取得完整试车记录' if disabled else '试车记录已完成',(451,354,1280,58),35,family='title',color=ui.MUTED if disabled else ui.GREEN)
        c.text('完成试车并取得评分后，才能保存轨道蓝图。' if disabled else '刺激度 6.80  强度 5.20  眩晕度 2.40\n本次为游龙飞车的试车数据样例。',(451,432,1280,101),27,color=ui.MUTED)
        control(c,'Ride',item('SAVE_TRACK_DESIGN','保存轨道蓝图',kind='button',state='disabled' if disabled else 'normal'),(1147,597,625,100))
        if not disabled:
            for y,label in [(718,'只保存轨道'),(804,'包含周围景物')]:
                c.button(label,(1162,y,605,70),primary=False)
                mark(c,'Ride','WIDX_SAVE_TRACK_DESIGN',(1162,y,605,70),'dynamic-menu-choice',label,parent='WIDX_SAVE_TRACK_DESIGN')
                c.coverage[-1]['sourceDynamicChoice']='MeasurementsOnMouseDown save dropdown entry; no separate fixed WIDX for each item.'
        else:c.text('缺少试车评分，保存入口不可用。',(1170,737,575,77),25,color=ui.RED)
        footer_action(c,'返回设施','Ride')
        save(c,'ride','ride-ops',slug,'测试',condition,{'sourceEvidenceNotes':['Ride.cpp:5807-5830 WIDX_SAVE_TRACK_DESIGN opens save-only/save-with-scenery dropdown','Ride.cpp:5920-5933 canSaveTrackDesign and visibility'],'entryVsCommit':'WIDX_SAVE_TRACK_DESIGN is the actual entry; WIDX_SAVE_DESIGN is a later confirmation and does not substitute for it.'})
    condition='gTrackDesignSaveMode and gTrackDesignSaveRideIndex match this ride; scenery selection active'
    c,box=frame(store,'ride','Ride','15-blueprint-scenery-selection','蓝图景物选择','测试',condition)
    viewport=(414,325,900,486);c.viewport(viewport,'选择随蓝图保存的景物',selection=True)
    for i,(cid,label) in enumerate([('SELECT_NEARBY_SCENERY','选择邻近景物'),('RESET_SELECTION','重新选择'),('SAVE_DESIGN','保存蓝图'),('CANCEL_DESIGN','取消保存')]):
        control(c,'Ride',item(cid,label,kind='button'),(1351,350+i*108,425,100))
    c.text('已选 18 项景物（样例）。景物、墙体与步道可随蓝图保存。',(430,830,1335,60),24,color=ui.MUTED)
    save(c,'ride','ride-ops','15-blueprint-scenery-selection','测试',condition,{'sourceEvidenceNotes':['Ride.cpp MeasurementsOnMouseUp SELECT_NEARBY_SCENERY / RESET_SELECTION / SAVE_DESIGN / CANCEL_DESIGN','Ride.cpp:5917-5926 selection controls visible only in save mode'],'conditionalOmissions':['WIDX_SAVE_TRACK_DESIGN hidden while saving; its entry is shown in13-blueprint-entry.']})

def rename_page(store,key,unit,group,slug,title,current_name,max_length):
    condition=f'Rename requested from {unit}:WIDX_RENAME; nonempty name accepted, character limit {max_length}'
    c,box=frame(store,key,unit,slug,title,'概览' if unit in ('Ride','Guest') else '入口',condition)
    c.panel((414,350,1365,370))
    c.text('输入新名称',(460,386,1260,50),31,family='title')
    c.place('secondary_normal',(460,463,1260,84),mode='nine',role='external-text-input')
    c.text(current_name,(510,483,1160,54),30)
    c.widgets.append({'role':'external-text-input-semantics','region':[460,463,1260,84],'sourceBusinessControl':unit+':WIDX_RENAME','sourceInput':'WindowTextInputRawOpen','maxCharacters':max_length,'textSeparate':True})
    c.text('名称不能为空。请确认后保存，或取消返回。',(460,580,1260,63),25,color=ui.MUTED)
    control(c,'TextInput',item('OKAY','确认名称',kind='button'),(1308,772,236,90))
    control(c,'TextInput',item('CANCEL','取消',kind='button'),(1563,772,216,90))
    save(c,key,group,slug,'命名',condition,{'sourceEvidenceNotes':[unit+'.cpp WIDX_RENAME invokes native text input; text input receives nonempty string'],'externalInputContract':'The input region is native text input rather than an invented WIDX. Confirm/cancel use TextInput source IDs.'})

def guest_pages(store):
    for disabled in (False,True):
        slug='02-pickup-unavailable' if disabled else '01-guest-actions'
        condition='Guest.canBePickedUp is false' if disabled else 'Guest.canBePickedUp is true; tracking enabled in sample'
        c,box=frame(store,'guest','Guest',slug,'游客详细资料','概览',condition)
        c.viewport((414,325,800,473),'游客所在位置',selection=True);mark(c,'Guest','WIDX_VIEWPORT',(414,325,800,473),'viewport','游客所在位置')
        c.text('青云小客  正在游园' if not disabled else '青云小客  正在乘坐设施',(1245,330,525,77),29,family='title')
        mark(c,'Guest',['WIDX_MARQUEE','WIDX_ACTION_LBL'],(1245,330,525,77),'guest-summary','游客姓名与当前行动')
        for i,(cid,label) in enumerate([('PICKUP','移动游客'),('RENAME','命名游客'),('LOCATE','定位游客'),('TRACK','已开启追踪')]):
            control(c,'Guest',item(cid,label,kind='button',state='disabled' if disabled and cid=='PICKUP' else 'selected' if cid=='TRACK' else 'normal'),(1240,425+i*87,535,90))
        c.text('游客当前状态不允许移动，请稍后重试。' if disabled else '追踪开启后，游客的行动会显示在最近消息中。',(430,825,1340,65),24,color=ui.RED if disabled else ui.MUTED)
        footer_action(c,'返回游客列表','Guest')
        save(c,'guest','guest-ops',slug,'概览',condition,{'sourceEvidenceNotes':['Guest.cpp:483-501 DisableWidgets','Guest.cpp:643-687 pickup, rename, tracking actions']})
    condition='Pickup action succeeded; picker tool active; target path is a placement preview'
    c,box=frame(store,'guest','Guest','03-pickup-placement','移动游客','概览',condition)
    c.viewport((414,325,970,485),'选择游客落脚位置',selection=True);mark(c,'Guest','WIDX_VIEWPORT',(414,325,970,485),'viewport','游客落点预览')
    c.icon(0,(1440,365,250,250),'visitor')
    c.text('青云小客',(1400,630,340,50),30,family='title',align='center')
    c.text('选择可用步道放下游客。取消后保留原位置。',(430,826,1330,65),25,color=ui.MUTED)
    control(c,'Guest',item('PICKUP','移动中',kind='button',state='selected'),(1120,904,300,90))
    c.button('取消移动',(1460,916,325,70),primary=False)
    c.widgets.append({'role':'pickup-cancel-action','region':[1460,916,325,70],'sourceFunction':'Guest.cpp onToolAbortOverview','note':'Tool cancellation has no separate fixed WIDX.'})
    save(c,'guest','guest-ops','03-pickup-placement','移动',condition,{'sourceEvidenceNotes':['Guest.cpp:643-666 PeepPickupAction success activates picker','Guest.cpp onToolUpdateOverview/onToolDownOverview/onToolAbortOverview'],'worldBoundary':'Viewport is static placement concept, no pathfinding or real placement executed.'})
    rename_page(store,'guest','Guest','guest-ops','04-rename','游客命名','青云小客',32)

def park_pages(store):
    for mode in ('normal','forced-open','no-money'):
        slug={'normal':'01-park-actions','forced-open':'02-objective-keeps-open','no-money':'03-no-money-actions'}[mode]
        condition={'normal':'Monetary park; ordinary objective; park open','forced-open':'ObjectiveType.guestsAndRating disables open/close controls','no-money':'ParkFlag.noMoney hides purchase land/construction rights'}[mode]
        c,box=frame(store,'park','Park',slug,'园区入口管理','入口',condition)
        c.viewport((414,325,800,473),'云游仙苑入口',selection=True);mark(c,'Park','WIDX_VIEWPORT',(414,325,800,473),'viewport','园区入口')
        c.text('园区开放中',(1245,330,525,50),29,family='title',color=ui.GREEN);mark(c,'Park','WIDX_STATUS',(1245,330,525,50),'status','园区开放中')
        control(c,'Park',item('OPEN_OR_CLOSE','园区营业状态','开放',kind='dropdown',state='disabled' if mode=='forced-open' else 'normal'),(1240,400,535,96))
        for j,(cid,label) in enumerate([('CLOSE_LIGHT','关闭园区'),('OPEN_LIGHT','开放园区')]):
            control(c,'Park',item(cid,label,kind='button',state='disabled' if mode=='forced-open' else 'selected' if j==1 else 'normal'),(1240+j*273,501,262,90))
            c.coverage[-1]['representationMerge']='Alternative source light skin represented as expanded OPEN_OR_CLOSE menu choice.'
        actions=[('RENAME','命名园区'),('LOCATE','定位入口')]
        if mode!='no-money':actions.append(('BUY_LAND_RIGHTS','土地与建造权'))
        for j,(cid,label) in enumerate(actions):control(c,'Park',item(cid,label,kind='button'),(1240,601+j*83,535,86))
        note='当前场景目标要求园区保持开放。' if mode=='forced-open' else '无金钱模式下不显示购买土地与建造权。' if mode=='no-money' else '土地所有权和建造权分别在购买工具中选择。'
        c.text(note,(430,825,1340,62),24,color=ui.RED if mode=='forced-open' else ui.MUTED)
        footer_action(c,'返回园区','Park')
        save(c,'park','park-ops',slug,'入口',condition,{'sourceEvidenceNotes':['Park.cpp:513-519 objective/open-close and no-money rights visibility'],'conditionalOmissions':['WIDX_BUY_LAND_RIGHTS hidden in noMoney mode'] if mode=='no-money' else []})
    for locked in (False,True):
        slug='05-ticket-free-locked' if locked else '04-ticket-price'
        condition='EntranceFeeUnlocked is false or ParkFlag.noMoney; price is label, stepper buttons hidden' if locked else 'EntranceFeeUnlocked and monetary park; editable admission price'
        c,box=frame(store,'park','Park',slug,'园区门票管理','票价',condition)
        c.icon(0,(460,370,320,300),'park_gate')
        if locked:
            c.text('门票价格',(840,366,850,44),28,family='title')
            c.place('secondary_disabled',(840,438,860,90),mode='nine',role='read-only-price')
            c.text('免费',(888,458,765,54),32,color=ui.MUTED)
            mark(c,'Park','WIDX_PRICE_LABEL',(840,366,850,44),'label','门票价格')
            mark(c,'Park','WIDX_PRICE',(840,438,860,90),'read-only-price','免费','disabled')
            c.text('当前经营规则不允许修改门票价格。',(840,590,860,100),27,color=ui.MUTED)
        else:
            control(c,'Park',item('PRICE','门票价格','30 铜钱',kind='spinner',parts={'increase':'WIDX_INCREASE_PRICE','decrease':'WIDX_DECREASE_PRICE'}),(840,380,860,120))
            mark(c,'Park','WIDX_PRICE_LABEL',(848,380,844,34),'label','门票价格')
            c.text('门票调整范围由经营规则决定。\n园区门票与设施商品价格分别设置。',(840,590,860,126),27,color=ui.MUTED)
        footer_action(c,'返回园区','Park')
        save(c,'park','park-ops',slug,'票价',condition,{'sourceEvidenceNotes':['Park.cpp:837-860 entrance price unlocked/read-only conditions'],'noInventedControl':'Park has no same-price-throughout-park checkbox; those source controls belong to Ride sale items.'})
    rename_page(store,'park','Park','park-ops','06-rename','园区命名','云游仙苑',32)
    condition='ParkFlag.scenarioCompleteNameInput is set; scenario completed and chart name can be entered'
    c,box=frame(store,'park','Park','07-completion-name-entry','园区目标记录','目标',condition)
    c.icon(0,(475,370,325,325),'trophy')
    c.text('场景目标已达成',(870,380,825,58),38,family='title',color=ui.GREEN)
    c.text('完成者：尚未登记',(870,472,825,52),29)
    c.text('登记姓名后，显示在本次场景的完成记录中。',(870,548,825,96),27,color=ui.MUTED)
    control(c,'Park',item('ENTER_NAME','登记完成者姓名',kind='button'),(870,686,825,94))
    footer_action(c,'返回园区','Park')
    save(c,'park','park-ops','07-completion-name-entry','目标',condition,{'sourceEvidenceNotes':['Park.cpp:1038-1045 shows WIDX_ENTER_NAME only with scenarioCompleteNameInput','Park.cpp:981-984 name input uses kParkNameMaxLength 128'],'scenarioResult':'Static completed-state example, no objective simulated or score submitted.'})

def main():
    store=ui.AssetStore(ROOT)
    for state in ('closed','testing','open','simulating'):ride_overview(store,state)
    ride_overview(store,'closed',protected=True)
    ride_graphs(store);ride_prices(store);ride_prices(store,True);ride_blueprint_pages(store)
    rename_page(store,'ride','Ride','ride-ops','12-rename','设施命名','游龙飞车',32)
    guest_pages(store);park_pages(store)
    result={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(),'referenceCommit':'52a55c3e8da5972460642bdfed61d091fe9cabfd',
            'artScope':'Supplemental actual product UI proposals for source-backed Ride/Guest/Park operations, not source styleboards.',
            'referenceResolution':[1920,1080],'screens':SCREENS,'coverage':COVERAGE,'layoutIssueCount':sum(len(s['layoutIssues']) for s in SCREENS),
            'status':'produced_pending_visual_review','unityValidated':False,'sourceControlPlacementBoundary':'Only the listed actually drawn rectangles are placement evidence; no all-controls claim.',
            'semanticMerges':['Alternative source status light controls map to readable expanded status menu choices.','External rename text input is native input channel, not an invented WIDX; TextInput confirmation/cancel buttons use real source controls.']}
    ui.write_json(ROOT/'docs/operations-detail-manifest.json',result)
    print('OPERATIONS',len(SCREENS),'coverage',len(COVERAGE),'issues',result['layoutIssueCount'],flush=True)

if __name__=='__main__':main()
