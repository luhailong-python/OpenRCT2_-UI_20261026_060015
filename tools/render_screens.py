"""Compose the OpenRCT2 Taoist UI art previews from the delivered painted kit.

This script creates layout previews and source records, not native AI images.
It does not generate decorative artwork, change the source repository, or run Unity.
Run only after assets/slice-manifest.json and the illustration exports are ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
W, H = 1920, 1080
JADE = '#174F43'
DEEP = '#183F36'
MUTED = '#7A745E'
GOLD = '#B28C43'
CREAM = '#FFF8DF'
RED = '#AB4537'
GREEN = '#397D60'
PAPER = '#F5EEDC'
BLUE = '#4D8292'
FONT_FILES = {
    'title': Path('C:/Windows/Fonts/simkai.ttf'),
    'body': Path('C:/Windows/Fonts/msyh.ttc'),
    'bold': Path('C:/Windows/Fonts/msyhbd.ttc'),
}
# Prefer the independently licensed, task-local fonts once the art export worker
# has delivered them. Never copy the installed Microsoft fonts into the package.
if (ROOT / 'assets/fonts/NotoSansCJKsc-Regular.otf').exists():
    FONT_FILES['body'] = ROOT / 'assets/fonts/NotoSansCJKsc-Regular.otf'
    FONT_FILES['bold'] = FONT_FILES['body']
if (ROOT / 'assets/fonts/MaShanZheng-Regular.ttf').exists():
    FONT_FILES['title'] = ROOT / 'assets/fonts/MaShanZheng-Regular.ttf'
FONT_CACHE: dict = {}
ICON_SUBJECTS = {
    0: 'pause', 1: 'fast_forward', 2: 'save', 3: 'display', 4: 'mountain',
    5: 'path', 6: 'roller_coaster', 7: 'pine_tree', 8: 'visitor', 9: 'mechanic',
    10: 'coins', 11: 'research', 12: 'news', 13: 'multiplayer',
    20: 'path', 21: 'queue', 22: 'bench', 23: 'lantern', 24: 'mountain',
    25: 'path', 35: 'clock', 37: 'rating', 38: 'warning', 39: 'information',
    42: 'information', 44: 'success', 45: 'warning', 55: 'eyedropper',
}
ILLUSTRATION_SUBJECTS = {
    0: 'dragon_coaster', 1: 'celestial_wheel', 2: 'gourd_carousel',
    3: 'bamboo_flume', 4: 'cloud_train', 5: 'hedge_maze',
    6: 'achievement_trophy', 7: 'tea_keeper', 8: 'cleaner',
    9: 'mechanic', 10: 'lake_scenario', 11: 'mountain_scenario',
}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def font(size=26, family='body'):
    key = (size, family)
    if key not in FONT_CACHE:
        path = FONT_FILES[family]
        if not path.exists():
            path = FONT_FILES['body']
        if not path.exists():
            raise FileNotFoundError('A Chinese font is required: C:/Windows/Fonts/msyh.ttc')
        FONT_CACHE[key] = ImageFont.truetype(str(path), size)
    return FONT_CACHE[key]


class AssetStore:
    def __init__(self, root: Path):
        self.root = root
        self.manifest_path = root / 'assets/slice-manifest.json'
        self.manifest = json.loads(self.manifest_path.read_text(encoding='utf-8'))
        self.entries = {}
        for entry in self.manifest.get('assets', []) + self.manifest.get('icons', []):
            if isinstance(entry, dict) and entry.get('file'):
                self.entries[entry.get('name', Path(entry['file']).stem)] = entry
        self.cache, self.info_cache = {}, {}
        self.files = list((root / 'assets').rglob('*.png'))
        self.icons = sorted([p for p in self.files if 'icons' in p.parts], key=lambda p: p.name)
        self.illustrations = sorted([p for p in self.files if 'illustrations' in p.parts], key=lambda p: p.name)
        self.background = root / 'assets/backgrounds/park-day-native.png'
        if not self.background.exists():
            raise FileNotFoundError(self.background)
        for name in ['panel_main', 'panel_card', 'title_plate', 'toolbar', 'primary_normal',
                     'primary_disabled', 'secondary_normal', 'tab_normal', 'tab_selected',
                     'close', 'slider_track', 'slider_thumb', 'progress_track', 'progress_fill']:
            self.path(name)
        if not self.icons:
            raise RuntimeError('No independent painted icons have been exported yet.')

    def path(self, name) -> Path:
        if isinstance(name, Path):
            return name
        candidate = self.entries.get(name)
        if candidate:
            return self.root / candidate['file']
        candidates = [p for p in self.files if p.stem == name]
        if not candidates:
            raise FileNotFoundError(f'Painted asset missing: {name}')
        return candidates[0]

    def load(self, name):
        path = self.path(name)
        if path not in self.cache:
            self.cache[path] = Image.open(path).convert('RGBA')
        return self.cache[path]

    def info(self, name):
        path = self.path(name)
        if path not in self.info_cache:
            image = self.load(path)
            generation = Path(str(path) + '.generation.json')
            source = Path(str(path) + '.source.json')
            self.info_cache[path] = {
                'file': rel(path), 'sha256': digest(path),
                'nativeDimensions': list(image.size),
                'generationRecord': rel(generation) if generation.exists() else None,
                'derivationRecord': rel(source) if source.exists() else 'assets/slice-manifest.json',
            }
        return self.info_cache[path]

    def border(self, name):
        entry = self.entries.get(name, {})
        border = entry.get('borderLeftBottomRightTop')
        if border:
            return tuple(int(x) for x in border)
        image = self.load(name)
        x = min(48, max(12, image.width // 5))
        y = min(32, max(10, image.height // 4))
        return x, y, x, y

    def icon(self, index=0, subject=None):
        subject = subject or ICON_SUBJECTS.get(index, 'information')
        aliases = {'color': 'eyedropper'}
        subject = aliases.get(subject, subject)
        matches = [p for p in self.icons if p.stem == subject]
        if not matches:
            raise FileNotFoundError('Semantic icon is missing: ' + subject)
        return matches[0]

    def illustration(self, index=0, subject=None):
        subject = subject or ILLUSTRATION_SUBJECTS.get(index, 'mountain_scenario')
        matches = [p for p in self.illustrations if p.stem == subject]
        if not matches:
            raise FileNotFoundError('Semantic illustration is missing: ' + subject)
        return matches[0]


def nine_slice(source: Image.Image, size, border):
    width, height = map(int, size)
    left, bottom, right, top = border
    left = min(left, source.width // 2 - 1, width // 2 - 1)
    right = min(right, source.width // 2 - 1, width // 2 - 1)
    top = min(top, source.height // 2 - 1, height // 2 - 1)
    bottom = min(bottom, source.height // 2 - 1, height // 2 - 1)
    sx = (0, left, source.width - right, source.width)
    sy = (0, top, source.height - bottom, source.height)
    dx = (0, left, width - right, width)
    dy = (0, top, height - bottom, height)
    result = Image.new('RGBA', (width, height))
    for row in range(3):
        for column in range(3):
            crop = source.crop((sx[column], sy[row], sx[column + 1], sy[row + 1]))
            target = (dx[column + 1] - dx[column], dy[row + 1] - dy[row])
            if min(target) > 0:
                result.alpha_composite(crop.resize(target, Image.Resampling.LANCZOS), (dx[column], dy[row]))
    return result


class Canvas:
    def __init__(self, store: AssetStore, identity, title):
        self.store, self.identity, self.title = store, identity, title
        self.used, self.texts, self.widgets, self.shapes, self.issues = {}, [], [], [], []
        self.image = Image.new('RGBA', (W, H))
        self.draw = ImageDraw.Draw(self.image)
        self.place(store.background, (0, 0, W, H), mode='cover', role='park-background')

    def use(self, name):
        path = self.store.path(name)
        self.used[rel(path)] = self.store.info(path)
        return self.store.load(path)

    def place(self, name, box, mode='contain', role='illustration'):
        x, y, width, height = [int(v) for v in box]
        source = self.use(name)
        if mode == 'cover':
            placed = ImageOps.fit(source, (width, height), Image.Resampling.LANCZOS)
            self.image.alpha_composite(placed, (x, y))
        elif mode == 'nine':
            border = self.store.border(str(name))
            entry = self.store.entries.get(str(name), {})
            if entry.get('resizeAxes') == 'horizontal':
                # Preserve the complete painted face, including its padding and
                # tassels: scale uniformly, then stretch only along the x-axis.
                scale = height / source.height
                source = source.resize((round(source.width * scale), height), Image.Resampling.LANCZOS)
                border = tuple(round(v * scale) for v in border)
            placed = nine_slice(source, (width, height), border)
            self.image.alpha_composite(placed, (x, y))
        elif mode == 'stretch':
            self.image.alpha_composite(source.resize((width, height), Image.Resampling.LANCZOS), (x, y))
        else:
            placed = ImageOps.contain(source, (width, height), Image.Resampling.LANCZOS)
            self.image.alpha_composite(placed, (x + (width - placed.width) // 2, y + (height - placed.height) // 2))
        self.widgets.append({'role': role, 'asset': rel(self.store.path(name)),
                             'region': [x, y, width, height], 'resize': mode})

    def panel(self, box, name='panel_card'):
        self.place(name, box, mode='nine', role='panel')

    def lines(self, points, color=GOLD, width=2, role='data-rule'):
        self.draw.line(points, fill=color, width=width)
        self.shapes.append({'role': role, 'points': points, 'color': color, 'width': width})

    def text(self, text, box, size=26, color=DEEP, family='body', align='left', valign='top',
             role='dynamic-text', max_lines=None, minimum=22):
        text = str(text)
        # FreeType probes found these four unsupported Ma Shan Zheng glyphs;
        # use the bundled Noto face for the whole layer, preserving text and metrics.
        if family == 'title' and any(ch in text for ch in ('·', '›', '⇄', '✓')):
            family = 'body'
        if family == 'title':
            # The licensed calligraphy font omits U+00B7; preserve the title's
            # wording with a spacing separator, rather than render tofu boxes.
            text = text.replace('·', '  ')
        x, y, width, height = box
        chosen = size
        while True:
            tf = font(chosen, family)
            rows = []
            for raw in text.split('\n'):
                current = ''
                for char in raw:
                    if current and self.draw.textlength(current + char, font=tf) > width:
                        rows.append(current)
                        current = char
                    else:
                        current += char
                rows.append(current)
            line_height = int(chosen * 1.42)
            needed = len(rows) * line_height
            if needed <= height and (not max_lines or len(rows) <= max_lines):
                break
            if chosen <= minimum:
                self.issues.append({'type': 'text-overflow', 'text': text, 'region': list(box),
                                    'neededHeight': needed, 'fontSize': chosen})
                break
            chosen -= 1
        ty = y if valign == 'top' else y + max(0, (height - needed) / 2)
        for row in rows:
            length = self.draw.textlength(row, font=tf)
            tx = x + (width - length) / 2 if align == 'center' else x + width - length if align == 'right' else x
            self.draw.text((int(tx), int(ty)), row, font=tf, fill=color, stroke_width=0)
            ty += line_height
        self.texts.append({'id': f'text-{len(self.texts) + 1:03}', 'text': text, 'role': role,
                           'region': list(map(int, box)), 'fontFamily': family,
                           'fontFileReference': str(FONT_FILES[family]), 'fontSize': chosen,
                           'color': color, 'alignment': align, 'verticalAlignment': valign,
                           'lineHeight': line_height, 'wrappedLines': rows,
                           'dynamic': role != 'fixed-art-title'})

    def button(self, text, box, state='normal', primary=True, role='action'):
        family = 'primary' if primary else 'secondary'
        name = f'{family}_{state}'
        try:
            self.store.path(name)
        except FileNotFoundError:
            name = f'{family}_normal'
        self.place(name, box, mode='nine', role=role)
        x, y, width, height = box
        face_y = y + height * (.12 if primary else .13)
        face_h = height * (.55 if primary else .69)
        self.text(text, (x + 24, face_y, width - 48, face_h), size=25,
                  color=CREAM if primary and state != 'disabled' else MUTED if state == 'disabled' else DEEP,
                  family='title', align='center', valign='center', minimum=22)
        self.widgets[-1]['state'] = state

    def icon(self, index, box, subject=None):
        self.place(self.store.icon(index, subject), box, role='icon')

    def illustration(self, index, box, subject=None):
        self.place(self.store.illustration(index, subject), box, role='illustration')

    def progress(self, value, box, label=None, color=GREEN):
        x, y, width, height = box
        self.place('progress_track', box, mode='nine', role='progress-track')
        inset = min(8, height // 5)
        amount = max(0, min(1, value))
        if amount > 0:
            self.place('progress_fill', (x + inset, y + inset, max(12, int((width - inset * 2) * amount)), height - inset * 2),
                       mode='nine', role='progress-fill')
        if label:
            self.text(label, (x, y - 40, width, 36), 24, color=color)

    def checkbox(self, label, box, checked=True):
        x, y, width, height = box
        self.place('checkbox_on' if checked else 'checkbox_off', (x, y + 6, 40, 40), role='checkbox')
        self.text(label, (x + 55, y + 8, width - 60, height - 8), 24)

    def field(self, label, value, box, kind=None):
        x, y, width, height = box
        self.text(label, (x + 5, y + 6, min(240, width * .43), height - 8), 25, color=MUTED)
        control_x = x + int(width * .46)
        control_w = width - (control_x - x)
        value = str(value)
        if kind == 'toggle' or value in ('开启', '关闭', '已开启', '已关闭'):
            checked = value in ('开启', '已开启')
            self.place('toggle_on' if checked else 'toggle_off', (control_x + control_w - 126, y + 4, 112, 48), role='toggle')
            self.text('开' if checked else '关', (control_x, y + 8, control_w - 144, height - 8), 24, align='right')
        elif kind == 'slider' or ('音量' in label) or ('灵敏度' in label):
            track_y = y + 15
            track_width = control_w - 100
            self.place('slider_track', (control_x, track_y, track_width, 20), mode='nine', role='slider-track')
            match = re.search(r'[-+]?\d+(?:\.\d+)?', value)
            fraction = max(0.0, min(1.0, float(match.group()) / 100.0)) if match else .5
            thumb_center = control_x + 10 + (track_width - 20) * fraction
            self.place('slider_thumb', (round(thumb_center - 20), track_y - 15, 40, 50), role='slider-thumb')
            self.widgets[-1]['valueFraction'] = fraction
            self.text(value, (x + width - 90, y + 4, 90, height - 8), 24, align='right')
        elif kind == 'color' or value.startswith('#'):
            self.icon(55, (control_x, y + 2, 50, 50), 'color')
            self.text(value, (control_x + 64, y + 8, control_w - 68, height - 8), 24)
        else:
            self.place('secondary_normal', (control_x, y - 1, control_w, height + 2), mode='nine', role='input-field')
            self.text(value, (control_x + 40, y + 8, control_w - 80, height - 12), 24,
                      valign='center', minimum=22)

    def title_plaque(self, title, subtitle=None):
        self.place('title_plate', (W // 2 - 440, 22, 880, 170), role='title-plaque')
        self.text(title, (W // 2 - 340, 66, 680, 75), size=46, family='title',
                  color=CREAM, align='center', valign='center', minimum=32)
        if subtitle:
            self.text(subtitle, (W // 2 - 270, 141, 540, 36), 22, align='center', color=CREAM)

    def footer(self, phrase='美术设计样例 · 名称 / 数值待定'):
        self.text(phrase, (600, 1046, 720, 28), 18, color=CREAM, align='center', minimum=18)

    def frame(self, record, tab, index):
        self.panel((52, 96, 1816, 930), 'panel_main')
        self.title_plaque(record['title'])
        self.place('close', (1776, 110, 68, 68), role='close')
        tabs = record['tabs']
        if len(tabs) > 4:
            nav = (84, 208, 268, 756)
            self.panel(nav)
            row_height = min(70, int(720 / len(tabs)))
            for ti, item in enumerate(tabs):
                box = (100, 224 + ti * row_height, 236, row_height - 6)
                self.place('tab_selected' if ti == index else 'tab_normal', box, mode='nine', role='navigation-tab')
                self.text(item, (box[0] + 16, box[1] + 7, box[2] - 32, box[3] - 10), 25,
                          color=CREAM if ti == index else DEEP, family='title',
                          align='center', valign='center', minimum=22)
            content = (390, 222, 1408, 640)
        else:
            total = max(1, len(tabs))
            tab_w = min(330, int(1680 / total))
            start = 108
            for ti, item in enumerate(tabs):
                box = (start + ti * (tab_w + 12), 200, tab_w, 66)
                self.place('tab_selected' if ti == index else 'tab_normal', box, mode='nine', role='navigation-tab')
                self.text(item, (box[0] + 20, box[1] + 8, box[2] - 40, 46), 26,
                          color=CREAM if ti == index else DEEP, family='title', align='center', valign='center')
            content = (110, 304, 1684, 556)
        self.text(f'{tab}', (content[0] + 8, content[1] - 4, content[2] - 20, 48), 32, family='title')
        self.lines([(content[0] + 8, content[1] + 54), (content[0] + content[2] - 8, content[1] + 54)], width=1)
        self.footer()
        return (content[0], content[1] + 78, content[2], content[3] - 78)

    def actions(self, labels, disabled=False):
        labels = list(labels)[:3]
        right = 1788
        for index, label in enumerate(reversed(labels)):
            width = max(196, min(344, len(label) * 30 + 76))
            self.button(label, (right - width, 916, width, 70),
                        state='disabled' if disabled and index == len(labels) - 1 else 'normal',
                        primary=(index == len(labels) - 1))
            right -= width + 18

    def viewport(self, box, label='园区视图', selection=False):
        x, y, width, height = box
        self.panel(box)
        self.place(self.store.background, (x + 16, y + 16, width - 32, height - 32), mode='cover', role='viewport-art')
        label_width = min(310, width - 64)
        label_height = 104 if self.draw.textlength(str(label), font=font(22)) > label_width - 48 else 54
        self.button(label, (x + 32, y + 28, label_width, label_height), primary=False)
        if selection:
            cx, cy = x + width * .52, y + height * .6
            points = [(int(cx - 90), int(cy)), (int(cx), int(cy - 48)),
                      (int(cx + 90), int(cy)), (int(cx), int(cy + 48)), (int(cx - 90), int(cy))]
            self.lines(points, color='#F3CD71', width=5, role='selection-diagram')

    def save(self, path: Path, metadata):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.convert('RGB').save(path, optimize=False, compress_level=3)
        layout_path = path.with_suffix('.layout.json')
        source_path = path.with_suffix('.source.json')
        now = datetime.now().astimezone().isoformat()
        write_json(layout_path, {'schemaVersion': 1, 'screenId': self.identity, 'title': self.title,
                                'referenceResolution': [W, H], 'origin': 'top-left',
                                'textLayers': self.texts, 'artAndControlLayers': self.widgets,
                                'dataDiagrams': self.shapes, 'layoutIssues': self.issues,
                                'fontDistribution': 'Official OFL-licensed fonts are included in assets/fonts; see records/font-sources.json.',
                                'status': 'produced_pending_review'})
        write_json(source_path, {'schemaVersion': 1, 'file': rel(path), 'sha256': digest(path),
                                'exportedAt': now, 'width': W, 'height': H, 'format': 'PNG',
                                'operation': 'composite_preview_not_native_generation',
                                'process': ['Nine-slice/contain/cover composition of painted PNG sprites',
                                            'Separate Chinese text typesetting and data diagrams'],
                                'resampling': 'LANCZOS where art is fitted; output dimensions do not represent new native generated detail.',
                                'nativeModelClaim': None, 'actualModel': None, 'actualQuality': None,
                                'modelEvidencePolicy': 'Resolve original AI model/quality through each source asset record; unreported values remain unconfirmed.',
                                'derivedFrom': list(self.used.values()), 'layoutRecord': rel(layout_path),
                                'functionalReference': metadata, 'status': 'produced_pending_review'})
        return {'screenPath': rel(path), 'layoutPath': rel(layout_path), 'sourceRecordPath': rel(source_path),
                'file': rel(path), 'layoutFile': rel(layout_path), 'sourceRecord': rel(source_path),
                'assetPaths': sorted(self.used), 'imageSha256': digest(path), 'width': W, 'height': H,
                'productionStatus': 'produced_pending_review', 'acceptanceStatus': 'pending_visual_review',
                'layoutIssues': self.issues}


def pairs(*values):
    return [{'label': label, 'value': value, 'controlKind': 'value'} for label, value in values]


def table(columns, rows):
    return {'layout': 'table', 'columns': columns, 'rows': rows}


def profile(record, tab, index=0):
    key = record['key']
    p = {'layout': record['layoutKind'], 'fields': [], 'actions': ['返回园区'], 'hint': '', 'illustration': index}
    details = next((x for x in record.get('tabDetails', []) if x['tab'] == tab), None)
    if details:
        p.update(layout=details.get('layoutKind', 'form'), fields=details.get('fields', []),
                 actions=[details.get('primaryAction', '返回园区'), '关闭'])
    if key == 'about':
        p.update(layout='document', heading='云游仙苑（暂名）',
                 paragraphs=['道家 Q 版游乐园经营美术设计。',
                             '功能研究参考 OpenRCT2；本画面为原创主题 UI。',
                             '参考代码：52a55c3e8da5 · develop',
                             'OpenRCT2 为开源 RCT2 重实现，原作者与贡献者信息保留于来源记录。' if tab == 'OpenRCT2' else
                             'RollerCoaster Tycoon 2 原作与商业资料由其权利人所有；原作资料不包含于本次美术包。'],
                 actions=['查看鸣谢', '关闭'])
    elif key == 'asset-packs':
        p.update(table(['启用', '资源包', '优先级', '状态'], [['开启', '云游仙苑 · UI 美术', '1', '已启用'],
                 ['开启', '基础对象资源包', '2', '已启用'], ['关闭', '自定义景观主题', '3', '未启用']]),
                 actions=['重新应用', '上移', '下移'], hint='上方资源包优先覆盖相同资源。')
    elif key in ('banner', 'sign'):
        p.update(layout='form', fields=pairs(('文字', '青云广场 · 欢迎光临'), ('底色', '#2F6D5A'), ('文字颜色', '#FFF8DF'),
                   ('禁止通行', '关闭')),
                 actions=['保存文字', '定位', '拆除'], illustration=7)
        if key == 'sign':
            p['fields'] = p['fields'][:3]
    elif key == 'changelog':
        p.update(layout='document', heading='制作版本与变更说明',
                 paragraphs=['本次设计版本 · 2026.10.26', '新增道家主题控件、设施经营页、编辑器与联机界面。',
                             '功能参考版本：OpenRCT2 develop / 52a55c3e8da5。',
                             '成果版本与参考游戏版本分别管理。' if tab == '更新日志' else '正式更新源与成果发布地址待项目后续确认。'],
                 actions=['返回', '关闭'])
    elif key == 'cheats':
        fields = {
            '财务': pairs(('目标现金', '500,000 铜钱'), ('当前贷款', '20,000 铜钱'), ('无金钱模式', '关闭')),
            '日期': pairs(('年份', '3'), ('月份', '6 月'), ('日期', '15 日')),
            '游客': pairs(('幸福感', '最大'), ('体力', '最大'), ('禁止乱丢垃圾', '开启'), ('禁止破坏公物', '开启')),
            '员工': pairs(('员工速度', '普通')),
            '公园': pairs(('开放公园', '开启'), ('强制园区评分', '820'), ('营销永不结束', '关闭'), ('允许暂停建设', '开启')),
            '设施': pairs(('忽略研究状态', '关闭'), ('禁用所有故障', '关闭'), ('禁用车辆限制', '关闭')),
            '天气': pairs(('天气', '晴朗'), ('冻结天气', '关闭')),
        }
        actions = {'财务': ['设置现金', '清除贷款', '返回'], '日期': ['设置日期', '重置日期', '返回'],
                   '游客': ['生成游客', '移除游客', '返回'], '员工': ['返回园区'],
                   '公园': ['拥有所有土地', '完成场景目标', '返回'],
                   '设施': ['维修全部设施', '翻新全部设施', '返回'], '天气': ['生成鸭子', '移除鸭子', '返回']}
        p.update(layout='form', fields=fields[tab], actions=actions[tab], hint='沙盒工具 · 操作会直接改变当前园区。')
    elif key == 'custom-currency':
        p.update(layout='form', fields=pairs(('Unicode 符号', '铜钱'), ('ASCII 符号', 'Q'), ('符号位置', '数值之后'),
                 ('显示汇率', '1.00'), ('预览', '12,800 铜钱')), actions=['返回设置'])
    elif key == 'debug-paint':
        p.update(layout='form', fields=pairs(('显示宽阔走道', '关闭'), ('显示受阻地块', '开启'), ('显示分段高度', '关闭'),
                 ('显示包围盒', '关闭'), ('显示无效块', '关闭'), ('稳定渲染排序', '开启'), ('强制重绘', '关闭')),
                 actions=['返回园区'], hint='绘制诊断')
    elif key in ('demolish-ride-prompt', 'refurbish-ride-prompt', 'staff-fire-prompt', 'overwrite-prompt', 'save-prompt', 'error', 'text-input', 'progress-window', 'network-status'):
        p.update(layout='dialog')
    elif key == 'editor-inventions-list':
        p.update(layout='dual-list', leftTitle='已研究 · 开始即可建造', rightTitle='未研究 · 按顺序解锁',
                 leftRows=['云游小火车', '旋转木马', '茶饮摊', '基础景观'],
                 rightRows=['游龙飞车', '竹影水道', '高空摆锤', '云海景观组'],
                 actions=['随机顺序', '全部已研究', '下一步'], hint='拖动对象可在两栏间移动并调整研究顺序。')
    elif key == 'editor-object-selection':
        names = {'设施车辆': ['木质过山车', '单轨列车', '旋转木马', '观景轮', '急流船', '碰碰车'],
                 '景观主题': ['桃林景观组', '道观建筑组', '竹林景观组', '灯笼装饰组', '山石园景组', '荷池水景组'],
                 '步道': ['青石步道', '木质步道', '排队道路', '金玉栏杆', '石桥栏杆', '木制栏杆'],
                 '入口建筑': ['山门入口', '石拱入口', '云纹入口', '园区车站', '木亭车站', '青瓦车站'],
                 '地形': ['浅灰石地', '青灰岩壁', '青草地', '细沙地', '泥土地', '清澈水面'],
                 '音乐': ['设施音乐 A', '设施音乐 B', '标题音乐', '园区音效', '钟声主题', '轻快主题'],
                 '游客员工': ['游客动画', '清洁工动画', '维修工动画', '保安动画', '表演者动画', '人物姓名集']}
        p.update(layout='catalog', names=names[tab], checked=True, actions=['查看对象', '下一步'], hint='选择对象类型与来源；勾选表示本场景可使用。')
    elif key == 'editor-scenario-options':
        p['actions'] = ['下一步', '上一步']
        p['wizard'] = True
    elif key in ('editor-status-line', 'editor-step-controller'):
        p.update(layout='editor-hud')
    elif key == 'finances':
        if tab == '收支':
            p.update(table(['收支项目', '本月', '上月', '累计'],
                 [['设施门票', '+24,600', '+22,800', '+184,200'], ['商店与餐饮', '+7,800', '+6,400', '+52,400'],
                  ['员工工资', '−3,200', '−3,040', '−24,800'], ['建设与维护', '−16,400', '−14,600', '−92,600'],
                  ['研究与利息', '−2,000', '−2,000', '−15,600']]),
                 summary=[('现金', '128,400'), ('贷款', '20,000'), ('本月净额', '+10,800')], actions=['调整贷款', '关闭'])
        elif tab in ('现金', '公园价值', '周利润'):
            p.update(layout='chart', chart=tab, actions=['返回收支', '关闭'])
        elif tab == '营销':
            p.update(table(['活动', '目标', '剩余周期', '费用 / 周'],
                 [['设施宣传', '游龙飞车', '2 周', '500 铜钱'], ['入园优惠', '全园游客', '1 周', '300 铜钱']]),
                 summary=[('进行中', '2 项'), ('本周投入', '800'), ('可用方案', '6 类')], actions=['新建营销', '关闭'])
        else:
            p.update(layout='research', fields=pairs(('研究经费', '最高'), ('月度费用', '400 铜钱'), ('当前阶段', '设计中')),
                     actions=['查看研究进度', '关闭'])
    elif key == 'footpath':
        p.update(layout='tool', fields=pairs(('道路类型', '排队道路' if tab == '区域' else '普通步道'),
                 ('路面', '青石铺地'), ('栏杆', '金玉栏杆'), ('朝向', '东北'),
                 ('坡度', '上坡' if tab == '桥梁隧道' else '平地'), ('预估费用', '120 铜钱')),
                 actions=['建造此段', '移除'], toolLabel='铺设步道', hint='普通路连接园区，排队路连接设施入口。')
    elif key == 'guest':
        if tab == '需求':
            p['layout'] = 'needs'
        elif tab in ('游玩记录', '消费', '想法', '携带物', '调试'):
            datasets = {
                '游玩记录': table(['设施', '乘坐次数', '最近体验'], [['旋转木马', '2', '很开心'], ['游龙飞车', '1', '非常刺激'], ['竹影水道', '1', '风景很好']]),
                '消费': table(['支出项目', '金额', '累计'], [['入园门票', '50 铜钱', '50 铜钱'], ['设施门票', '80 铜钱', '130 铜钱'], ['餐饮商品', '28 铜钱', '158 铜钱']]),
                '想法': table(['最近想法', '状态', '时间'], [['这里的风景真不错！', '积极', '刚刚'], ['想找一杯清茶。', '口渴', '3 分钟前'], ['游龙飞车很好玩！', '满意', '8 分钟前']]),
                '携带物': table(['携带物', '数量', '说明'], [['园区地图', '1', '游园导览'], ['青梅茶', '1', '已购买饮品'], ['纪念气球', '1', '游园纪念品']]),
                '调试': {'layout': 'form', 'fields': pairs(('实体编号', '128'), ('目标设施', '游龙飞车'), ('当前位置', '64, 72'), ('寻路状态', '行进中'))}}
            p.update(datasets[tab])
        else:
            p['layout'] = 'person'
        p['person'] = 'guest'
        p['actions'] = ['定位游客', '追踪', '关闭']
    elif key == 'guest-list':
        p.update(table(['游客 / 群体', '当前行动' if tab == '个体' else '共同想法', '人数' if tab == '汇总' else '幸福感', '位置'],
                 [['云游客 128' if tab == '个体' else '排队游客', '前往游龙飞车' if tab == '个体' else '期待乘坐', '82%' if tab == '个体' else '126', '青云广场'],
                  ['云游客 241' if tab == '个体' else '寻找餐饮', '购买清茶' if tab == '个体' else '有些口渴', '76%' if tab == '个体' else '48', '茶饮长廊'],
                  ['云游客 369' if tab == '个体' else '休息游客', '欣赏景观' if tab == '个体' else '风景真好', '94%' if tab == '个体' else '72', '桃林步道']]),
                 actions=['定位所选', '追踪名单', '关闭'], hint='搜索姓名或按行为、想法筛选。')
    elif key in ('install-track', 'track-list'):
        if key == 'track-list' and tab == '设计列表':
            p.update(table(['轨道设计', '类型', '长度', '预计费用'], [['云龙环山', '钢制过山车', '1,240 米', '24,600'],
                    ['竹影疾行', '木质过山车', '860 米', '18,200'], ['飞云穿谷', '悬挂过山车', '1,080 米', '22,400']]),
                     actions=['查看设计', '从零建造', '关闭'])
        else:
            p.update(layout='viewport', fields=pairs(('设计名', '云龙环山'), ('轨道类型', '钢制过山车'), ('长度', '1,240 米'),
                     ('刺激度', '6.80 · 高'), ('强度', '5.20 · 中'), ('预计费用', '24,600 铜钱')),
                     actions=['安装设计' if key == 'install-track' else '放置设计', '返回'], illustration=0)
    elif key == 'land':
        p.update(layout='tool', fields=pairs(('笔刷尺寸', '3 × 3'), ('山地模式', '开启' if tab == '整形' else '关闭'),
                 ('地表材质', '自然青灰石'), ('崖面材质', '浅灰岩壁'), ('操作', '升高地形' if tab == '整形' else '涂绘地表'), ('预估费用', '180 铜钱')),
                 actions=['应用工具', '返回'], toolLabel='整修地形')
    elif key == 'land-rights':
        p.update(layout='tool', fields=pairs(('购买类型', tab), ('选择范围', '3 × 3'), ('可售地块', '9'),
                 ('单格价格', '90 铜钱'), ('合计费用', '810 铜钱')), actions=['购买所选权利', '取消'], toolLabel=tab)
    elif key == 'load-save':
        p.update(layout='files', columns=['文件名', '类型', '大小', '修改日期'],
                 rows=[['青云初试', '公园存档' if tab in ('读取', '保存') else tab, '2.8 MB', '2026.10.26'],
                       ['桃源乐园', '公园存档' if tab in ('读取', '保存') else tab, '3.4 MB', '2026.10.25'],
                       ['云海奇游', '公园存档' if tab in ('读取', '保存') else tab, '4.1 MB', '2026.10.24']],
                 actions=['保存文件' if tab == '保存' else '打开所选', '浏览目录', '返回'], hint='公园 / 本地文件')
    elif key in ('main', 'viewport', 'game-status-bar', 'park-info-panel', 'news-ticker', 'date-info-panel', 'top-toolbar', 'title-exit', 'title-logo', 'title-options', 'title-version', 'chat'):
        p.update(layout='hud')
    elif key == 'map':
        p.update(layout='map', fields=pairs(('图层', '游客分布' if tab == '游客' else '设施分布'), ('视图缩放', '1 : 2'),
                 ('园区面积', '128 × 128'), ('选中位置', '64, 72')),
                 actions=['定位所选位置', '关闭'], hint='青云园区 · 分布示意')
    elif key == 'map-gen':
        p['actions'] = ['生成地图', '返回编辑器']
        p['wizard'] = True
    elif key in ('map-tooltip', 'tooltip', 'dropdown'):
        p.update(layout='popup')
    elif key == 'maze-construction':
        p.update(layout='tool', fields=pairs(('模式', tab), ('方向', '东北'), ('选中高度', '8 米'),
                 ('入口', '已建造'), ('出口', '待建造'), ('预估费用', '40 铜钱')),
                 actions=['确认' + tab, '建造出口', '返回'], toolLabel='迷宫' + tab)
    elif key == 'multiplayer':
        if tab == '玩家':
            p.update(table(['玩家', '权限组', '最近操作', '延迟'], [['青云', '园主', '建造轨道', '32 ms'], ['清风', '建设者', '铺设道路', '46 ms'],
                    ['明月', '建设者', '布置景观', '58 ms'], ['竹影', '访客', '查看园区', '40 ms']]), actions=['查看玩家', '关闭'])
        elif tab == '权限组':
            p.update(layout='permissions', fields=pairs(('当前权限组', '建设者'), ('默认权限组', '访客')),
                     actions=['新增权限组', '删除权限组', '关闭'])
        elif tab == '选项':
            p.update(layout='form', fields=pairs(('记录服务器操作', '开启'), ('记录聊天', '开启'), ('仅允许已知密钥', '关闭'),
                     ('公开服务器', '开启')), actions=['返回园区'])
        else:
            p['layout'] = 'document'
            p['heading'] = '青云同游 · 合作建园'
            p['paragraphs'] = ['服务器：青云同游（示例）', '欢迎一起经营这座仙山游乐园。', '在线人数：8 / 16',
                               '参考网络版本：develop', '建设与管理操作由服务器权限组控制。']
            p['actions'] = ['复制地址', '关闭']
    elif key == 'new-campaign':
        p.update(layout='form', fields=pairs(('活动类型', '设施宣传'), ('推广设施', '游龙飞车'), ('持续时间', '4 周'),
                 ('每周费用', '500 铜钱'), ('费用合计', '2,000 铜钱')), actions=['开始营销活动', '取消'], illustration=10)
    elif key == 'new-ride':
        names = {'交通': ['云游小火车', '山间单轨', '观景索道', '悬挂单轨', '观景升降台', '环园列车'],
                 '温和': ['旋转木马', '观景轮', '迷你汽车', '观光塔', '小型轨道车', '休闲游船'],
                 '过山车': ['木质过山车', '钢制过山车', '悬挂过山车', '倒挂过山车', '矿山过山车', '发射过山车'],
                 '惊险': ['高空摆锤', '自由落体', '旋转飞椅', '摇摆船', '旋转平台', '高空飞行'],
                 '水上': ['竹影水道', '急流漂流', '激流勇进', '回旋水道', '游船码头', '山泉水车'],
                 '商店摊位': ['丹茶铺', '点心摊', '纪念品店', '咨询处', '洗手间', '自动提款机'],
                 '研发': ['交通研究', '温和设施研究', '过山车研究', '水上研究', '商店研究', '景观研究']}
        p.update(layout='catalog', names=names[tab], actions=['选择设施' if tab != '研发' else '研究经费', '返回'],
                 hint='按名称搜索 · 选择既有蓝图或自定义建造')
    elif key == 'news':
        if tab == '通知设置':
            p.update(layout='form', fields=pairs(('设施故障通知', '开启'), ('研究完成通知', '开启'), ('园区奖项通知', '开启'),
                    ('经营提醒', '开启'), ('游客追踪消息', '关闭')), actions=['返回消息'])
        else:
            p.update(table(['消息', '分类', '日期', '操作'], [['游龙飞车需要维修', '设施', '6 月 15 日', '定位'],
                    ['竹影水道研究完成', '研究', '6 月 14 日', '查看'], ['园区获得整洁奖项', '园区', '6 月 13 日', '查看']]),
                     actions=['定位消息对象', '查看历史', '关闭'])
    elif key == 'object-load-error':
        if tab == '下载中':
            p.update(layout='progress', heading='正在下载对象', message='云海景观组 · 已完成 8 / 12 个对象',
                     actions=['取消下载', '查看清单'])
        else:
            p.update(table(['对象名称', '来源', '类型', '状态'], [['cloud_garden', '自定义资源', '景观组', '缺失' if tab == '缺失对象' else '下载失败'],
                    ['jade_station', '自定义资源', '车站', '缺失'], ['tea_shop', '自定义资源', '商店', '缺失']]),
                     actions=['下载全部', '复制清单', '返回'], hint='取得所需对象后再次读取文件。')
    elif key == 'options':
        p['layout'] = 'form'
        p['actions'] = ['快捷键设置', '返回游戏'] if tab == '操作' else ['返回游戏']
        p['hint'] = '设置调整后即时保存。'
    elif key == 'park':
        if tab in ('评分', '游客'):
            p.update(layout='chart', chart='园区评分' if tab == '评分' else '游客人数', actions=['返回入口', '关闭'])
        elif tab == '目标':
            p.update(layout='objective', fields=pairs(('场景目标', '游客人数与园区评分'), ('游客人数', '1,280 / 1,500'),
                     ('园区评分', '820 / 600'), ('截止日期', '第 3 年 10 月')), actions=['继续经营', '关闭'])
        elif tab == '奖项':
            p.update(layout='catalog', names=['整洁园区', '优美景观', '服务周到', '热闹园区', '设施丰富', '游客满意'],
                     actions=['返回入口', '关闭'], hint='园区奖项 · 表现记录')
        elif tab in ('入口', '统计'):
            p['layout'] = 'viewport' if tab == '入口' else 'form'
    elif key == 'patrol-area':
        p.update(layout='tool', fields=pairs(('员工', '清风'), ('岗位', '维修工'), ('当前模式', tab), ('显示同类巡逻区', '开启'),
                 ('已选范围', '东侧设施区')), actions=['完成巡逻区', '清除范围', '取消'], toolLabel='员工巡逻区 · ' + tab)
    elif key == 'player':
        p.update(layout='person' if tab == '概览' else 'form', fields=pairs(('玩家', '清风'), ('权限组', '建设者'), ('最近操作', '铺设道路'),
                 ('操作次数', '142'), ('园区花费', '12,400 铜钱')), actions=['定位最近操作', '调整权限组', '关闭'], person='player')
    elif key == 'research':
        p.update(layout='research', fields=pairs(('当前项目', '竹影水道'), ('研究阶段', '设计中'), ('预计完成', '6 月 22 日'),
                 ('研究经费', '最高' if tab == '经费' else '普通'), ('月度费用', '400 铜钱')),
                 actions=['返回园区'], hint='新项目完成后自动解锁。')
    elif key == 'ride':
        if tab in ('概览',):
            p['layout'] = 'viewport'
        elif tab == '图表':
            p.update(layout='chart', chart='速度', actions=['开始试车', '关闭'])
        elif tab == '测试':
            p.update(layout='ratings', fields=pairs(('刺激度', '6.80 · 高'), ('强度', '5.20 · 中'), ('眩晕度', '2.40 · 低'),
                     ('最高速度', '82 千米 / 时'), ('平均速度', '46 千米 / 时'), ('轨道长度', '1,240 米')),
                     actions=['开始试车', '查看图表', '关闭'])
        elif tab == '游客':
            p.update(table(['指标', '本期', '累计'], [['本小时顾客', '142 人', '1,284 人'], ['排队人数', '126 人', '—'],
                    ['等待时间', '18 分钟', '—'], ['满意度', '92%', '89%']]), actions=['查看排队游客', '关闭'])
        elif tab == '配色':
            p['fields'] = pairs(('轨道主色', '#26745A'), ('轨道辅色', '#D9BD75'), ('支撑颜色', '#B2B5A6'), ('车辆颜色', '#8DAE7A'))
        p['hint'] = '游龙飞车 · 钢制过山车（示例）'
    elif key == 'ride-construction':
        p.update(layout='tool', fields=pairs(('建设部件', tab), ('方向', '东北'), ('曲线', '右弯 · 中半径'), ('坡度', '缓上坡'),
                 ('链条提升', '开启' if tab == '轨道' else '关闭'), ('预估费用', '240 铜钱')),
                 actions=['建造此段', '移除上一段', '模拟'], toolLabel='游龙飞车 · ' + tab,
                 hint='入口连接排队道路，出口连接普通步道。')
    elif key == 'ride-list':
        lists = {'游乐设施': [['游龙飞车', '营业中', '126', '+4,600'], ['旋转木马', '营业中', '34', '+1,280'], ['竹影水道', '试车中', '0', '—']],
                 '商店摊位': [['丹茶铺', '营业中', '16', '+860'], ['点心摊', '营业中', '9', '+620'], ['纪念品店', '已关闭', '0', '—']],
                 '服务设施': [['咨询处', '营业中', '4', '+120'], ['洗手间', '营业中', '3', '+80'], ['自动提款机', '营业中', '2', '—']]}
        p.update(table(['名称', '状态', '排队 / 顾客', '本小时利润'], lists[tab]), actions=['查看设施', '全部开放', '全部关闭'])
    elif key == 'scenario-select':
        p.update(layout='scenarios', names=['青云初试', '桃源乐园', '云海奇游', '竹影山谷', '仙山游园', '水云长廊'],
                 actions=['开始经营', '返回主菜单'], hint=tab + ' · 场景名称为本项目排版示例')
    elif key == 'scenery':
        p.update(layout='catalog', names=['桃花树', '青竹', '云纹石灯', '太极山石', '荷池装饰', '玉色栏杆'],
                 actions=['选择景物', '重涂工具', '返回'], hint='搜索景观 · 旋转与配色')
    elif key == 'scenery-scatter':
        p.update(layout='tool', fields=pairs(('笔刷范围', '5 × 5'), ('散布密度', '中等'), ('随机朝向', '开启'),
                 ('景观对象', '桃花树'), ('预估数量', '12 棵')), actions=['应用散布', '取消'], toolLabel='散布景观')
    elif key == 'server-list':
        if tab == '直接连接':
            p.update(layout='form', fields=pairs(('玩家名', '清风'), ('服务器地址', '127.0.0.1'), ('端口', '11753')),
                     actions=['连接服务器', '返回列表'], illustration=11)
        else:
            p.update(table(['服务器', '玩家', '版本', '访问'], [['青云同游', '8 / 16', '兼容', '密码'], ['桃源共建', '5 / 12', '兼容', '公开'],
                    ['云海协作', '12 / 16', '版本不同', '公开']]), actions=['加入服务器', '刷新列表', '创建服务器'], hint='玩家名：清风')
    elif key == 'server-start':
        p.update(layout='form', fields=pairs(('服务器名称', '青云同游'), ('说明', '合作经营，同建乐园'), ('欢迎语', '欢迎来到青云同游'),
                 ('端口', '11753'), ('人数上限', '16'), ('服务器密码', '••••••••'), ('公开广播', '开启')),
                 actions=['读取存档开服' if tab == '读档' else '选择场景开服', '取消'])
    elif key == 'shortcut-keys':
        p.update(table(['操作', '当前按键', '分类'], [['暂停 / 继续', 'Pause', '时间'], ['加快速度', '+', '时间'],
                    ['缩放视图', 'Page Up / Down', '视图'], ['旋转园区', 'Enter', '视图'], ['打开设施目录', 'F3', '经营']]),
                 actions=['修改快捷键', '清除绑定', '恢复默认'], hint='选择操作后按下新的组合键。')
    elif key == 'staff':
        if tab == '概览':
            p['layout'] = 'person'
            p['person'] = 'staff'
            p['actions'] = ['设置巡逻区', '定位员工', '关闭']
        elif tab == '职责':
            p['hint'] = '岗位：维修工 · 可用职责随岗位变化。'
            p['actions'] = ['返回员工']
        else:
            p['layout'] = 'form'
    elif key == 'staff-list':
        job = {'清洁': '清洁工', '维修': '维修工', '安保': '保安', '演员': '表演者'}[tab]
        p.update(table(['姓名', '岗位', '当前工作', '巡逻区'], [['清风', job, {'清洁': '清扫步道', '维修': '检查设施', '安保': '巡逻中', '演员': '表演中'}[tab], '东区'],
                    ['明月', job, '巡逻中', '西区'], ['竹影', job, '前往工作地点', '全园']]),
                 summary=[('此类员工', '3 人'), ('月度工资', '240 铜钱'), ('制服颜色', '玉绿')],
                 actions=['雇佣' + job, '查看员工', '巡逻范围'])
    elif key == 'themes':
        p.update(layout='form', fields=pairs(('当前主题', '云游仙苑 · 玉绿'), ('当前类别', tab), ('主色', '#2F6D5A'),
                 ('次色', '#F5EEDC'), ('边饰色', '#B28C43'), ('透明效果', '关闭')),
                 actions=['复制主题', '重命名', '返回设置'])
    elif key == 'tile-inspector':
        p.update(layout='inspector', fields=pairs(('地块坐标', '64, 72'), ('选中元素', tab), ('基础高度', '8'), ('清除高度', '12'), ('方向', '东北')),
                 actions=['复制元素', '上移元素', '关闭'], hint='高级检查器 · 当前地块')
    elif key == 'title-menu':
        p.update(layout='menu')
    elif key == 'track-design-manage':
        if tab == '删除确认':
            p['layout'] = 'dialog'
        else:
            p.update(table(['设计名称', '类型', '文件状态'], [['云龙环山', '钢制过山车', '可用'], ['竹影疾行', '木质过山车', '可用'],
                        ['飞云穿谷', '悬挂过山车', '可用']]), actions=['重命名', '删除设计', '关闭'])
    elif key == 'track-design-place':
        p.update(layout='tool', fields=pairs(('设计', '云龙环山'), ('方向', '东北'), ('镜像', '关闭'), ('包含景观', '开启'),
                 ('建造费用', '24,600 铜钱')), actions=['确认放置', '旋转', '取消'], toolLabel='放置轨道蓝图')
    elif key == 'transparency':
        p.update(layout='form', fields=pairs(('游乐设施', '显示'), ('景观与建筑', '半透明'), ('步道', '显示'), ('支撑', '隐藏'),
                 ('人物', '显示'), ('地下视图', '关闭')), actions=['返回园区'])
    elif key == 'view-clipping':
        p.update(layout='tool', fields=pairs(('裁切方式', tab), ('启用裁切', '开启'), ('可见高度', '24 米'),
                 ('裁切区域', '32, 32 — 96, 96'), ('显示选区', '开启')),
                 actions=['重置范围', '返回园区'], toolLabel='视图裁切')
    elif key == 'water':
        p.update(layout='tool', fields=pairs(('笔刷尺寸', '3 × 3'), ('当前水位', '8 米'), ('调整方向', '升高水位'),
                 ('目标水位', '10 米'), ('预估费用', '120 铜钱')), actions=['调整水位', '返回'], toolLabel='整修水域')
    elif key == 'console':
        p.update(layout='console')
    elif key == 'plugin-window':
        p.update(layout='form', fields=pairs(('插件名称', '自定义园区工具（示例）'), ('当前页面', '园区信息'),
                 ('文字输入', '示例输入'), ('选项', '开启'), ('列表筛选', '全部')), actions=['执行所选操作', '关闭'],
                 hint='插件窗口的内容由已安装插件定义。')
    if not p.get('fields') and p['layout'] == 'form':
        p['fields'] = pairs(*[(f, '可调整') for f in record['features'][:6]])
    return p


def render_table(c, box, columns, rows, row_height=70):
    x, y, width, height = box
    col_count = len(columns)
    weights = [1.45] + [1] * (col_count - 1)
    unit = (width - 64) / sum(weights)
    widths = [v * unit for v in weights]
    c.panel((x, y, width, min(height, row_height * (len(rows) + 1) + 20)))
    cx = x + 48
    for label, cw in zip(columns, widths):
        c.text(label, (cx, y + 24, cw - 24, 42), 25, family='bold', color=JADE)
        cx += cw
    c.lines([(x + 20, y + row_height - 5), (x + width - 20, y + row_height - 5)], width=2)
    for ri, row in enumerate(rows):
        if (ri + 2) * row_height > height:
            break
        cy = y + row_height * (ri + 1)
        cx = x + 48
        for ci, (value, cw) in enumerate(zip(row, widths)):
            color = GREEN if str(value).startswith('+') or value in ('已启用', '兼容', '营业中') else RED if str(value).startswith('−') or value in ('缺失', '下载失败', '版本不同') else DEEP
            c.text(value, (cx, cy + 10, cw - 24, row_height - 14), 24, color=color, valign='center')
            cx += cw
        if ri < len(rows) - 1:
            c.lines([(x + 22, cy + row_height - 2), (x + width - 22, cy + row_height - 2)], width=1)


def render_chart(c, box, title):
    x, y, width, height = box
    c.panel(box)
    c.text(title + '趋势', (x + 30, y + 20, width - 60, 50), 30, family='title')
    plot_x, plot_y, plot_w, plot_h = x + 125, y + 105, width - 195, height - 170
    if title == '园区评分':
        values, maximum, unit, labels = [520, 566, 602, 585, 642, 680, 710, 702, 760, 788, 804, 820], 1000, '评分', ['1月', '3月', '5月', '7月', '9月', '11月']
    elif title == '游客人数':
        values, maximum, unit, labels = [320, 410, 560, 620, 680, 790, 880, 960, 1050, 1160, 1210, 1280], 1500, '人', ['1月', '3月', '5月', '7月', '9月', '11月']
    elif title == '速度':
        values, maximum, unit, labels = [0, 18, 32, 72, 82, 56, 72, 44, 64, 30, 12, 0], 100, '千米/时', ['0秒', '20秒', '40秒', '60秒', '80秒', '100秒']
    elif title == '周利润':
        values, maximum, unit, labels = [2400, 3500, 2800, 4200, 4800, 5300, 4600, 5800, 6200, 7200, 6800, 7600], 10000, '铜钱', ['1周', '3周', '5周', '7周', '9周', '11周']
    elif title == '公园价值':
        values, maximum, unit, labels = [82, 96, 105, 118, 126, 144, 156, 168, 184, 206, 221, 240], 300, '千铜钱', ['1月', '3月', '5月', '7月', '9月', '11月']
    else:
        values, maximum, unit, labels = [48, 56, 52, 69, 72, 84, 81, 92, 108, 116, 122, 128.4], 150, '千铜钱', ['1月', '3月', '5月', '7月', '9月', '11月']
    c.text(unit, (x + 24, y + 74, 100, 36), 22, color=MUTED)
    for tick in range(5):
        ty = plot_y + plot_h - tick * plot_h / 4
        c.lines([(int(plot_x), int(ty)), (int(plot_x + plot_w), int(ty))], color='#D1C6A5', width=1, role='chart-grid')
        c.text(str(int(maximum * tick / 4)), (x + 22, ty - 15, 88, 34), 22, color=MUTED, align='right')
    c.lines([(int(plot_x), int(plot_y)), (int(plot_x), int(plot_y + plot_h)), (int(plot_x + plot_w), int(plot_y + plot_h))], color=GOLD, width=2, role='chart-axis')
    for ti, label in enumerate(labels):
        tx = plot_x + ti * plot_w / 5
        c.text(label, (tx - 42, plot_y + plot_h + 14, 84, 32), 22, color=MUTED, align='center')
    points = [(int(plot_x + i * plot_w / (len(values) - 1)), int(plot_y + plot_h * (1 - value / maximum))) for i, value in enumerate(values)]
    c.lines(points, color=GREEN, width=5, role='chart-series-example-data')
    for px, py in points:
        c.draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=GREEN)


def render_fields(c, box, fields, illustration=True, illustration_index=0):
    x, y, width, height = box
    if illustration:
        form_w = int(width * .66)
        art_x = x + form_w + 40
        c.illustration(illustration_index, (art_x, y + 35, width - form_w - 45, min(height - 65, 410)), 'mountain_scenario')
    else:
        form_w = width
    gap = min(74, max(58, int((height - 18) / max(1, len(fields)))))
    if len(fields) > 7:
        columns = 2
        fw = int((form_w - 36) / 2)
        for i, item in enumerate(fields):
            c.field(item['label'], item['value'], (x + i % columns * (fw + 36), y + i // columns * 76, fw, 58), item.get('controlKind'))
    else:
        for i, item in enumerate(fields):
            c.field(item['label'], item['value'], (x + 10, y + i * gap, form_w - 20, 56), item.get('controlKind'))


def catalog_art(record, name, index):
    key = record['key']
    if key == 'park':
        return ('illustration', 'achievement_trophy')
    if key == 'new-ride':
        if '研究' in name:
            return ('icon', 'research')
        for token, asset in [('悬挂单轨', 'suspended_monorail'), ('单轨', 'monorail'), ('索道', 'cable_car'),
                             ('升降', 'observation_lift'), ('摇摆船', 'swinging_ship'), ('点心', 'dumpling_kiosk'),
                             ('丹茶', 'tea_kiosk'), ('洗手', 'toilet_pavilion'), ('急救', 'first_aid_pavilion')]:
            if token in name:
                return ('illustration', asset)
        for token, asset in [('火车', 'cloud_train'), ('列车', 'cloud_train'), ('单轨', 'cloud_train'), ('交通', 'cloud_train'),
                             ('过山车', 'dragon_coaster'), ('木马', 'gourd_carousel'), ('观景轮', 'celestial_wheel'),
                             ('水道', 'bamboo_flume'), ('漂流', 'bamboo_flume'), ('激流', 'bamboo_flume'),
                             ('茶', 'tea_keeper')]:
            if token in name:
                return ('illustration', asset)
        for token, asset in [('索道', 'miniature_train'), ('汽车', 'track_blueprint'), ('轨道车', 'track_blueprint'),
                             ('观光', 'ferris_wheel'), ('游船', 'water_flume'), ('水车', 'water_flume'), ('码头', 'water_flume'),
                             ('摆锤', 'pirate_ship'), ('摇摆', 'pirate_ship'), ('飞椅', 'carousel'), ('旋转', 'carousel'),
                             ('落体', 'ferris_wheel'), ('飞行', 'ferris_wheel'), ('点心', 'dumpling_shop'),
                             ('纪念品', 'souvenir_shop'), ('咨询', 'information'), ('洗手', 'toilet'), ('提款', 'cash_machine')]:
            if token in name:
                return ('icon', asset)
        return ('icon', 'research' if '研究' in name else 'track_blueprint')
    if key == 'scenery':
        subject = ['peach_flowers', 'pine_tree', 'lantern', 'mountain', 'water', 'bench'][index % 6]
        return ('icon', subject)
    if key == 'editor-object-selection':
        for token, asset in [('过山车', 'roller_coaster'), ('列车', 'miniature_train'), ('木马', 'carousel'), ('观景轮', 'ferris_wheel'),
                             ('船', 'water_flume'), ('车', 'track_blueprint'), ('景观', 'peach_flowers'), ('道观', 'park_gate'),
                             ('竹', 'pine_tree'), ('灯笼', 'lantern'), ('山石', 'mountain'), ('水景', 'water'), ('水面', 'water'),
                             ('排队', 'queue'), ('步道', 'path'), ('栏杆', 'bench'), ('入口', 'park_gate'), ('车站', 'miniature_train'),
                             ('岩', 'mountain'), ('地', 'mountain'), ('音乐', 'settings'), ('音效', 'settings'), ('钟声', 'settings'),
                             ('主题', 'settings'), ('清洁', 'cleaner'), ('维修', 'mechanic'), ('保安', 'security'),
                             ('表演', 'entertainer'), ('游客', 'visitor'), ('姓名', 'visitor')]:
            if token in name:
                return ('icon', asset)
    return ('icon', 'information')


def render_catalog(c, box, p, record):
    x, y, width, height = box
    names = p.get('names', ['设施', '景观', '服务', '道路', '研究', '园区'])
    gap = 18
    card_w = int((width - gap * 2) / 3)
    card_h = int((height - gap) / 2)
    for i, name in enumerate(names[:6]):
        bx, by = x + i % 3 * (card_w + gap), y + i // 3 * (card_h + gap)
        c.panel((bx, by, card_w, card_h))
        art_type, art_subject = catalog_art(record, name, i)
        if art_type == 'illustration':
            c.illustration(0, (bx + 25, by + 40, 142, card_h - 70), art_subject)
        else:
            c.icon(0, (bx + 30, by + 48, 132, card_h - 86), art_subject)
        c.text(name, (bx + 178, by + 28, card_w - 197, 72), 28, family='title', minimum=24)
        if p.get('checked'):
            c.checkbox('已选择' if i < 4 else '可选择', (bx + 178, by + 116, card_w - 190, 52), i < 4)
        else:
            status = ('已获得' if i < 2 else '尚未获得') if record['key'] == 'park' else '已解锁' if i < 5 else '研究中'
            c.text(status, (bx + 178, by + 108, card_w - 197, 42), 23, color=GREEN if status in ('已获得', '已解锁') else MUTED)
            if card_h > 205 and record['key'] != 'park':
                c.text(f'{[1200, 2400, 3800, 5200, 6800, 8400][i]:,} 铜钱' if '研究' not in name else '查看研究进度',
                       (bx + 178, by + 154, card_w - 197, 38), 22, color=MUTED)


def render_hud(c, record, tab, index=0):
    c.place('toolbar', (24, 18, 1872, 108), mode='nine', role='main-toolbar')
    c.text('云游仙苑', (48, 32, 240, 52), 33, family='title', color=CREAM)
    c.text('暂名 · 经营园区', (49, 81, 240, 30), 20, color=CREAM, minimum=20)
    items = [('暂停', 0), ('加速', 1), ('文件', 2), ('视图', 3), ('地形', 4), ('步道', 5), ('设施', 6), ('景观', 7), ('游客', 8), ('员工', 9), ('财务', 10), ('研究', 11), ('消息', 12), ('联机', 13)]
    for i, (label, icon_id) in enumerate(items):
        bx = 318 + i * 109
        c.icon(icon_id, (bx + 24, 25, 52, 52))
        c.text(label, (bx + 6, 79, 90, 32), 22, color=CREAM, align='center')
    c.place('toolbar', (24, 974, 1872, 82), mode='nine', role='status-toolbar')
    values = [('现金', '128,400 铜钱'), ('游客', '1,280 人'), ('评分', '820 / 999'), ('日期', '第 3 年 · 6 月 15 日'), ('天气', '晴朗 · 24°C')]
    for i, (label, value) in enumerate(values):
        bx = 66 + i * 366
        c.text(label, (bx, 991, 92, 34), 22, color=CREAM)
        c.text(value, (bx + 82, 989, 275, 40), 25, color=CREAM)
    key = record['key']
    if key == 'main' and tab == '暂停':
        c.button('园区已暂停', (766, 156, 388, 82), primary=True)
    elif key == 'viewport':
        c.viewport((1140, 180, 700, 450), '辅助视口')
        c.button('同步主视口位置', (1450, 650, 346, 70), primary=False)
    elif key == 'date-info-panel':
        c.panel((1300, 736, 540, 204))
        c.text('日期与天气', (1332, 757, 470, 44), 30, family='title')
        c.text('第 3 年 · 6 月 15 日\n晴朗   24°C', (1334, 815, 470, 110), 26)
        c.icon(35, (1700, 806, 108, 108))
    elif key == 'park-info-panel':
        c.panel((60, 730, 670, 208))
        c.text('青云园区 · 营业中', (90, 752, 580, 48), 30, family='title')
        c.text('园区价值 240,000 铜钱\n游客满意度 89%    开放设施 18 / 21', (92, 820, 570, 100), 25)
    elif key == 'news-ticker':
        c.panel((470, 850, 980, 88))
        c.icon(12, (494, 864, 58, 58))
        c.text('竹影水道研究完成，已可建造。', (568, 874, 660, 48), 27)
        c.button('查看', (1232, 866, 188, 58), primary=False)
    elif key == 'chat':
        c.panel((65, 540, 930, 398))
        c.text('同游频道', (100, 562, 650, 46), 32, family='title')
        c.text('青云：我来负责轨道建设。\n清风：东侧步道已经接通。\n明月：茶饮铺附近补几棵桃花树吧。',
               (102, 628, 835, 182), 26)
        c.panel((96, 830, 670, 68))
        c.text('一起把园区经营好吧！', (114, 844, 626, 44), 25)
        c.button('发送', (788, 832, 172, 66))
    elif key in ('title-exit', 'title-logo', 'title-options', 'title-version'):
        render_menu(c, {'key': 'title-menu'}, '主菜单')
        if key == 'title-options':
            c.panel((1370, 180, 450, 300))
            for i, label in enumerate(['游戏设置', '关于', '更新日志']):
                c.button(label, (1400, 204 + i * 84, 390, 68), primary=False)
    elif key == 'top-toolbar':
        menus = {'文件': ['保存园区', '读取园区', '新游戏', '截图', '返回主菜单'],
                 '视图': ['缩放视图', '旋转园区', '园区地图', '透明与隐藏', '视图裁切'],
                 '多人': ['玩家与权限', '服务器信息', '同游聊天', '断开连接'],
                 '调试': ['沙盒与作弊', '地块检查器', '绘制诊断', '控制台']}
        c.panel((320, 144, 500, len(menus[tab]) * 74 + 36))
        for i, label in enumerate(menus[tab]):
            c.button(label, (345, 164 + i * 74, 450, 60), primary=False)
    c.footer()


def render_menu(c, record, tab):
    c.title_plaque('云游仙苑', '暂名 · 道家游园经营')
    if tab == '工具箱':
        labels = ['场景编辑器', '存档转场景', '过山车设计器', '轨道设计管理', '打开内容目录', '返回']
    else:
        labels = ['开始新场景', '继续游园', '多人同游', '工具箱', '游戏设置', '退出游戏']
    c.panel((1260, 238, 550, 695), 'panel_main')
    for i, label in enumerate(labels):
        c.button(label, (1320, 284 + i * 96, 430, 74), primary=(i == 0))
    c.text('一园山水，万般欢喜。', (92, 834, 1050, 76), 51, color=CREAM, family='title')
    c.text('以建造与经营，留住每一位游客的笑容。', (96, 916, 1100, 44), 26, color=CREAM)
    c.text('美术设计版本 2026.10.26 · 功能参考 OpenRCT2', (65, 1017, 1120, 38), 22, color=CREAM)
    c.footer()


def render_tool(c, record, tab, p):
    render_hud(c, {'key': 'main'}, '运行')
    c.panel((1290, 164, 558, 762), 'panel_card')
    c.text(p.get('toolLabel', record['title']), (1350, 220, 438, 78), 34, family='title', minimum=28)
    c.place('close', (1782, 180, 50, 50), role='close')
    fields = p.get('fields', [])[:6]
    field_y = 318
    for item in fields:
        value = str(item['value'])
        kind = item.get('controlKind')
        long_value = (kind not in ('toggle','slider','color') and value not in ('开启','关闭','已开启','已关闭')
                      and c.draw.textlength(value, font=font(22)) > 156)
        if long_value:
            # Preserve the entire value on a full-width second line in narrow docks.
            c.text(item['label'], (1355, field_y, 428, 34), 22, color=MUTED)
            c.place('secondary_normal', (1350, field_y + 34, 438, 48), mode='nine', role='input-field')
            c.text(value, (1390, field_y + 40, 358, 36), 22, valign='center')
            field_y += 90
        else:
            c.field(item['label'], value, (1350, field_y, 438, 56), kind)
            field_y += 72
    c.button(p.get('actions', ['应用工具'])[0], (1330, 817, 470, 70))
    c.panel((70, 152, 940, 112))
    c.text(p.get('hint') or '选择位置查看预览，确认后应用。', (125, 180, 820, 72), 27, minimum=24)
    # A selection guide is data overlay over the painted park; it is not map art.
    center_x, center_y = 798, 564
    color = '#E9BD58'
    for row in range(3):
        for col in range(3):
            dx, dy = (col - row) * 66, (col + row - 2) * 33
            points = [(center_x + dx - 64, center_y + dy), (center_x + dx, center_y + dy - 32),
                      (center_x + dx + 64, center_y + dy), (center_x + dx, center_y + dy + 32),
                      (center_x + dx - 64, center_y + dy)]
            c.lines(points, color=color, width=3, role='tool-selection-grid')
    c.panel((82, 798, 870, 122))
    c.text('当前工具：' + tab, (138, 824, 445, 50), 29, family='title')
    c.button('取消工具', (660, 820, 252, 66), primary=False)


def render_popup(c, record, tab):
    render_hud(c, {'key': 'main'}, '运行')
    if record['key'] == 'dropdown':
        c.panel((670, 260, 680, 570))
        c.text('选择' + tab, (708, 288, 585, 48), 34, family='title')
        if tab == '颜色':
            values = ['玉绿', '青绿', '暖金', '米白', '朱砂', '桃粉', '浅灰', '天青']
            colors = ['#367D61', '#4F9690', '#C6A04F', '#F4EBD6', '#B84F42', '#DAB3AE', '#A3ADA7', '#81ABB7']
            for i, value in enumerate(values):
                bx, by = 708 + i % 4 * 150, 370 + i // 4 * 190
                c.draw.rectangle((bx + 22, by + 8, bx + 112, by + 98), fill=colors[i], outline=GOLD, width=3)
                c.shapes.append({'role': 'color-palette-value', 'region': [bx + 22, by + 8, 90, 90], 'color': colors[i]})
                c.text(value, (bx, by + 113, 138, 44), 24, align='center')
        elif tab == '图像':
            for i, value in enumerate(['普通路', '排队路', '木栏杆', '玉栏杆', '青石路', '木步道']):
                bx, by = 712 + i % 3 * 200, 366 + i // 3 * 180
                c.icon(20 + i, (bx + 46, by, 100, 100))
                c.text(value, (bx, by + 110, 185, 42), 24, align='center')
        else:
            for i, value in enumerate(['普通', '快速', '更快', '最高速度', '不可用选项']):
                c.button(('✓ ' if i == 1 else '') + value, (708, 356 + i * 82, 590, 64),
                         state='disabled' if i == 4 else 'normal', primary=(i == 1))
    else:
        c.panel((880, 468, 770, 232))
        title = '游龙飞车' if record['key'] == 'map-tooltip' else '建造新设施'
        c.icon(6, (913, 500, 110, 110))
        c.text(title, (1040, 494, 560, 50), 32, family='title')
        c.text('营业中 · 排队 126 人\n点击查看设施，右键关闭提示。' if record['key'] == 'map-tooltip' else
               '选择设施类型，使用蓝图或自定义轨道。\n快捷键：F3', (1040, 554, 550, 118), 24)


def dialog_data(record, tab):
    key = record['key']
    presets = {
        'demolish-ride-prompt': ('拆除游龙飞车？', '设施与所属轨道将被移除。\n预计返还 8,200 铜钱。', ['确认拆除', '取消'], 'danger'),
        'refurbish-ride-prompt': ('翻新游龙飞车？', '翻新费用 3,600 铜钱。\n翻新后改善设施可靠性。', ['确认翻新', '取消'], 'confirm'),
        'staff-fire-prompt': ('解雇清风？', '当前岗位：维修工\n解雇后，此员工将离开园区。', ['确认解雇', '取消'], 'danger'),
        'overwrite-prompt': ('覆盖同名存档？', '文件：青云初试.park\n新保存内容将替换此文件。', ['覆盖保存', '取消'], 'danger'),
        'save-prompt': ('离开前保存园区？', '当前园区的改动尚未保存。\n请选择保存、不保存或取消。', ['保存', '不保存', '取消'], 'confirm'),
        'error': ('此处无法建造', '所选位置不属于园区。\n请购买土地或选择其他位置。', ['关闭'], 'error'),
        'text-input': ('修改园区名称', '请输入园区名称。', ['确认', '取消'], 'input'),
        'progress-window': ('正在处理园区', '正在加载对象与园区资料 · 68%', ['取消'], 'progress'),
        'network-status': ('正在连接服务器' if tab == '连接中' else '正在下载园区' if tab == '下载中' else '无法连接服务器',
                           '青云同游 · 正在认证' if tab == '连接中' else '已下载 6.8 / 10 MB' if tab == '下载中' else '当前游戏与服务器网络版本不同。',
                           ['取消连接'] if tab != '失败' else ['返回服务器列表'], 'progress' if tab != '失败' else 'error'),
        'track-design-manage': ('永久删除轨道蓝图？', '蓝图：云龙环山\n此操作会删除所选蓝图文件。', ['确认删除', '取消'], 'danger'),
    }
    return presets.get(key, (record['title'], tab, ['确认', '取消'], 'confirm'))


def render_dialog(c, title, message, actions, kind='confirm', context=True, state=None):
    if context:
        render_hud(c, {'key': 'main'}, '运行')
    x, y, width, height = 425, 280, 1070, 550
    c.panel((x, y, width, height), 'panel_main')
    c.text(title, (x + 70, y + 45, width - 140, 88), 40, family='title', align='center', minimum=30,
           color=RED if kind in ('danger', 'error') else JADE)
    c.lines([(x + 62, y + 145), (x + width - 62, y + 145)], width=1)
    icon = 45 if kind in ('danger', 'error', 'warning') else 44 if kind == 'success' else 42
    c.icon(icon, (x + 68, y + 188, 144, 144))
    c.text(message, (x + 252, y + 190, width - 320, 176), 28, minimum=24, valign='center')
    if kind == 'progress':
        c.progress(.68, (x + 86, y + 375, width - 172, 30))
    elif kind in ('input', 'form'):
        c.panel((x + 252, y + 338, width - 320, 68))
        c.text('••••••••' if state and state.get('id') == 'password' else '青云游园',
               (x + 276, y + 351, width - 365, 44), 26)
    if state and state.get('visualKind') == 'disabled':
        label = '开始活动' if state.get('id') == 'selection-required' else '当前操作不可用'
        c.button(label, (x + 260, y + 359, 550, 58), state='disabled')
    total = sum(max(186, min(320, len(a) * 30 + 80)) for a in actions[:3]) + (len(actions[:3]) - 1) * 18
    bx = x + (width - total) / 2
    for i, label in enumerate(actions[:3]):
        bw = max(186, min(320, len(label) * 30 + 80))
        c.button(label, (int(bx), y + height - 106, bw, 68), primary=(i == 0))
        bx += bw + 18


def render_body(c, record, tab, p, box):
    x, y, width, height = box
    layout = p['layout']
    if p.get('hint'):
        c.text(p['hint'], (x + 5, 867, width - 12, 36), 22, color=MUTED)
    if layout == 'catalog':
        render_catalog(c, box, p, record)
    elif layout == 'scenarios':
        list_w = int(width * .57)
        for i, name in enumerate(p['names'][:4]):
            by = y + i * 108
            c.panel((x, by, list_w - 20, 96))
            c.illustration(0, (x + 15, by + 5, 112, 86), 'mountain_scenario' if i % 2 == 0 else 'lake_scenario')
            c.text(name, (x + 145, by + 12, list_w - 315, 48), 29, family='title')
            c.text('初学者' if i < 2 else '挑战场景', (x + 147, by + 57, 220, 32), 22, color=MUTED)
            c.text('已完成' if i == 0 else '可挑战', (x + list_w - 170, by + 27, 130, 40), 23, color=GREEN)
        rx = x + list_w + 16
        rw = width - list_w - 16
        c.viewport((rx, y, rw, 230), '青云初试')
        c.text('经营目标', (rx + 12, y + 250, rw - 24, 44), 30, family='title')
        c.text('在第 3 年 10 月前，吸引 1,500 位游客，\n并保持园区评分不少于 600。', (rx + 12, y + 307, rw - 26, 130), 25)
    elif layout == 'table':
        sy = y
        if p.get('summary'):
            sw = int((width - 36) / 3)
            for i, (label, value) in enumerate(p['summary']):
                bx = x + i * (sw + 18)
                c.panel((bx, y, sw, 130))
                c.text(label, (bx + 48, y + 28, sw - 96, 34), 23, color=MUTED)
                c.text(value, (bx + 48, y + 72, sw - 96, 44), 29, family='body')
            sy += 150
        render_table(c, (x, sy, width, height - (sy - y)), p.get('columns', ['名称', '状态']), p.get('rows', []), row_height=64)
    elif layout == 'chart':
        render_chart(c, box, p.get('chart', tab))
    elif layout in ('form', 'tabs', 'detail'):
        render_fields(c, box, p.get('fields', []), illustration=True, illustration_index=p.get('illustration', 0))
    elif layout == 'document':
        c.illustration(11, (x + width - 370, y + 20, 330, min(410, height - 20)))
        c.text(p.get('heading', record['title']), (x + 24, y + 14, width - 410, 72), 38, family='title', minimum=30)
        paragraphs = p.get('paragraphs') or [f['label'] + '：' + str(f['value']) for f in p.get('fields', [])]
        c.text('\n\n'.join(paragraphs), (x + 24, y + 105, width - 415, height - 110), 27, minimum=22)
    elif layout in ('person', 'needs'):
        cw = 340
        c.panel((x, y, cw, height))
        if p.get('person') == 'guest':
            c.icon(0, (x + 56, y + 42, cw - 112, 236), 'visitor')
        elif p.get('person') == 'staff':
            c.illustration(0, (x + 28, y + 22, cw - 56, 280), 'mechanic')
        else:
            c.icon(0, (x + 56, y + 42, cw - 112, 236), 'multiplayer')
        name = '云游客 128' if p.get('person') == 'guest' else '清风 · 维修工' if p.get('person') == 'staff' else '清风 · 建设者'
        c.text(name, (x + 20, y + 322, cw - 40, 70), 31, family='title', align='center')
        rx, rw = x + cw + 34, width - cw - 34
        if layout == 'needs':
            fields = p.get('fields') or pairs(('幸福感', '82%'), ('体力', '64%'), ('饥饿', '30%'), ('口渴', '45%'), ('眩晕', '12%'), ('如厕需求', '20%'))
            for i, item in enumerate(fields):
                by = y + i * 77
                label, value = item['label'], item['value']
                c.text(label, (rx + 4, by + 8, 160, 46), 26)
                number = float(re.search(r'\d+', str(value)).group()) / 100
                c.progress(number, (rx + 170, by + 12, rw - 286, 32))
                c.text(value, (rx + rw - 100, by + 8, 96, 42), 26, align='right')
        else:
            fields = p.get('fields') or pairs(('当前行动', '前往游龙飞车'), ('所在位置', '青云广场'), ('追踪', '开启'), ('携带现金', '240 铜钱'))
            render_fields(c, (rx, y + 20, rw, height - 30), fields, illustration=False)
    elif layout == 'viewport':
        view_w = int(width * .56)
        c.viewport((x, y, view_w, height), '游龙飞车' if record['key'] == 'ride' else '园区预览')
        render_fields(c, (x + view_w + 34, y + 5, width - view_w - 34, height - 10), p.get('fields', []), illustration=False)
    elif layout == 'files':
        c.text(p.get('hint', '本地文件'), (x + 12, y, width - 24, 40), 25, color=MUTED)
        list_w = int(width * .72)
        render_table(c, (x, y + 58, list_w, height - 58), p['columns'], p['rows'])
        c.viewport((x + list_w + 24, y + 58, width - list_w - 24, 252), '存档预览')
        c.text('青云初试\n游客 1,280 人\n第 3 年 · 6 月', (x + list_w + 48, y + 334, width - list_w - 72, 130), 25)
    elif layout == 'dual-list':
        cw = int((width - 80) / 2)
        for i, side in enumerate(('left', 'right')):
            bx = x + i * (cw + 80)
            c.panel((bx, y, cw, height))
            c.text(p[side + 'Title'], (bx + 22, y + 20, cw - 44, 58), 29, family='title')
            for j, row in enumerate(p[side + 'Rows']):
                c.icon(5 + j + i * 4, (bx + 24, y + 105 + j * 88, 62, 62))
                c.text(row, (bx + 104, y + 116 + j * 88, cw - 132, 50), 27)
        c.text('⇄', (x + cw + 4, y + height // 2 - 30, 72, 70), 44, color=GOLD, align='center')
    elif layout == 'research':
        left_w = int(width * .61)
        render_fields(c, (x, y, left_w, 345), p.get('fields', []), illustration=False)
        c.progress(.68, (x + 12, y + height - 64, left_w - 24, 36), '当前阶段进度 · 68%')
        rx, rw = x + left_w + 28, width - left_w - 28
        c.panel((rx, y, rw, height))
        c.text('研究优先类别', (rx + 24, y + 20, rw - 48, 46), 29, family='title')
        for i, label in enumerate(['交通设施', '温和设施', '过山车', '惊险设施', '水上设施', '商店与服务', '景观主题']):
            c.checkbox(label, (rx + 28, y + 76 + i * 55, rw - 56, 52), i in (0, 2, 4, 6))
    elif layout == 'objective':
        c.illustration(6, (x + width - 430, y + 10, 400, 340))
        render_fields(c, (x, y, width - 480, height - 100), p['fields'], illustration=False)
        c.progress(1280 / 1500, (x + 15, y + height - 68, width - 500, 36), '游客目标 · 1,280 / 1,500')
    elif layout == 'ratings':
        for i, (label, value) in enumerate([('刺激度', '6.80 · 高'), ('强度', '5.20 · 中'), ('眩晕度', '2.40 · 低')]):
            cw = int((width - 36) / 3)
            bx = x + i * (cw + 18)
            c.panel((bx, y, cw, 180))
            c.icon(37 + i, (bx + 16, y + 26, 112, 112))
            c.text(label, (bx + 145, y + 30, cw - 170, 44), 27, family='title')
            c.text(value, (bx + 145, y + 90, cw - 170, 58), 30, color=GREEN if i == 0 else JADE)
        render_fields(c, (x + 8, y + 220, width - 16, height - 230), p['fields'][3:], illustration=True, illustration_index=0)
    elif layout == 'permissions':
        render_fields(c, (x, y, width, 150), p['fields'], illustration=False)
        labels = ['建设轨道', '铺设步道', '编辑景观', '修改设施', '管理财务', '调整员工', '编辑园区', '管理权限组']
        for i, label in enumerate(labels):
            c.checkbox(label, (x + i % 2 * width // 2 + 20, y + 180 + i // 2 * 70, width // 2 - 50, 60), i < 5)
    elif layout == 'map':
        view_w = int(width * .68)
        c.viewport((x, y, view_w, height), '园区地图', selection=True)
        render_fields(c, (x + view_w + 24, y + 8, width - view_w - 24, height - 16), p['fields'], illustration=False)
    elif layout == 'inspector':
        list_w = int(width * .56)
        render_table(c, (x, y, list_w, height), ['元素', '基础高度', '清除高度'],
                     [['地表', '8', '8'], ['步道', '8', '12'], ['轨道', '16', '22'], ['墙体', '8', '16'], ['横幅', '12', '16']], 66)
        render_fields(c, (x + list_w + 28, y, width - list_w - 28, height), p['fields'], illustration=False)
    elif layout == 'progress':
        c.illustration(10, (x + 25, y + 30, 300, height - 60))
        c.text(p.get('heading', '处理中'), (x + 360, y + 50, width - 400, 80), 38, family='title')
        c.text(p.get('message', '正在处理，请稍候。'), (x + 360, y + 158, width - 400, 100), 27)
        c.progress(.68, (x + 360, y + 305, width - 420, 42))
    elif layout == 'console':
        c.panel(box)
        c.text('控制台', (x + 30, y + 18, width - 60, 50), 32, family='title')
        c.text('> help\n查看可用命令与参数。\n\n> screenshot\n截图命令示例\n\n输入命令：_', (x + 34, y + 90, width - 68, height - 110), 28)
    else:
        render_fields(c, box, p.get('fields') or pairs(*[(v, '可查看') for v in record['features'][:5]]),
                      illustration=True, illustration_index=p.get('illustration', 0))


def render_screen(store, record, tab, index):
    identity = f"{record['key']}:{index + 1:02}"
    c = Canvas(store, identity, record['title'] + ' · ' + tab)
    p = profile(record, tab, index)
    if p['layout'] == 'menu':
        render_menu(c, record, tab)
    elif p['layout'] == 'hud':
        render_hud(c, record, tab, index)
    elif p['layout'] == 'tool':
        render_tool(c, record, tab, p)
    elif p['layout'] == 'popup':
        render_popup(c, record, tab)
    elif p['layout'] == 'dialog':
        render_dialog(c, *dialog_data(record, tab))
    elif p['layout'] == 'editor-hud':
        render_hud(c, {'key': 'main'}, '运行')
        c.panel((66, 154, 1788, 146))
        c.text('场景编辑 · 第 2 步 / 共 7 步', (110, 180, 1200, 50), 35, family='title')
        c.text('设置园区土地、入口道路与游客出生点。', (112, 240, 1500, 42), 26)
        c.button('上一步', (90, 858, 270, 78), primary=False)
        c.button('下一步', (1560, 858, 270, 78))
    else:
        box = c.frame(record, tab, index)
        if p.get('wizard'):
            c.text('对象  ›  地形  ›  研究  ›  选项  ›  目标  ›  资料  ›  保存', (box[0] + 8, box[1] - 6, box[2] - 16, 40), 23, color=MUTED)
            box = (box[0], box[1] + 52, box[2], box[3] - 52)
        render_body(c, record, tab, p, box)
        c.actions(p.get('actions', ['关闭']))
    return c, p


STATE_WINDOWS = {
    'start': 'scenario-select', 'hud': 'main', 'new-ride': 'new-ride', 'track-build': 'ride-construction',
    'ride-operation': 'ride', 'shops': 'ride', 'paths-land': 'footpath', 'scenery': 'scenery',
    'guests': 'guest', 'staff': 'staff-list', 'park': 'park', 'finances': 'finances', 'marketing': 'new-campaign',
    'research': 'research', 'editor': 'editor-scenario-options', 'mapgen': 'map-gen', 'save-load': 'load-save',
    'track-files': 'track-list', 'multiplayer': 'server-list', 'settings': 'options', 'messages-support': 'news',
}


def render_state(store, system, state, records):
    key = STATE_WINDOWS[system['key']]
    record = records[key]
    kind, state_id = state['visualKind'], state['id']
    identity = 'state:' + system['key'] + ':' + state_id
    c = Canvas(store, identity, system['title'] + ' · ' + state['title'])
    actions = [state['primaryAction']]
    actions.extend([part.strip() for part in state['secondaryAction'].split('/')])
    modal_kinds = {'error', 'warning', 'danger', 'confirm', 'disabled', 'locked', 'input'}
    if kind in modal_kinds or state_id in ('password', 'overwrite', 'save-prompt'):
        render_dialog(c, state['title'], state['message'], actions, kind, state=state)
    elif kind == 'empty':
        box = c.frame(record, record['tabs'][0], 0)
        x, y, width, height = box
        c.illustration(11, (x + width // 2 - 160, y - 5, 320, 255))
        c.text(state['title'], (x + 100, y + 260, width - 200, 70), 37, family='title', align='center')
        c.text(state['message'], (x + 90, y + 345, width - 180, 110), 27, align='center')
        c.actions(actions)
    elif kind == 'progress' and system['key'] not in ('research', 'park'):
        render_dialog(c, state['title'], state['message'], actions, 'progress', state=state)
    elif kind in ('hud', 'paused') and system['key'] == 'hud':
        render_hud(c, {'key': 'main'}, '暂停' if state_id == 'paused' else '运行')
        if state_id != 'running':
            c.panel((70, 730, 990, 180))
            c.text(state['title'], (104, 752, 900, 50), 34, family='title')
            c.text(state['message'], (106, 816, 890, 80), 27)
    else:
        tab_index = 0
        tab_targets = {
            'ride-operation': {'untested': '测试', 'testing': '测试', 'broken': '维护', 'disconnected': '概览'},
            'guests': {'normal': '需求', 'no-items': '携带物', 'no-rides': '游玩记录'},
            'park': {'objective-progress': '目标', 'objective-success': '目标', 'objective-failure': '目标', 'no-awards': '奖项'},
            'finances': {'graph-empty': '现金'},
            'settings': {'accessibility': '操作', 'theme-edit': '界面', 'custom-currency': '文化'},
            'editor': {'objective': '目标', 'details': '场景详情', 'options': '财务'},
            'multiplayer': {'connected': '公共列表'},
        }
        target = tab_targets.get(system['key'], {}).get(state_id)
        if target in record['tabs']:
            tab_index = record['tabs'].index(target)
        if system['key'] == 'editor' and state_id == 'object-selection':
            record = records['editor-object-selection']
        elif system['key'] == 'editor' and state_id == 'research-list':
            record = records['editor-inventions-list']
        elif system['key'] == 'messages-support' and state_id == 'about':
            record = records['about']
        elif system['key'] == 'messages-support' and state_id == 'asset-packs':
            record = records['asset-packs']
        elif system['key'] == 'settings' and state_id == 'custom-currency':
            record = records['custom-currency']
        elif system['key'] == 'settings' and state_id == 'theme-edit':
            record = records['themes']
        elif system['key'] == 'mapgen' and state_id == 'map-view':
            record = records['map']
        elif system['key'] == 'mapgen' and state_id == 'view-clipping':
            record = records['view-clipping']
        elif system['key'] == 'multiplayer' and state_id == 'connected':
            record = records['multiplayer']
        tab_index = min(tab_index, len(record['tabs']) - 1)
        p = profile(record, record['tabs'][tab_index], tab_index)
        p['actions'] = actions
        p['hint'] = state['message']
        if system['key'] == 'shops':
            p.update(layout='viewport', fields=pairs(('商店', '丹茶铺'), ('状态', '营业中' if state_id == 'open' else '已关闭'),
                     ('商品', '青梅茶'), ('售价', '8 铜钱'), ('单位成本', '3 铜钱'), ('已售数量', '240 杯')))
        if kind in ('selection', 'construction', 'tool'):
            p['layout'] = 'tool'
            p['toolLabel'] = state['title']
            if not p.get('fields'):
                p['fields'] = pairs(('当前工具', state['title']), ('选择范围', '3 × 3'), ('方向', '东北'), ('预估费用', '120 铜钱'))
            render_tool(c, record, state['title'], p)
        else:
            box = c.frame(record, record['tabs'][tab_index], tab_index)
            if kind == 'success':
                c.text('✓ ' + state['title'], (box[0] + 8, box[1] - 2, box[2] - 16, 52), 32, color=GREEN, family='title')
                box = (box[0], box[1] + 65, box[2], box[3] - 65)
            if system['key'] == 'park' and state_id == 'objective-success':
                p.update(layout='form', fields=pairs(('结果', '场景目标已达成'), ('公司价值', '240,000 铜钱'), ('完成者', '清风（示例）')))
            elif kind == 'closed' or state_id in ('closed', 'open'):
                p['fields'] = pairs(('当前状态', '已关闭' if state_id == 'closed' else '营业中')) + p.get('fields', [])[1:]
            render_body(c, record, record['tabs'][tab_index], p, box)
            c.actions(actions)
    c.text(system['title'], (64, 1038, 520, 32), 18, color=CREAM, minimum=18)
    return c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', action='append', help='Window or state system key; may be repeated.')
    parser.add_argument('--screens-only', action='store_true')
    parser.add_argument('--states-only', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    store = AssetStore(ROOT)
    inventory_path = ROOT / 'docs/repo-ui-inventory.json'
    state_path = ROOT / 'docs/state-contracts.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    state_contracts = json.loads(state_path.read_text(encoding='utf-8'))
    records = {r['key']: r for r in inventory}
    entries = []
    print('Ready:', len(inventory), 'window units;', sum(len(x['tabs']) for x in inventory), 'screen tabs;',
          sum(len(s['states']) for s in state_contracts['systems']), 'state contracts', flush=True)
    if not args.states_only:
        for record in inventory:
            if args.only and record['key'] not in args.only:
                continue
            for index, tab in enumerate(record['tabs']):
                if args.limit and len(entries) >= args.limit:
                    break
                c, p = render_screen(store, record, tab, index)
                slug = re.sub(r'[^\w\-]+', '-', tab, flags=re.UNICODE).strip('-')[:60]
                path = ROOT / 'designs' / record['key'] / f'{index + 1:02}-{slug}.png'
                meta = {'repository': 'https://github.com/OpenRCT2/OpenRCT2.git', 'commit': record['functionalReferenceCommit'],
                        'windowKey': record['key'], 'tab': tab, 'sourceEvidence': record.get('sourceEvidence', []),
                        'visualAssumptions': record.get('visualAssumptions', [])}
                result = c.save(path, meta)
                entries.append(dict(screenId=c.identity, id=c.identity, key=record['key'], category='screen', windowKey=record['key'], system=record['system'],
                                    title=record['title'], tab=tab, tabIndex=index, layoutKind=p['layout'],
                                    sourceFiles=record.get('sourceFiles', []), sourceEvidence=record.get('sourceEvidence', []), **result))
                print('SCREEN', record['key'], index + 1, tab, 'issues', len(c.issues), flush=True)
    if not args.screens_only:
        for system in state_contracts['systems']:
            if args.only and system['key'] not in args.only:
                continue
            for state in system['states']:
                if args.limit and len(entries) >= args.limit:
                    break
                c = render_state(store, system, state, records)
                path = ROOT / 'previews/states' / system['key'] / (state['id'] + '.png')
                meta = {'repository': state_contracts['referenceRepository'], 'commit': state_contracts['referenceCommit'],
                        'stateContract': 'docs/state-contracts.json', 'system': system['key'], 'state': state,
                        'evidence': system['evidence']}
                result = c.save(path, meta)
                entries.append(dict(screenId=c.identity, id=c.identity, category='state', systemKey=system['key'], system=system['key'], title=system['title'],
                                    stateId=state['id'], stateTitle=state['title'], visualKind=state['visualKind'],
                                    logicBasis=state['logicBasis'], sourceEvidence=system['evidence'], **result))
                print('STATE', system['key'], state['id'], 'issues', len(c.issues), flush=True)
    manifest_path = ROOT / 'docs/ui-production-manifest.json'
    previous = {}
    if manifest_path.exists() and (args.only or args.limit or args.screens_only or args.states_only):
        previous = {x['screenId']: x for x in json.loads(manifest_path.read_text(encoding='utf-8')).get('images', [])}
    for entry in entries:
        previous[entry['screenId']] = entry
    all_entries = sorted(previous.values(), key=lambda x: x['screenId']) if previous else entries
    manifest = {'schemaVersion': 1, 'createdAt': datetime.now().astimezone().isoformat(),
                'project': '云游仙苑（暂名）· OpenRCT2 道家 Q 版 UI',
                'referenceResolution': [W, H], 'operation': 'composite_preview_not_native_generation',
                'status': 'produced_pending_review', 'expectedScreenTabs': sum(len(r['tabs']) for r in inventory),
                'expectedStates': sum(len(s['states']) for s in state_contracts['systems']),
                'screenCount': sum(e['category'] == 'screen' for e in all_entries),
                'stateCount': sum(e['category'] == 'state' for e in all_entries),
                'layoutIssueCount': sum(len(e['layoutIssues']) for e in all_entries),
                'assetManifest': 'assets/slice-manifest.json', 'sourceInventory': 'docs/repo-ui-inventory.json',
                'stateContract': 'docs/state-contracts.json',
                'fontNotes': 'Uses bundled OFL-licensed Noto Sans CJK SC and Ma Shan Zheng; see records/font-sources.json.',
                'unityStatus': 'not_integrated_not_runtime_validated', 'images': all_entries,
                'screens': [e for e in all_entries if e['category'] == 'screen'],
                'states': [e for e in all_entries if e['category'] == 'state']}
    write_json(manifest_path, manifest)
    print('Wrote', rel(manifest_path), 'screens', manifest['screenCount'], 'states', manifest['stateCount'],
          'layout issues', manifest['layoutIssueCount'], flush=True)


if __name__ == '__main__':
    main()
