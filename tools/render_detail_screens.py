"""Render source-backed product detail screens that complete essential UI controls.

The original game controls are re-arranged into readable, painted product pages.
This module only composes the approved PNG kit and dynamic text; it does not run
game logic, draw replacement artwork, or modify render_screens.py.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path

import render_screens as ui

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / 'docs/control-resource-mapping.json').read_text(encoding='utf-8'))
CONTROL_MAP = {(c['unit'], c['controlId']): c for c in SOURCE['controls']}
INVENTORY = {r['key']: r for r in json.loads((ROOT / 'docs/repo-ui-inventory.json').read_text(encoding='utf-8'))}
SCREENS, COVERAGE = [], []


def clean_label(value):
    value = re.sub(r'\{[^}]*\}', '', value)
    return value.replace('……', '').replace('...', '').strip(' ：:▼▲')


def item(control, label=None, value=None, kind=None, state='normal', checked=False, parts=None, note=None):
    control = 'WIDX_' + control.removeprefix('WIDX_')
    return dict(control=control, label=label, value=value, kind=kind, state=state,
                checked=checked, parts=parts, note=note)


def source_item(unit, spec):
    key = (unit, spec['control'])
    if key not in CONTROL_MAP:
        raise KeyError('No source control: ' + str(key))
    return CONTROL_MAP[key]


def infer_kind(source):
    kind = source.get('sourceWidgetType')
    return {'checkbox': 'checkbox', 'spinner': 'spinner', 'dropdownMenu': 'dropdown',
            'scroll': 'slider', 'colourBtn': 'color', 'viewport': 'viewport'}.get(kind, 'button')


def label_for(unit, spec):
    if spec.get('label'):
        return spec['label']
    source = source_item(unit, spec)
    labels = [clean_label(x['zhCN']) for x in source.get('sourceLabels', []) if x.get('zhCN')]
    labels = [label for label in labels if label and label not in ('最大', '最小')]
    if not labels:
        raise ValueError('A product-facing label is required: ' + unit + ':' + spec['control'])
    return labels[0]


def suffix_parts(unit, control):
    results = {}
    for role, suffixes in [('increase', ['_UP', '_INCREASE']), ('decrease', ['_DOWN', '_DECREASE']),
                           ('dropdown', ['_DROPDOWN', '_DROPDOWN_BUTTON', '_BUTTON', '_BTN'])]:
        for suffix in suffixes:
            if (unit, control + suffix) in CONTROL_MAP:
                results[role] = control + suffix
                break
    return results


class DetailCanvas(ui.Canvas):
    def __init__(self, store, identity, title, unit, condition):
        super().__init__(store, identity, title)
        self.unit = unit
        self.condition = condition
        self.coverage = []

    def mark(self, controls, rect, kind, label, state='normal', parent=None):
        if isinstance(controls, str):
            controls = [controls]
        for control in controls:
            source = CONTROL_MAP.get((self.unit, control))
            if source is None:
                raise KeyError(f'Source control is missing: {self.unit}:{control}')
            entry = {'sourceControlKeys': [self.unit + ':' + control], 'unit': self.unit,
                     'controlId': control, 'screenId': self.identity,
                     'region': [int(v) for v in rect], 'visualKind': kind,
                     'label': label, 'state': state, 'parentControl': parent,
                     'sourceWidgetType': source.get('sourceWidgetType'),
                     'sourceEvidence': source.get('sourceEvidence'),
                     'sourceVisibilityConditions': source.get('sourceVisibilityConditions', []),
                     'displayedCondition': self.condition,
                     'claim': 'drawn_product_layout_not_executed_game_logic'}
            self.coverage.append(entry)
            self.widgets.append({'role': 'source-control-geometry', **entry})

    def control(self, spec, box):
        x, y, width, height = box
        source = source_item(self.unit, spec)
        label = label_for(self.unit, spec)
        kind = spec.get('kind') or infer_kind(source)
        state = spec.get('state', 'normal')
        disabled = state == 'disabled'
        color = ui.MUTED if disabled else ui.DEEP
        value = str(spec.get('value') if spec.get('value') is not None else '')
        control = spec['control']
        parts = spec.get('parts') or suffix_parts(self.unit, control)
        if kind == 'checkbox':
            icon_box = (x + 8, y + 18, 42, 42)
            self.place('checkbox_on' if spec.get('checked') else 'checkbox_off', icon_box, role='checkbox')
            self.text(label, (x + 66, y + 14, width - 88, 62), 24, color=color, valign='center', minimum=22)
            if disabled:
                self.text('不可用', (x + width - 105, y + 63, 92, 29), 18, color=ui.MUTED, minimum=18, align='right')
            self.mark(control, box, kind, label, state)
        elif kind == 'button':
            self.button(label, (x + 4, y + 12, width - 8, 68),
                        state='disabled' if disabled else 'selected' if state == 'selected' else 'normal',
                        primary=state == 'selected')
            self.mark(control, (x + 4, y + 12, width - 8, 68), kind, label, state)
        elif kind == 'viewport':
            self.viewport(box, label)
            self.mark(control, box, kind, label, state)
        else:
            self.text(label, (x + 8, y, width - 16, 34), 23, color=color, minimum=22)
            cy = y + 36
            cb = (x + 4, cy, width - 8, 52)
            if kind == 'slider':
                self.place('slider_track', (x + 20, cy + 18, width - 150, 18), mode='nine', role='slider-track')
                numbers = re.findall(r'\d+(?:\.\d+)?', value)
                amount = min(1, max(0, float(numbers[0]) / 100)) if numbers else .5
                self.place('slider_thumb', (x + 20 + round((width - 184) * amount), cy + 1, 34, 50), role='slider-thumb')
                self.text(value or '50%', (x + width - 115, cy + 6, 105, 40), 23, color=color, align='right')
                self.mark(control, cb, kind, label, state)
            else:
                self.place('secondary_disabled' if disabled else 'secondary_normal', cb, mode='nine', role='value-field')
                if kind == 'spinner':
                    self.place('minus', (x + 13, cy + 6, 40, 40), role='spinner-decrease')
                    self.place('plus', (x + width - 53, cy + 6, 40, 40), role='spinner-increase')
                    self.text(value or '1', (x + 68, cy + 8, width - 136, 36), 24, color=color, align='center')
                    self.mark(control, (x + 60, cy, width - 120, 52), kind, label, state)
                    if parts.get('decrease'):
                        self.mark(parts['decrease'], (x + 13, cy + 6, 40, 40), 'stepper-decrease', label + '减少', state, control)
                    if parts.get('increase'):
                        self.mark(parts['increase'], (x + width - 53, cy + 6, 40, 40), 'stepper-increase', label + '增加', state, control)
                elif kind == 'dropdown':
                    self.text(value or '请选择', (x + 40, cy + 8, width - 120, 36), 23, color=color)
                    self.text('▼', (x + width - 67, cy + 8, 40, 36), 23, color=color, align='center')
                    self.mark(control, (x + 4, cy, width - 82, 52), kind, label, state)
                    if parts.get('dropdown'):
                        self.mark(parts['dropdown'], (x + width - 74, cy, 66, 52), 'dropdown-button', label + '选择', state, control)
                elif kind == 'color':
                    self.icon(0, (x + 14, cy + 8, 36, 36), 'eyedropper')
                    self.text(value or '#367D61', (x + 65, cy + 8, width - 104, 36), 23, color=color)
                    self.mark(control, cb, kind, label, state)
                else:
                    self.text(value, (x + 40, cy + 8, width - 80, 36), 23, color=color)
                    self.mark(control, cb, kind, label, state)
        return self.coverage


def render_page(store, key, unit, mode, title, specs, condition, note='', actions=None,
                columns=2, hero=None):
    record = INVENTORY[key]
    identity = f'detail:{key}:{mode}'
    c = DetailCanvas(store, identity, title, unit, condition)
    display = dict(record)
    # The plaque is an aspect-preserved illustration with a narrower live text
    # face than its transparent canvas. Keep the system name on the plaque and
    # show the detailed mode in the paper content heading below it.
    display['title'] = title.split('  ')[0]
    display['tabs'] = [mode_title for mode_title in PAGE_TABS.get(key, [title])]
    active = PAGE_MODE_TAB.get((key, mode), display['tabs'][0])
    ti = display['tabs'].index(active) if active in display['tabs'] else 0
    x, y, width, height = c.frame(display, display['tabs'][ti], ti)
    if hero:
        art_type, art = hero
        art_w = 320
        if unit == 'Staff' and mode in ('01-overview', '02-working'):
            c.illustration(0, (x + width - art_w, y + 5, art_w, 260), art)
            view_box = (x + width - art_w, y + 300, art_w, 210)
            c.viewport(view_box, '工作位置')
            c.mark('WIDX_VIEWPORT', view_box, 'viewport', '员工所在位置')
        elif art_type == 'illustration':
            c.illustration(0, (x + width - art_w, y + 60, art_w, height - 100), art)
        else:
            c.icon(0, (x + width - art_w + 40, y + 90, art_w - 80, 260), art)
        width -= art_w + 30
        columns = 1
    gap = 28
    cw = int((width - gap * (columns - 1)) / columns)
    row_height = 96
    max_rows = math.ceil(len(specs) / columns)
    if max_rows * row_height > height:
        row_height = int(height / max_rows)
    if row_height < 90:
        raise ValueError(f'Too many controls for readable detail page: {identity} / {len(specs)}')
    for i, spec in enumerate(specs):
        column, row = i % columns, i // columns
        c.control(spec, (x + column * (cw + gap), y + row * row_height, cw, row_height))
    if note:
        c.text(note, (x + 7, 870, width - 14, 39), 22, color=ui.MUTED)
    if actions:
        right = 1790
        for spec in reversed(actions):
            label = label_for(unit, spec)
            bw = min(380, max(210, len(label) * 27 + 70))
            c.control(spec, (right - bw, 904, bw, 90))
            right -= bw + 18
    path = ROOT / 'designs/details' / key / (mode + '.png')
    meta = {'functionalRepository': 'https://github.com/OpenRCT2/OpenRCT2.git',
            'commit': record['functionalReferenceCommit'], 'sourceUnit': unit,
            'sourceFiles': record['sourceFiles'], 'condition': condition,
            'scope': 'Complete controls arranged as an actual product UI proposal; no runtime verification.',
            'sourceControls': c.coverage, 'decorativeArtPolicy': 'Existing painted PNGs only'}
    result = c.save(path, meta)
    SCREENS.append({'id': identity, 'key': key, 'system': record['system'], 'title': title,
                    'tab': active, 'condition': condition, 'sourceUnit': unit,
                    'file': result['file'], 'layoutFile': result['layoutFile'],
                    'sourceRecord': result['sourceRecord'], 'assetPaths': result['assetPaths'],
                    'productionStatus': result['productionStatus'], 'acceptanceStatus': result['acceptanceStatus'],
                    'layoutIssues': result['layoutIssues'], 'sourceControlKeys': sorted({v for e in c.coverage for v in e['sourceControlKeys']})})
    for entry in c.coverage:
        entry['file'] = result['file']
        entry['layoutFile'] = result['layoutFile']
        COVERAGE.append(entry)
    print(identity, 'controls', len(c.coverage), 'issues', len(c.issues), flush=True)


PAGE_TABS = {
    'ride-construction': ['曲线方向', '坡度与侧倾', '制动与推进', '座椅旋转', '入口与出口'],
    'footpath': ['地面铺设', '桥梁与隧道', '区域拖建'],
    'staff': ['员工概览', '清洁职责', '维修职责', '表演服装', '作业状态'],
    'options': ['显示', '渲染', '文化', '声音', '界面', '操作', '杂项', '高级'],
    'map-gen': ['平地', '噪声', '高度图', '地形', '水域', '森林'],
    'tile-inspector': ['元素操作', '地表', '步道', '轨道', '小景物', '大景物', '墙', '入口', '横幅'],
}
PAGE_MODE_TAB = {}


def assign(key, mode, tab):
    PAGE_MODE_TAB[key, mode] = tab


def ride_pages(store):
    key, unit = 'ride-construction', 'RideConstruction'
    assign(key, '01-curves', '曲线方向')
    curve_ids = ['LEFT_CURVE_VERY_SMALL', 'LEFT_CURVE_SMALL', 'LEFT_CURVE', 'LEFT_CURVE_LARGE', 'STRAIGHT',
                 'RIGHT_CURVE_LARGE', 'RIGHT_CURVE', 'RIGHT_CURVE_SMALL', 'RIGHT_CURVE_VERY_SMALL']
    labels = ['左转 · 很小半径', '左转 · 小半径', '左转', '左转 · 大半径', '直行',
              '右转 · 大半径', '右转', '右转 · 小半径', '右转 · 很小半径']
    specs = [item(i, l, kind='button', state='selected' if i == 'STRAIGHT' else 'normal') for i, l in zip(curve_ids, labels)]
    specs += [item('SPECIAL_TRACK_DROPDOWN', '特殊轨道', value='选择轨道部件', kind='dropdown')]
    render_page(store, key, unit, '01-curves', '轨道建造  曲线方向', specs,
                '轨道类型支持所示曲率；实际可用半径由设施与当前轨道决定。',
                note='选中方向后建造当前轨道段。',
                actions=[item('PREVIOUS_SECTION', '上一段'), item('NEXT_SECTION', '下一段'), item('DEMOLISH', '移除高亮段')])
    assign(key, '02-slopes-banking', '坡度与侧倾')
    specs = [item(i, l, kind='button', state='selected' if i == 'LEVEL' else 'normal') for i, l in [
        ('SLOPE_DOWN_VERTICAL', '垂直下坡'), ('SLOPE_DOWN_STEEP', '陡峭下坡'), ('SLOPE_DOWN', '下坡'),
        ('LEVEL', '水平'), ('SLOPE_UP', '上坡'), ('SLOPE_UP_STEEP', '陡峭上坡'), ('SLOPE_UP_VERTICAL', '垂直上坡')]]
    specs += [item('CHAIN_LIFT', '使用牵引链', kind='checkbox', checked=True),
              item('BANK_LEFT', '向左侧倾', kind='button'), item('BANK_STRAIGHT', '保持水平侧倾', kind='button', state='selected'),
              item('BANK_RIGHT', '向右侧倾', kind='button')]
    render_page(store, key, unit, '02-slopes-banking', '轨道建造  坡度与侧倾', specs,
                '非速度设置轨道段，设施支持 flatRollBanking；坡度与链条选项随轨道支持情况启用。',
                note='当前选段支持所示坡度和侧倾。', actions=[item('CONSTRUCT', '建造此段'), item('SIMULATE', '模拟运行')])
    for mode, title, value in [('03-brake', '制动段', '24 千米 / 时'), ('04-booster', '推进段', '64 千米 / 时')]:
        assign(key, mode, '制动与推进')
        render_page(store, key, unit, mode, '轨道建造  ' + title,
                    [item('SPECIAL_TRACK_DROPDOWN', '特殊轨道', title, 'dropdown'),
                     item('SPEED_SETTING_SPINNER', '制动速度上限' if mode == '03-brake' else '推进目标速度', value, 'spinner')],
                    'trackTypeHasSpeedSetting 为真；推进与制动文案按 trackTypeIsBooster 切换，侧倾组隐藏。',
                    note='速度设置随当前选中的特殊轨道段变化。',
                    actions=[item('CONSTRUCT', '建造此段'), item('DEMOLISH', '移除高亮段')], hero=('illustration', 'dragon_coaster'))
    assign(key, '05-seat-angle', '座椅旋转')
    render_page(store, key, unit, '05-seat-angle', '轨道建造  座椅旋转',
                [item('SEAT_ROTATION_ANGLE_SPINNER', '座椅旋转角度', '90°', 'spinner'),
                 item('BANK_LEFT', '向左侧倾', kind='button'), item('BANK_STRAIGHT', '不侧倾', kind='button', state='selected'),
                 item('BANK_RIGHT', '向右侧倾', kind='button')],
                '设施 hasSeatRotation，当前为不设置速度的轨道段，支持 flatRollBanking。',
                note='座椅旋转只在支持此能力的设施中显示。', actions=[item('CONSTRUCT', '建造此段')],
                hero=('illustration', 'dragon_coaster'))
    assign(key, '06-entrance-exit', '入口与出口')
    render_page(store, key, unit, '06-entrance-exit', '轨道建造  出入口',
                [item('ENTRANCE', '建造或移动入口', kind='button', state='selected'), item('EXIT', '建造或移动出口', kind='button'),
                 item('ROTATE', '旋转 90°', kind='button')],
                '设施支持车站出入口，选择入口或出口放置工具。',
                note='入口连接排队道路，出口连接普通步道。', hero=('illustration', 'dragon_coaster'))
    assign(key, '07-track-style', '坡度与侧倾')
    render_page(store, key, unit, '07-track-style', '轨道建造  轨道样式',
                [item('U_TRACK', '开放式轨道', kind='button', state='selected'),
                 item('O_TRACK', '覆盖式轨道', kind='button')],
                'trackDrawerDescriptor.HasCoveredPieces() 为真，当前轨道元素有效且非速度设置段。',
                note='此设施可在开放式与覆盖式轨道之间选择。', hero=('illustration', 'bamboo_flume'))


def path_pages(store):
    key, unit = 'footpath', 'Footpath'
    for mode, tab, bridge in [('01-ground', '地面铺设', False), ('02-bridge', '桥梁与隧道', True), ('03-area', '区域拖建', False)]:
        assign(key, mode, tab)
        specs = [item('FOOTPATH_TYPE', '普通道路路面', '青石步道', 'dropdown'),
                 item('QUEUELINE_TYPE', '排队道路路面', '玉绿排队路', 'dropdown'),
                 item('RAILINGS_TYPE', '道路栏杆', '金玉栏杆', 'dropdown')]
        specs += [item(i, l, kind='button', state='selected' if (bridge and i == 'DIRECTION_NE') else 'normal' if bridge else 'disabled')
                  for i, l in [('DIRECTION_NW', '西北'), ('DIRECTION_NE', '东北'), ('DIRECTION_SW', '西南'), ('DIRECTION_SE', '东南')]]
        specs += [item(i, l, kind='button', state='selected' if bridge and i == 'LEVEL' else 'normal' if bridge else 'disabled')
                  for i, l in [('SLOPEDOWN', '下坡'), ('LEVEL', '水平'), ('SLOPEUP', '上坡')]]
        # Mode buttons are the source-defined navigation controls, not invented
        # dropdown values. The construction buttons are conditional on bridge mode.
        render_page(store, key, unit, mode, '步道建设  ' + tab, specs,
                    'bridgeOrTunnel=' + str(bridge) + '; 方向可用性还受 validDirections 约束，此例为四向可用。',
                    note='桥梁与隧道逐段设置方向与坡度；地面和区域模式直接选择位置。',
                    actions=[item('CONSTRUCT', '建造道路', state='normal' if bridge else 'disabled'),
                             item('REMOVE', '移除上一段', state='normal' if bridge else 'disabled')])
    assign(key, '04-mode-switch', '地面铺设')
    render_page(store, key, unit, '04-mode-switch', '步道建设  选择铺设方式',
                [item('CONSTRUCT_ON_LAND', '在地面铺设', kind='button', state='selected'),
                 item('CONSTRUCT_BRIDGE_OR_TUNNEL', '建造桥梁或隧道', kind='button'),
                 item('CONSTRUCT_DRAG_AREA', '按区域拖建', kind='button')],
                '铺设方式可切换，当前选择地面铺设。', hero=('illustration', 'mountain_scenario'))


def staff_pages(store):
    key, unit = 'staff', 'Staff'
    for mode, tab, working in [('01-overview', '员工概览', False), ('02-working', '作业状态', True)]:
        assign(key, mode, tab)
        specs = [item('PICKUP', '移动到新位置', kind='button', state='disabled' if working else 'normal'),
                 item('PATROL', '设置巡逻区域', kind='button'), item('RENAME', '修改员工姓名', kind='button'),
                 item('LOCATE', '定位员工', kind='button'), item('FIRE', '解雇员工', kind='button', state='disabled' if working else 'normal')]
        render_page(store, key, unit, mode, '清风  维修工', specs,
                    '当前正在维修或检查，禁止搬运与解雇。' if working else '员工没有处于禁止搬运或解雇的工作状态。',
                    note='正在检查游龙飞车。' if working else '当前巡逻区域：东侧设施区。',
                    hero=('illustration', 'mechanic'))
    assign(key, '03-handyman', '清洁职责')
    render_page(store, key, unit, '03-handyman', '清洁工  工作职责',
                [item('CHECKBOX_1', '清扫步道', kind='checkbox', checked=True),
                 item('CHECKBOX_2', '浇灌花园', kind='checkbox', checked=True),
                 item('CHECKBOX_3', '清空垃圾桶', kind='checkbox', checked=True),
                 item('CHECKBOX_4', '修剪草地', kind='checkbox', checked=False)],
                'StaffType::handyman；四个职责复选框可见，服装选择隐藏。',
                hero=('illustration', 'cleaner'))
    assign(key, '04-mechanic', '维修职责')
    render_page(store, key, unit, '04-mechanic', '维修工  工作职责',
                [item('CHECKBOX_1', '检查设施', kind='checkbox', checked=True),
                 item('CHECKBOX_2', '修理设施', kind='checkbox', checked=True)],
                'StaffType::mechanic；只显示检查与修理两项，另外两个复选框与服装选择隐藏。',
                hero=('illustration', 'mechanic'))
    assign(key, '05-costume', '表演服装')
    render_page(store, key, unit, '05-costume', '表演者  选择服装',
                [item('COSTUME_BOX', '演出服装', '当前对象的服装名称', 'dropdown', parts={'dropdown': 'WIDX_COSTUME_BTN'})],
                'StaffType::entertainer；下拉项由当前可用动画对象的 friendlyName 构成，职责复选框隐藏。',
                note='服装列表随本园区已加载的人物动画对象变化。', hero=('icon', 'entertainer'))


OPTION_LABELS = {
    'FULLSCREEN': '窗口模式', 'RESOLUTION': '分辨率', 'SCALE': '界面缩放', 'DRAWING_ENGINE': '渲染引擎',
    'FRAME_RATE_LIMIT': '帧率上限', 'VIRTUAL_FLOOR': '虚拟楼层', 'LANGUAGE': '语言', 'CURRENCY': '货币',
    'DISTANCE': '距离与速度单位', 'TEMPERATURE': '温度单位', 'HEIGHT_LABELS': '高度单位', 'DATE_FORMAT': '日期格式',
    'SOUND': '声音设备', 'TITLE_MUSIC': '主菜单音乐', 'MASTER_VOLUME': '主音量', 'SOUND_VOLUME': '音效音量',
    'MUSIC_VOLUME': '设施音乐音量', 'THEMES': '界面主题', 'TITLE_SEQUENCE': '主菜单游园动画',
    'SCENARIO_PREVIEWS': '场景预览类型', 'DEFAULT_INSPECTION_INTERVAL': '默认设施检查间隔',
    'AUTOSAVE_FREQUENCY': '自动保存频率', 'AUTOSAVE_AMOUNT': '自动保存数量',
    'GAMEPAD_DEADZONE': '手柄死区', 'GAMEPAD_SENSITIVITY': '手柄灵敏度',
    'HOTKEY_DROPDOWN': '快捷键设置', 'EXPORT_EMSCRIPTEN_DATA': '导出网页游戏数据', 'IMPORT_EMSCRIPTEN_DATA': '导入网页游戏数据',
}
OPTION_VALUES = {
    'FULLSCREEN': '全屏', 'RESOLUTION': '1920 × 1080', 'SCALE': '100%', 'DRAWING_ENGINE': 'OpenGL',
    'FRAME_RATE_LIMIT': '60 FPS', 'VIRTUAL_FLOOR': '透明', 'LANGUAGE': '简体中文', 'CURRENCY': '铜钱（主题示例）',
    'DISTANCE': '公制', 'TEMPERATURE': '摄氏度', 'HEIGHT_LABELS': '米', 'DATE_FORMAT': '日 / 月 / 年',
    'SOUND': '默认输出设备', 'TITLE_MUSIC': '当前安装的标题音乐', 'MASTER_VOLUME': '80%', 'SOUND_VOLUME': '75%',
    'MUSIC_VOLUME': '60%', 'THEMES': '云游仙苑', 'TITLE_SEQUENCE': '当前安装的游园动画',
    'SCENARIO_PREVIEWS': '小地图', 'DEFAULT_INSPECTION_INTERVAL': '30 分钟', 'AUTOSAVE_FREQUENCY': '每 5 分钟',
    'AUTOSAVE_AMOUNT': '10', 'GAMEPAD_DEADZONE': '20%', 'GAMEPAD_SENSITIVITY': '65%',
}


def option_pages(store):
    key, unit = 'options', 'Options'
    controls = [c for c in SOURCE['controls'] if c['unit'] == unit and not c.get('excludedFromInteractiveCount')]
    child_ids = set()
    for control in controls:
        if control.get('sourceWidgetType') in ('spinner', 'dropdownMenu'):
            child_ids.update(suffix_parts(unit, control['controlId']).values())
    groups = {tab: [] for tab in PAGE_TABS[key]}
    for control in controls:
        cid = control['controlId']
        if cid in child_ids or control.get('sourceWidgetType') in ('label', 'groupbox', 'tableHeader'):
            continue
        if cid in ('WIDX_EXPORT_EMSCRIPTEN_DATA', 'WIDX_IMPORT_EMSCRIPTEN_DATA'):
            continue
        pages = control.get('existingPageGroups') or []
        if len(pages) != 1 or pages[0] not in groups:
            continue
        base = cid.removeprefix('WIDX_')
        label = OPTION_LABELS.get(base)
        if not label:
            labels = [clean_label(v['zhCN']) for v in control['sourceLabels'] if v.get('zhCN')]
            labels = [v for v in labels if v]
            if labels:
                label = labels[0]
            else:
                raise ValueError('Options label is missing: ' + cid)
        kind = infer_kind(control)
        groups[pages[0]].append(item(cid, label, OPTION_VALUES.get(base), kind,
                                     checked=kind == 'checkbox' and base not in ('MINIMIZE_FOCUS_LOSS', 'SHOW_FPS_CHECKBOX', 'STAY_CONNECTED_AFTER_DESYNC')))
    for ti, (tab, specs) in enumerate(groups.items()):
        chunks = [specs[i:i + 10] for i in range(0, len(specs), 10)]
        for pi, chunk in enumerate(chunks):
            mode = f'{ti + 1:02}-{tab}-{pi + 1:02}'
            assign(key, mode, tab)
            render_page(store, key, unit, mode, '游戏设置  ' + tab, chunk,
                        '当前是桌面版，适用的渲染/设备选项已启用；即时变更，不增加应用确认。',
                        note='设置调整后即时保存。' + (f'  本类第 {pi + 1} 页 / 共 {len(chunks)} 页' if len(chunks) > 1 else ''))
    assign(key, '09-web-data', '高级')
    render_page(store, key, unit, '09-web-data', '游戏设置  网页数据管理',
                [item('EXPORT_EMSCRIPTEN_DATA', '导出网页游戏数据', kind='button'),
                 item('IMPORT_EMSCRIPTEN_DATA', '导入网页游戏数据', kind='button')],
                '仅 Emscripten 网页构建显示，桌面构建不显示这些入口。', note='网页游戏的数据导入与导出。',
                hero=('icon', 'save'))


def mapgen_pages(store):
    key, unit = 'map-gen', 'MapGen'
    base = lambda disabled=False: [item('MAP_SIZE_X', '地图宽度', '128', 'spinner', state='disabled' if disabled else 'normal'),
                                   item('MAP_SIZE_Y', '地图高度', '128', 'spinner', state='disabled' if disabled else 'normal'),
                                   item('MAP_SIZE_LINK', '保持正方形', kind='button', state='disabled' if disabled else 'selected')]
    assign(key, '01-flatland', '平地')
    render_page(store, key, unit, '01-flatland', '地图生成  平地',
                base() + [item('HEIGHTMAP_SOURCE', '地形来源', '平地', 'dropdown')],
                'Algorithm::blank；高度图和噪声参数隐藏。', actions=[item('MAP_GENERATE', '生成地图')], hero=('illustration', 'mountain_scenario'))
    assign(key, '02-noise', '噪声')
    render_page(store, key, unit, '02-noise', '地图生成  噪声',
                base() + [item('HEIGHTMAP_SOURCE', '地形来源', 'Simplex 噪声', 'dropdown'),
                          item('SIMPLEX_BASE_FREQ', '基础频率', '0.50', 'spinner'), item('SIMPLEX_OCTAVES', '噪声层数', '6', 'spinner')],
                'Algorithm::simplexNoise；显示频率和层数，高度图参数隐藏。', actions=[item('MAP_GENERATE', '生成地图')])
    for mode, loaded, smooth in [('03-image-unloaded', False, False), ('04-image-loaded', True, False), ('05-image-smooth', True, True)]:
        assign(key, mode, '高度图')
        specs = base(True) + [item('HEIGHTMAP_SOURCE', '地形来源', '高度图文件', 'dropdown'),
                 item('HEIGHTMAP_BROWSE', '选择高度图文件', kind='button'),
                 item('HEIGHTMAP_NORMALIZE', '归一化高度图', kind='checkbox', checked=loaded, state='normal' if loaded else 'disabled'),
                 item('HEIGHTMAP_SMOOTH_HEIGHTMAP', '平滑高度图', kind='checkbox', checked=smooth, state='normal' if loaded else 'disabled'),
                 item('HEIGHTMAP_STRENGTH', '高度图平滑强度', '4', 'spinner', state='normal' if loaded and smooth else 'disabled')]
        render_page(store, key, unit, mode, '地图生成  高度图', specs,
                    f'Algorithm::heightmapImage；heightmapLoaded={loaded}；smooth_height_map={smooth}。尺寸和正方形锁定禁用；强度仅加载且平滑时启用。',
                    note='已载入：青云山势.png' if loaded else '尚未载入高度图，请先选择文件。',
                    actions=[item('MAP_GENERATE', '生成地图', state='normal' if loaded else 'disabled')])
    assign(key, '06-terrain', '地形')
    render_page(store, key, unit, '06-terrain', '地图生成  地形参数',
                [item('HEIGHTMAP_LOW', '最低地形高度', '8', 'spinner'), item('HEIGHTMAP_HIGH', '最高地形高度', '32', 'spinner'),
                 item('FLOOR_TEXTURE', '地表材质', '自然青灰石', 'dropdown'), item('WALL_TEXTURE', '崖面材质', '浅灰岩壁', 'dropdown'),
                 item('SURFACE_COLOUR_1', '地表颜色', '#A6B8AA', 'color'), item('EDGE_COLOUR_1', '崖面颜色', '#A7ADA7', 'color'),
                 item('RANDOM_TERRAIN', '随机地形', kind='checkbox', checked=False),
                 item('HEIGHTMAP_SMOOTH_TILE_EDGES', '平滑地块边缘', kind='checkbox', checked=True)],
                '当前为 Simplex 地形、randomTerrain=false，地表/崖面样式可用；选择的对象支持颜色。非平地算法可平滑地块边缘。',
                actions=[item('MAP_GENERATE', '生成地图')])
    assign(key, '07-water', '水域')
    render_page(store, key, unit, '07-water', '地图生成  水域',
                [item('WATER_LEVEL', '水位', '8', 'spinner'), item('ADD_BEACHES', '在水体周围增加海滩', kind='checkbox', checked=True)],
                '水域页：水位与海滩开关。', actions=[item('MAP_GENERATE', '生成地图')], hero=('illustration', 'lake_scenario'))
    for mode, trees in [('08-forest', True), ('09-forest-disabled', False)]:
        assign(key, mode, '森林')
        render_page(store, key, unit, mode, '地图生成  森林',
                    [item('FORESTS_PLACE_TREES', '放置树木', kind='checkbox', checked=trees),
                     item('TREE_LAND_RATIO', '树木与土地比例', '35%', 'spinner', state='normal' if trees else 'disabled'),
                     item('TREE_ALTITUDE_MIN', '树木最低海拔', '8', 'spinner', state='normal' if trees else 'disabled'),
                     item('TREE_ALTITUDE_MAX', '树木最高海拔', '28', 'spinner', state='normal' if trees else 'disabled')],
                    f'placeTrees={trees}；未勾选放置树木时禁用比例和海拔控制。',
                    actions=[item('MAP_GENERATE', '生成地图')], hero=('illustration', 'mountain_scenario'))


def inspector_pages(store):
    key, unit = 'tile-inspector', 'TileInspector'
    assign(key, '01-element-tools', '元素操作')
    render_page(store, key, unit, '01-element-tools', '地块检查  元素操作',
                [item('SPINNER_X', '地块 X 坐标', '64', 'spinner'), item('SPINNER_Y', '地块 Y 坐标', '72', 'spinner'),
                 item('BUTTON_COPY', '复制所选元素', kind='button'), item('BUTTON_PASTE', '粘贴元素', kind='button'),
                 item('BUTTON_MOVE_UP', '元素上移', kind='button'), item('BUTTON_MOVE_DOWN', '元素下移', kind='button'),
                 item('BUTTON_ROTATE', '旋转所选元素', kind='button'), item('BUTTON_SORT', '按基础高度排序', kind='button'),
                 item('BUTTON_REMOVE', '移除所选元素', kind='button')],
                '已选择一个元素且剪贴板已有可粘贴元素；移动按钮还受元素顺序约束。',
                note='高级地块编辑 · 改动即时作用于当前园区。')
    inspector_list_page(store)
    pages = [
        ('02-surface', '地表', [item('SURFACE_SPINNER_HEIGHT', '基础高度', '8', 'spinner'),
             item('SURFACE_BUTTON_REMOVE_FENCES', '移除园区边界', kind='button'), item('SURFACE_BUTTON_RESTORE_FENCES', '还原园区边界', kind='button')]
             + [item('SURFACE_CHECK_CORNER_' + d, '抬高' + label + '角', kind='checkbox', checked=d == 'N') for d, label in [('N', '北'), ('E', '东'), ('S', '南'), ('W', '西')]]
             + [item('SURFACE_CHECK_DIAGONAL', '斜角地形', kind='checkbox')]),
        ('03-path', '步道', [item('PATH_SPINNER_HEIGHT', '基础高度', '8', 'spinner'), item('PATH_CHECK_BROKEN', '道路附件损坏', kind='checkbox'),
             item('PATH_CHECK_SLOPED', '坡道', kind='checkbox', checked=True), item('PATH_CHECK_JUNCTION_RAILINGS', '路口显示栏杆', kind='checkbox', checked=True)]
             + [item('PATH_CHECK_EDGE_' + d, label + '连通边', kind='checkbox', checked=d in ('NE', 'SW')) for d, label in [('NE', '东北'), ('E', '东'), ('SE', '东南'), ('S', '南'), ('SW', '西南'), ('W', '西'), ('NW', '西北'), ('N', '北')]]),
        ('04-track', '轨道', [item('TRACK_SPINNER_HEIGHT', '基础高度', '16', 'spinner'), item('TRACK_CHECK_APPLY_TO_ALL', '应用于整个轨道组件', kind='checkbox', checked=True),
             item('TRACK_CHECK_CHAIN_LIFT', '链条提升坡', kind='checkbox', checked=True), item('TRACK_CHECK_BRAKE_CLOSED', '关闭制动器', kind='checkbox'),
             item('TRACK_CHECK_IS_INDESTRUCTIBLE', '不可拆除', kind='checkbox')]),
        ('05-small-scenery', '小景物', [item('SCENERY_SPINNER_HEIGHT', '基础高度', '8', 'spinner')]
             + [item('SCENERY_CHECK_QUARTER_' + d, label + '侧占用区', kind='checkbox', checked=d == 'N') for d, label in [('N', '北'), ('E', '东'), ('S', '南'), ('W', '西')]]
             + [item('SCENERY_CHECK_COLLISION_' + d, label + '侧碰撞区', kind='checkbox', checked=d == 'N') for d, label in [('N', '北'), ('E', '东'), ('S', '南'), ('W', '西')]]),
        ('06-large-scenery', '大景物', [item('LARGE_SCENERY_SPINNER_HEIGHT', '基础高度', '8', 'spinner')]),
        ('07-wall-sloped', '墙', [item('WALL_SPINNER_HEIGHT', '基础高度', '8', 'spinner'), item('WALL_DROPDOWN_SLOPE', '墙体坡度', '上坡', 'dropdown'),
             item('WALL_SPINNER_ANIMATION_FRAME', '动画帧', '0', 'spinner', state='disabled'), item('WALL_ANIMATION_IS_BACKWARDS', '反向播放动画', kind='checkbox', state='disabled')]),
        ('08-wall-animated', '墙', [item('WALL_SPINNER_HEIGHT', '基础高度', '8', 'spinner'), item('WALL_DROPDOWN_SLOPE', '墙体坡度', '水平', 'dropdown', state='disabled'),
             item('WALL_SPINNER_ANIMATION_FRAME', '动画帧', '3', 'spinner'), item('WALL_ANIMATION_IS_BACKWARDS', '反向播放动画', kind='checkbox', checked=True)]),
        ('09-entrance', '入口', [item('ENTRANCE_SPINNER_HEIGHT', '基础高度', '8', 'spinner'), item('ENTRANCE_BUTTON_MAKE_USABLE', '设为有效入口或出口', kind='button')]),
        ('10-banner', '横幅', [item('BANNER_SPINNER_HEIGHT', '基础高度', '12', 'spinner')]
             + [item('BANNER_CHECK_BLOCK_' + d, '允许' + label + '通行', kind='checkbox', checked=d == 'NE') for d, label in [('NE', '东北'), ('SE', '东南'), ('SW', '西南'), ('NW', '西北')]]),
    ]
    for mode, tab, specs in pages:
        assign(key, mode, tab)
        condition = '选中有效的' + tab + '元素。'
        if mode == '07-wall-sloped':
            condition += ' canBeSloped=true；hasAnimation=false。'
        if mode == '08-wall-animated':
            condition += ' canBeSloped=false；hasAnimation=true。'
        if mode == '09-entrance':
            condition += ' 当前为设施入口或出口，允许更新该站台的有效位置。'
        # The path page has twelve specific controls; split it into two readable
        # product subpages rather than shrinking Chinese text below 22px.
        chunks = [specs[i:i + 10] for i in range(0, len(specs), 10)]
        for ci, chunk in enumerate(chunks):
            page_mode = mode + (f'-{ci + 1}' if len(chunks) > 1 else '')
            assign(key, page_mode, tab)
            render_page(store, key, unit, page_mode, '地块检查  ' + tab, chunk, condition,
                        note='地块坐标 64, 72 · 方向基于当前视图',
                        actions=[item('BUTTON_ROTATE', '旋转元素'), item('BUTTON_COPY', '复制元素'), item('BUTTON_REMOVE', '移除元素')],
                        hero=('illustration', 'mountain_scenario') if len(chunk) <= 4 else None)


def inspector_list_page(store):
    key, unit, mode = 'tile-inspector', 'TileInspector', '00-element-list'
    assign(key, mode, '元素操作')
    identity = 'detail:tile-inspector:' + mode
    c = DetailCanvas(store, identity, '地块检查  元素列表', unit,
                     '已选中地块64,72；当前选中轨道元素，剪贴板有可粘贴元素。')
    record = dict(INVENTORY[key], title='地块检查', tabs=PAGE_TABS[key])
    x, y, width, height = c.frame(record, '元素操作', 0)
    c.panel((x, y, width, 334))
    columns = [('COLUMN_INVISIBLE', '可见', 110), ('COLUMN_TYPE', '元素类型', 260),
               ('COLUMN_BASEHEIGHT', '基础高度', 170), ('COLUMN_CLEARANCEHEIGHT', '净空高度', 170),
               ('COLUMN_DIRECTION', '方向', 160), ('COLUMN_GHOSTFLAG', '幽灵标记', 170),
               ('COLUMN_LASTFLAG', '最后元素', 170)]
    cx = x + 46
    for control, label, column_width in columns:
        c.text(label, (cx, y + 27, column_width - 10, 40), 22, color=ui.JADE)
        c.mark('WIDX_' + control, (cx, y + 15, column_width - 10, 58), 'table-header', label)
        cx += column_width
    rows = [['是', '地表', '8', '8', '—', '否', '否'], ['是', '步道', '8', '12', '东北', '否', '否'],
            ['是', '轨道', '16', '22', '东北', '否', '否'], ['是', '墙体', '8', '16', '东南', '否', '是']]
    for row_i, values in enumerate(rows):
        cy = y + 82 + row_i * 58
        cx = x + 46
        for value, (_, _, column_width) in zip(values, columns):
            c.text(value, (cx, cy + 8, column_width - 10, 38), 23)
            cx += column_width
        c.lines([(x + 35, cy + 54), (x + width - 35, cy + 54)], width=1)
    c.mark('WIDX_LIST', (x + 25, y + 76, width - 50, 242), 'scrolling-element-list', '当前地块的元素列表')
    half = int((width - 35) / 2)
    c.control(item('SPINNER_X', '地块 X 坐标', '64', 'spinner'), (x, y + 365, half, 95))
    c.control(item('SPINNER_Y', '地块 Y 坐标', '72', 'spinner'), (x + half + 35, y + 365, half, 95))
    c.text('选择元素后可复制、粘贴、旋转或调整顺序。', (x + 8, 870, width - 16, 37), 22, color=ui.MUTED)
    for i, spec in enumerate([item('BUTTON_COPY', '复制元素'), item('BUTTON_PASTE', '粘贴元素'), item('BUTTON_SORT', '按基础高度排序')]):
        c.control(spec, (x + i * 450, 904, 420, 90))
    path = ROOT / 'designs/details/tile-inspector' / (mode + '.png')
    result = c.save(path, {'referenceCommit': '52a55c3e8da5972460642bdfed61d091fe9cabfd',
                           'sourceUnit': unit, 'sourceControls': c.coverage, 'condition': c.condition})
    SCREENS.append({'id': identity, 'key': key, 'system': '编辑器', 'title': c.title, 'tab': '元素操作',
                    'condition': c.condition, 'sourceUnit': unit, 'file': result['file'], 'layoutFile': result['layoutFile'],
                    'sourceRecord': result['sourceRecord'], 'assetPaths': result['assetPaths'],
                    'productionStatus': result['productionStatus'], 'acceptanceStatus': result['acceptanceStatus'],
                    'layoutIssues': result['layoutIssues'], 'sourceControlKeys': sorted({v for e in c.coverage for v in e['sourceControlKeys']})})
    for entry in c.coverage:
        entry['file'], entry['layoutFile'] = result['file'], result['layoutFile']
        COVERAGE.append(entry)
    print(identity, 'controls', len(c.coverage), 'issues', len(c.issues), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', action='append', choices=['ride-construction', 'footpath', 'staff', 'options', 'map-gen', 'tile-inspector'])
    args = parser.parse_args()
    store = ui.AssetStore(ROOT)
    tasks = [('ride-construction', ride_pages), ('footpath', path_pages), ('staff', staff_pages),
             ('options', option_pages), ('map-gen', mapgen_pages), ('tile-inspector', inspector_pages)]
    for key, fn in tasks:
        if not args.only or key in args.only:
            fn(store)
    path = ROOT / 'docs/detail-ui-production-manifest.json'
    old_screens, old_coverage = [], []
    if args.only and path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        ids = {s['id'] for s in SCREENS}
        old_screens = [s for s in previous.get('screens', []) if s['id'] not in ids]
        old_coverage = [s for s in previous.get('coverage', []) if s['screenId'] not in ids]
    ui.write_json(path, {'schemaVersion': 1, 'createdAt': datetime.now().astimezone().isoformat(),
                        'artScope': 'actual product proposal',
                        'referenceCommit': '52a55c3e8da5972460642bdfed61d091fe9cabfd',
                        'referenceResolution': [1920, 1080],
                        'method': 'Compose existing painted PNG assets with separate Chinese text and source-backed control geometry.',
                        'status': 'produced_pending_review',
                        'layoutIssueCount': sum(len(s['layoutIssues']) for s in old_screens + SCREENS),
                        'screens': old_screens + SCREENS, 'coverage': old_coverage + COVERAGE,
                        'scopeNote': 'Supplemental feature detail pages, not source-code/style contract boards. Conditional widgets are shown in separate valid modes. No Unity runtime validation.'})
    print('DETAILS', len(old_screens + SCREENS), 'controls', len(old_coverage + COVERAGE),
          'layoutIssues', sum(len(s['layoutIssues']) for s in old_screens + SCREENS), flush=True)


if __name__ == '__main__':
    main()
