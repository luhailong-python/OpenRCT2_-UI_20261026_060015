"""Static widget evidence extractor. Does not run or modify the reference game.

The parser expands the repository's makeWidgets helpers and evaluates integer
enum indices. Ambiguous/dynamic controls remain explicit unknowns. It never
infers screenshot presence from a successful source parse.
"""
from pathlib import Path
import ast
import copy
import json
import operator
import re
from collections import Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'reference/OpenRCT2'


def no_comments(t):
    pat = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/'
    return re.sub(pat, lambda m: ''.join('\n' if c == '\n' else ' ' for c in m.group())
                  if m.group().startswith(('//', '/*')) else m.group(), t)


def closing(t, pos):
    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = [pairs[t[pos]]]
    quote = None
    i = pos + 1
    while i < len(t):
        c = t[i]
        if quote:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in ('"', "'"):
            quote = c
        elif c in pairs:
            stack.append(pairs[c])
        elif c == stack[-1]:
            stack.pop()
            if not stack:
                return i
        i += 1
    raise ValueError('unbalanced expression')


def split_args(t, start=0):
    result = []
    i = 0
    begin = 0
    while i < len(t):
        if t[i] in '([{':
            i = closing(t, i)
        elif t[i] in ('"', "'"):
            quote = t[i]
            i += 1
            while i < len(t):
                if t[i] == '\\':
                    i += 2
                    continue
                if t[i] == quote:
                    break
                i += 1
        elif t[i] == ',':
            result.append((t[begin:i], start + begin))
            begin = i + 1
        i += 1
    result.append((t[begin:], start + begin))
    return [(s, n) for s, n in result if s.strip()]


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.LShift: operator.lshift, ast.RShift: operator.rshift,
       ast.BitOr: operator.or_, ast.BitAnd: operator.and_}


def integer(expr, known):
    def run(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.Name) and node.id in known and known[node.id] is not None:
            return known[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](run(node.left), run(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -run(node.operand)
        raise ValueError(expr)
    try:
        return run(ast.parse(expr.strip(), mode='eval').body)
    except (ValueError, SyntaxError, KeyError, TypeError):
        return None


def enum_defs(t):
    known = {}
    out = {}
    for em in re.finditer(r'\benum(?:\s+class)?[^;{}]*\{', t):
        b = em.end() - 1
        e = closing(t, b)
        body = t[b + 1:e]
        if 'WIDX_' not in body:
            continue
        cursor = -1
        for part, pos in split_args(body, b + 1):
            part = re.sub(r'^\s*#.*$', '', part, flags=re.M).strip()
            m = re.fullmatch(r'(\w+)\s*(?:=\s*([\s\S]+))?', part)
            if not m:
                continue
            name, expr = m.groups()
            cursor = integer(expr, known) if expr else (cursor + 1 if cursor is not None else None)
            known[name] = cursor
            if name.startswith('WIDX_'):
                out[name] = {'value': cursor, 'definitionPosition': pos + max(0, t[pos:pos + len(part) + 80].find(name)),
                             'enumBlockStart': em.start(), 'expression': expr}
    return out


class Unit:
    def __init__(self, p):
        self.path = p.relative_to(REPO).as_posix()
        self.original = p.read_text(encoding='utf-8-sig')
        self.t = no_comments(self.original)
        self.t = re.sub(r'^[ \t]*#.*$', lambda m:' '*len(m.group()), self.t, flags=re.M)
        self.defs = {}
        self.helpers = {}
        self.cache = {}
        for m in re.finditer(r'\b(\w+)\s*=\s*makeWidgets\s*\(', self.t):
            b = m.end() - 1
            self.defs[m.group(1)] = (self.t[b + 1:closing(self.t, b)], b + 1)
        for m in re.finditer(r'\bWidget\s+(\w+)\s*\[\s*\]\s*=\s*\{', self.t):
            b=m.end()-1
            self.defs[m.group(1)]=(self.t[b+1:closing(self.t,b)],b+1)
        for m in re.finditer(r'\b(make\w+)\s*=\s*\[', self.t):
            rm = re.search(r'\breturn\s+makeWidgets\s*\(', self.t[m.end():])
            if rm:
                b = m.end() + rm.end() - 1
                if b - m.end() < 1200:
                    self.helpers[m.group(1)] = (self.t[b + 1:closing(self.t, b)], b + 1)
        self.enums = enum_defs(self.t)

    def line(self, pos):
        return self.t.count('\n', 0, pos) + 1

    def descriptor(self, kind, text, pos, part=None):
        return {'widgetType': kind, 'sourcePath': self.path, 'line': self.line(pos),
                'sourceExpression': text.strip()[:650],
                'sourceStringIds': list(dict.fromkeys(re.findall(r'\bSTR_[A-Z0-9_]+', text))),
                'originalSpriteIds': list(dict.fromkeys(re.findall(r'\bSPR_[A-Z0-9_]+', text))),
                'helperPart': part}

    def flatten_args(self, expr, pos, seen=()):
        result = []
        for arg, ap in split_args(expr, pos):
            stripped = arg.strip()
            ap += len(arg) - len(arg.lstrip())
            if stripped in self.defs and stripped not in seen:
                a, b = self.defs[stripped]
                result += self.flatten_args(a, b, seen + (stripped,))
                continue
            m = re.match(r'(make\w+)\s*\(', stripped)
            if not m:
                # Explicit unresolved entry preserves index uncertainty.
                result.append(self.descriptor('unknown-expression', stripped, ap))
                continue
            fn = m.group(1)
            types = re.findall(r'WidgetType::(\w+)', stripped)
            kind = types[0] if types else None
            if fn in self.helpers:
                a, b = self.helpers[fn]
                result += self.flatten_args(a, b, seen + (fn,))
            elif fn == 'makeWindowShim':
                for k in ('frame', 'caption', 'closeBox'):
                    result.append(self.descriptor(k, stripped, ap, k))
            elif fn in ('makeSpinnerWidgets', 'makeHoldableSpinnerWidgets'):
                for k, part in ((kind or 'spinner', 'value'), ('button', 'increase'), ('button', 'decrease')):
                    result.append(self.descriptor(k, stripped, ap, part))
            elif fn == 'makeDropdownWidgets':
                for k, part in ((kind or 'dropdownMenu', 'value'), ('button', 'dropdown-arrow')):
                    result.append(self.descriptor(k, stripped, ap, part))
            elif fn == 'makeTab':
                result.append(self.descriptor('tab', stripped, ap))
            elif fn == 'makeProgressBar':
                result.append(self.descriptor('progressBar', stripped, ap))
            elif fn in ('makeWidget', 'makeRemapWidget', 'makeHoldableWidget'):
                result.append(self.descriptor(kind or 'unknown-type', stripped, ap))
            else:
                result.append(self.descriptor('unknown-helper', stripped, ap, fn))
        return result

    def array(self, name):
        if name not in self.cache:
            a, b = self.defs[name]
            self.cache[name] = self.flatten_args(a, b, (name,))
        return self.cache[name]


# Exact enum reset markers tie repeated indices to the source page's widget array.
# Source array names and numeric enum values are validated on each rebuild.
PAGES = {
 'Ride': [('WIDX_VIEWPORT','_mainWidgets',0),('WIDX_VEHICLE_TYPE','_vehicleWidgets',1),('WIDX_MODE_GROUP','_operatingWidgets',2),('WIDX_RELIABILITY_BAR','_maintenanceWidgets',3),('WIDX_PRIMARY_PREVIEW_GROUP','_colourWidgets',4),('WIDX_PLAY_MUSIC','_musicWidgets',5),('WIDX_SAVE_TRACK_DESIGN','_measurementWidgets',6),('WIDX_GRAPH','_graphsWidgets',7),('WIDX_PRIMARY_PRICE_LABEL','_incomeWidgets',8),('WIDX_SHOW_GUESTS_THOUGHTS','_customerWidgets',9)],
 'Guest': [('WIDX_MARQUEE','_guestWindowWidgetsOverview',0),('WIDX_HAPPINESS_LABEL','_guestWindowWidgetsStats',1),('WIDX_RIDES_BEEN_ON_LABEL','_guestWindowWidgetsRides',2),('WIDX_RECENT_THOUGHTS_LABEL','_guestWindowWidgetsThoughts',4),('WIDX_CARRYING_LABEL','_guestWindowWidgetsInventory',5)],
 'Staff': [('WIDX_VIEWPORT','_staffOverviewWidgets',0),('WIDX_CHECKBOX_1','_staffOptionsWidgets',1)],
 'Options': [('WIDX_WINDOW_GROUP','window_options_display_widgets',0),('WIDX_MAP_RENDERING_GROUP','window_options_rendering_widgets',1),('WIDX_LANGUAGE_LABEL','window_options_culture_widgets',2),('WIDX_SOUND','window_options_audio_widgets',3),('WIDX_THEMES_GROUP','window_options_interface_widgets',4),('WIDX_CONTROLS_GROUP','window_options_controls_widgets',5),('WIDX_TITLE_SEQUENCE_GROUP','window_options_misc_widgets',6),('WIDX_GROUP_RCT1_PATH','window_options_advanced_widgets',7)],
 'Finances': [('WIDX_SUMMARY_SCROLL','_windowFinancesSummaryWidgets',0),('WIDX_ACTIVE_CAMPAIGNS_GROUP','_windowFinancesMarketingWidgets',4),('WIDX_RESEARCH_FUNDING_GROUP','_windowFinancesResearchWidgets',5)],
 'Park': [('WIDX_VIEWPORT','_entranceWidgets',0),('WIDX_PRICE_LABEL','_priceWidgets',3),('WIDX_ENTER_NAME','_objectiveWidgets',5)],
 'Cheats': [('WIDX_NO_MONEY','window_cheats_money_widgets',0),('WIDX_DATE_GROUP','window_cheats_date_widgets',1),('WIDX_TRAM_GUESTS','window_cheats_guests_widgets',2),('WIDX_STAFF_GROUP','window_cheats_staff_widgets',3),('WIDX_GENERAL_GROUP','window_cheats_park_widgets',4),('WIDX_FIX_ALL','window_cheats_rides_widgets',5),('WIDX_WEATHER_GROUP','window_cheats_weather_widgets',6)],
 'EditorScenarioOptions': [('WIDX_OBJECTIVE_LABEL','window_editor_scenario_options_objective_widgets',0),('WIDX_PARK_NAME','window_editor_scenario_options_scenario_details_widgets',1),('WIDX_NO_MONEY','window_editor_scenario_options_financial_widgets',2),('WIDX_CASH_PER_GUEST_LABEL','window_editor_scenario_options_guests_widgets',3),('WIDX_LAND_COST_LABEL','window_editor_scenario_options_land_widgets',4)],
 'Multiplayer': [('WIDX_HEADER_PLAYER','window_multiplayer_players_widgets',1),('WIDX_DEFAULT_GROUP','window_multiplayer_groups_widgets',2),('WIDX_LOG_CHAT_CHECKBOX','window_multiplayer_options_widgets',3)],
 'MapGen': [('WIDX_MAP_SIZE_Y','kBaseWidgets',0),('WIDX_HEIGHTMAP_LOW','kTerrainWidgets',1),('WIDX_WATER_LEVEL','kWaterWidgets',2),('WIDX_FORESTS_PLACE_TREES','kForestsWidgets',3)],
 'Player': [('WIDX_GROUP','window_player_overview_widgets',0)],
 'TileInspector': [('WIDX_SURFACE_SPINNER_HEIGHT','kSurfaceWidgets',0),('WIDX_PATH_SPINNER_HEIGHT','kPathWidgets',1),('WIDX_TRACK_CHECK_APPLY_TO_ALL','kTrackWidgets',2),('WIDX_SCENERY_SPINNER_HEIGHT','kSceneryWidgets',3),('WIDX_ENTRANCE_SPINNER_HEIGHT','kEntranceWidgets',6),('WIDX_WALL_SPINNER_HEIGHT','kWallWidgets',5),('WIDX_LARGE_SCENERY_SPINNER_HEIGHT','kLargeSceneryWidgets',4),('WIDX_BANNER_SPINNER_HEIGHT','kBannerWidgets',7)],
 'TrackDesignManage': [('WIDX_RENAME','_trackManageWidgets',0),('WIDX_PROMPT_DELETE','_trackDeletePromptWidgets',1)],
 'About': [('WIDX_INTRO','_windowAboutOpenRCT2Widgets',0)],
 'Research': [('WIDX_CURRENTLY_IN_DEVELOPMENT_GROUP','window_research_development_widgets',0),('WIDX_RESEARCH_FUNDING_GROUP','window_research_funding_widgets',1)],
 'News': [('WIDX_SCROLL','kNewsTabWidgets',0),('WIDX_CHECKBOX_0','kOptionsTabWidgets',1)],
 'ShortcutKeys': [('WIDX_REMOVE','window_shortcut_change_widgets',0),('WIDX_RESET_PROMPT_BACKGROUND','WindowResetShortcutKeysPromptWidgets',0)],
}


def localization():
    known = {}
    for source in ['src/openrct2/localisation/StringIds.h','src/openrct2-ui/UiStringIds.h']:
        t = no_comments((REPO/source).read_text(encoding='utf-8-sig'))
        for m in re.finditer(r'\b(STR_[A-Z0-9_]+)\s*=\s*([^,\n]+)', t):
            known[m.group(1)] = integer(m.group(2), known)
    langs = {}
    for ln in (REPO/'data/language/zh-CN.txt').read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'STR_(\d+)\s*:(.*)', ln)
        if m:
            langs[int(m.group(1))] = m.group(2).strip()
    return {k: {'numericId': n, 'zhCN': langs.get(n)} for k,n in known.items()}


def formal_art(typ, cid, part):
    c = 'assets/common/'
    buttons = [c+'secondary_'+s+'.png' for s in ['normal','pressed','selected','disabled']]
    if typ in ('frame','resize','groupbox','tableHeader','scroll','textBox','dropdownMenu','spinner','viewport'):
        files=[c+'panel_card.png']
        mode={'textBox':'dynamic-text-input','dropdownMenu':'dynamic-selection-text-and-glyph',
              'spinner':'dynamic-number-input','viewport':'runtime-viewport-content',
              'scroll':'dynamic-scroll-list-or-graph-content','tableHeader':'dynamic-table-heading'}.get(typ,'stretch-panel')
    elif typ in ('label','labelCentred','caption','empty','horizontalSeparator','hiddenButton','placeholder','enum-index-marker'):
        files=[];mode='dynamic-text-or-layout'
    elif typ=='closeBox': files=[c+'close.png'];mode='close-button'
    elif typ=='tab':files=[c+'tab_'+s+'.png' for s in ['normal','pressed','selected','disabled']];mode='tab-with-separate-text'
    elif typ=='checkbox':files=[c+'checkbox_off.png',c+'checkbox_on.png'];mode='checkbox-with-separate-label'
    elif typ=='progressBar':files=[c+'progress_track.png',c+'progress_fill.png'];mode='dynamic-progress-fill'
    elif typ in ('slider','hSlider','vSlider'):files=[c+'slider_track.png',c+'slider_thumb.png'];mode='dynamic-slider'
    elif typ=='external-text-input':files=[c+'panel_card.png']+buttons;mode='shared-text-input-dialog-and-dynamic-password-field'
    elif typ in ('colourBtn','trnBtn'):files=buttons;mode='shared-labelled-button-with-runtime-color-or-icon'
    elif typ in ('button','flatBtn','imgBtn','tabButton','context-menu-action'):
        if re.search(r'(?:^|_)MOVE_(?:UP|DOWN)$',cid):files=buttons;mode='shared-button-with-independent-direction-glyph'
        elif part=='increase' or re.search(r'(INCREASE|INCREMENT|_UP$)',cid):files=[c+'plus.png'];mode='numeric-increase'
        elif part=='decrease' or re.search(r'(DECREASE|DECREMENT|_DOWN$)',cid):files=[c+'minus.png'];mode='numeric-decrease'
        else:files=buttons;mode='shared-button-with-independent-text-label-or-icon'
    else:files=[];mode='unresolved-source-widget'
    return {'formalSpritePaths':files,'spriteFilesExist':all((ROOT/f).is_file()for f in files),
            'renderMode':mode,'dynamicTextSeparate':True,
            'originalCommercialSpriteCopied':False,
            'runtimeContentNote':'List, graph, map, viewport, object thumbnails and text values are dynamic; static art does not supply world simulation or the original object library.'}


def main():
    inventory=json.loads((ROOT/'docs/repo-ui-inventory.json').read_text(encoding='utf-8'))
    loc=localization()
    records=[]
    unit_stats=[]
    unknowns=[]
    source_units={p.stem for p in (REPO/'src/openrct2-ui/windows').glob('*.cpp')}
    for r in inventory:
        if not r['controlIds']:
            continue
        u=Unit(REPO/r['sourceFiles'][0]);name=r['windowUnit']
        declared=list(u.enums)
        array_names=list(u.defs)
        overrides={a:(b,c)for a,b,c in PAGES.get(name,[])if a in u.enums and b in u.defs}
        common_array=next((n for n in array_names if re.search(r'(?:Main|Common|^kMain).*Widgets',n)),array_names[0]if array_names else None)
        single_array=array_names[0]if len(array_names)==1 else None
        current=None
        assignments={}
        for cid in declared:
            if cid in overrides:current=overrides[cid]
            assignments[cid]=current
        start=len(records)
        for cid in r['controlIds']:
            ed=u.enums.get(cid)
            chosen=[]
            why=''
            pages=list(r['tabs'])
            array=None
            idx=ed['value'] if ed else None
            if assignments.get(cid):
                array,pi=assignments[cid];pages=[r['tabs'][pi]]if pi<len(r['tabs'])else[]
            elif single_array:array=single_array
            elif common_array:array=common_array
            if name=='ServerList' and cid in ('WIDX_LIST_REMOVE','WIDX_LIST_SPECTATE'):
                chosen=[u.descriptor('context-menu-action',cid,ed['definitionPosition'] if ed else u.t.find(cid))]
                why='Source uses a separate context-menu action enum, not a widget-array slot'
            elif array and idx is not None:
                arr=u.array(array)
                if 0<=idx<len(arr):
                    chosen=[arr[idx]];why='Integer enum index into expanded source makeWidgets array'
            if not chosen:
                # Exact trailing WIDX annotations are strong evidence where helper arrays are dynamic.
                for m in re.finditer(r'\b'+re.escape(cid)+r'\b',u.original):
                    line=u.line(m.start());txt=u.original.splitlines()[line-1]
                    if '//' in txt and txt.find('//')<txt.find(cid):
                        prev='\n'.join(u.original.splitlines()[max(0,line-3):line])
                        ty=re.findall(r'WidgetType::(\w+)',prev)
                        if ty:
                            chosen=[u.descriptor(ty[-1],prev,m.start())];why='Exact WIDX trailing source annotation';break
            if not chosen and cid in ('WIDX_PAGE_START','WIDX_TAB_CONTENT','WIDX_TAB_CONTENT_START','WIDX_FIRST_TAB'):
                chosen=[u.descriptor('enum-index-marker',cid,ed['definitionPosition'] if ed else u.t.find(cid))]
                why='Enum offset alias only; no additional source widget or art required'
            if not chosen and name=='NetworkStatus' and cid=='WIDX_PASSWORD':
                at=u.t.find('WindowTextInputRawOpen')
                chosen=[u.descriptor('external-text-input',u.original[at:u.original.find(';',at)+1],at)]
                why='WindowTextInputRawOpen at NetworkStatus.cpp:175 opens shared password text input; WIDX_PASSWORD is callback index'
            if not chosen and name in ('Scenery','ShortcutKeys') and cid in ('WIDX_SCENERY_TAB_1','WIDX_TAB_0'):
                m=re.search(r'\bmakeTab\s*\(',u.t)
                if m:
                    e=closing(u.t,m.end()-1)
                    chosen=[u.descriptor('tab',u.original[m.start():e+1],m.start())]
                    why='Runtime-appended tab family starts at this enum offset; source makeTab plus widgets.push_back'
            typ=chosen[0]['widgetType']if chosen else None
            marker=bool(re.search(r'(?:^|_)(?:PAGE_START|TAB_CONTENT_START|TAB_CONTENT|FIRST_TAB)$',cid))
            structural=marker or typ in ('frame','caption','closeBox','resize','tab','label','labelCentred','groupbox','horizontalSeparator','enum-index-marker')
            if re.search(r'(BACKGROUND|TITLE(?:BAR)?$|CLOSE$|(?:^|_)TAB(?:_|\d|$)|(?:^|_)LABEL(?:_|$)|(?:^|_)LBL(?:_|$)|(?:^|_)GROUP(?:BOX)?(?:_|$)|CONTENT_PANEL|RESIZE$)',cid):structural=True
            vis=[]
            lines=u.original.splitlines()
            for i,line in enumerate(lines,1):
                if cid in line and re.search(r'(setHidden|setVisible|setDisabled|setEnabled|setWidgetDisabled|setWidgetVisible|setWidgetEnabled|widgetSetVisible|widgetSetDisabled|widgetSetEnabled)',line):
                    vis.append({'path':u.path,'line':i,'expression':' '.join(lines[max(0,i-2):min(len(lines),i+2)])[:650]})
            ids=list(dict.fromkeys(s for d in chosen for s in d['sourceStringIds']))
            art=formal_art(typ,cid,chosen[0].get('helperPart')if chosen else None)
            presence='specified_only'if typ and not typ.startswith('unknown')else'unknown'
            rec={'unit':name,'unitKey':r['key'],'controlId':cid,'enumValue':idx,'enumMarkerOnly':marker,
                 'excludedFromInteractiveCount':structural,'sourceWidgetType':typ,'sourceWidgetArray':array,
                 'resolutionBasis':why or 'Unresolved enum/helper/page or runtime-defined widget; no guessed type',
                 'sourceEvidence':{'definition':{'path':u.path,'line':u.line(ed['definitionPosition'])}if ed else None,'widgetCandidates':chosen},
                 'sourceLabels':[{'symbol':sid,**loc.get(sid,{'numericId':None,'zhCN':None})}for sid in ids],
                 'existingPageGroups':pages,'pageVisibilityNote':'Array/page assignment is statically known where recorded; runtime type, mode, permissions and options can hide/disable controls. See visibility conditions.',
                 'sourceVisibilityConditions':vis,'artMapping':art,'presence':presence,
                 'displayEvidence':[],'presenceNote':'No screenshot claim. specified_only means source/type/art mapping exists; displayed requires actual generated layout rect and PNG verification.'}
            records.append(rec)
            if presence=='unknown':unknowns.append({'unit':name,'controlId':cid,'sourcePath':u.path,'reason':rec['resolutionBasis']})
        us=records[start:]
        unit_stats.append({'unit':name,'allControlIds':len(us),'interactiveCandidates':sum(not q['excludedFromInteractiveCount']for q in us),'resolved':sum(q['presence']=='specified_only'for q in us),'unknown':sum(q['presence']=='unknown'for q in us),'sourceArrays':array_names})
    types=Counter(r['sourceWidgetType']or'unknown'for r in records)
    output={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(),'referenceCommit':'52a55c3e8da5972460642bdfed61d091fe9cabfd',
      'scope':'Every unit-scoped WIDX ID in the fixed source inventory; source parsing and art-resource contract, not automatic screenshot coverage',
      'parser':'docs/control_mapping_builder.py','sourceWindowUnits':sorted(source_units),'sourceWindowUnitCount':len(source_units),
      'mappedInventoryWindowUnits':sorted(r['windowUnit']for r in inventory if r['windowUnit']in source_units),
      'otherUiUnits':['src/openrct2-ui/interface/Chat.cpp','src/openrct2-ui/interface/InGameConsole.cpp','src/openrct2-ui/scripting/CustomWindow.cpp'],
      'dynamicUiNote':'Chat/console/custom plugin UI do not define fixed WIDX IDs here. Public skin covers shared controls; arbitrary future third-party plugin content cannot be enumerated.',
      'counts':{'scopedControlIds':len(records),'distinctSymbolSpellings':len(set(r['controlId']for r in records)),
                'interactiveCandidatesExcludingSourceResolvedStructureAndLexicalMarkers':sum(not r['excludedFromInteractiveCount']for r in records),
                'resolvedInteractiveCandidates':sum(not r['excludedFromInteractiveCount']and r['presence']=='specified_only'for r in records),
                'unknownInteractiveCandidates':sum(not r['excludedFromInteractiveCount']and r['presence']=='unknown'for r in records),
                'presence':dict(Counter(r['presence']for r in records)),'bySourceWidgetType':dict(types)},
      'units':unit_stats,'controls':records,'blockingUnknowns':unknowns,
      'acceptanceRule':'A resolved source widget and existing shared sprite are not proof that the control appears on a produced screen. Display evidence must name the actual PNG and rectangle. Unknown controls/page mappings remain blockers for strict full-control acceptance.'}
    # Preserve only independently verifiable style-board evidence on rebuild.
    # A style board never upgrades product screen placement to verified.
    ep=ROOT/'docs/control-display-evidence.json'
    if ep.exists():
        import hashlib
        ev=json.loads(ep.read_text(encoding='utf-8'))
        lookup={(c['unit'],c['controlId']):c for c in records}
        reused=0
        for board in ev.get('sourceBoards',[]):
            bp=ROOT/board['file']
            if not bp.is_file() or hashlib.sha256(bp.read_bytes()).hexdigest()!=board['sha256']:
                continue
            for old in board['controls']:
                c=lookup.get((old['unit'],old['controlId']))
                if c and c['sourceWidgetType']==old['sourceWidgetType']:
                    c['presence']='displayed_style_contract_only'
                    c['productScreenshotPlacement']='pending_unverified'
                    c['displayEvidence']=[{'file':board['file'],'sha256':board['sha256'],'layoutRecord':board['layoutRecord'],'rectTopLeftXYWH':old['rectTopLeftXYWH'],'kind':'technical_style_contract_not_product_screen'}]
                    c['presenceNote']='Verified existing style-contract PNG and bound rectangle. Product screen placement and Unity behavior remain unverified.'
                    reused+=1
        output['styleContractEvidence']='docs/control-display-evidence.json'
        output['productScreenshotPlacement']='pending_unverified'
        output['counts']['presence']=dict(Counter(c['presence']for c in records))
        output['counts']['reusedVerifiedStyleBindings']=reused
    (ROOT/'docs/control-resource-mapping.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(output['counts'],ensure_ascii=False,indent=2))
    print('Unmapped source units',sorted(source_units-set(output['mappedInventoryWindowUnits'])))
    for s in unit_stats:
        if s['unknown']:print('UNKNOWN',s['unit'],s['unknown'])


if __name__=='__main__':main()
