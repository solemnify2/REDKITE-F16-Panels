#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""통합 브리지 아이콘(`tools/bridge.ico`)을 만듭니다.

    python tools/make_bridge_icon.py

`BMS-BIOS.ico` 와 `DCS-BIOS2.ico` 에서 가져온 것:

  * 색 — BMS 의 파랑 그라디언트, DCS 의 주황 그라디언트. 실제 픽셀에서 뽑았습니다.
  * 모서리 둥근 사각형 — DCS 쪽 모양
  * 이탤릭 BIOS 워드마크 — 양쪽에 공통으로 있는 유일한 글자

하나의 브리지가 두 심을 상대한다는 것을 **대각선 분할**로 말합니다. 왼쪽 위가
DCS 주황, 오른쪽 아래가 BMS 파랑입니다. 16px 에서는 글자가 뭉개지므로 작은 크기는
분할과 기체만 남기고 글자를 뺍니다 — 색 두 개와 실루엣은 그 크기에서도 읽힙니다.

기체는 원본에서 오려내지 않고 다시 그렸습니다. BMS 아이콘의 기체는 같은 색의
콘트레일과 한 덩어리로 붙어 있어, 떼어내려고 자르면 날개까지 잘립니다.

PIL 이 필요합니다:  pip install pillow
"""
import math
import os
import sys

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
except ImportError:
    raise SystemExit('Pillow 가 필요합니다:  pip install pillow')

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, 'bridge.ico')
DEST_PLAIN = os.path.join(HERE, 'bridge-plain.ico')
DEST_USB = os.path.join(HERE, 'bridge-usb.ico')
DEST_TERM = os.path.join(HERE, 'bridge-term.ico')
DEST_PROMPT = os.path.join(HERE, 'bridge-prompt.ico')
DEST_LED = os.path.join(HERE, 'bridge-led.ico')
DEST_LAMP = os.path.join(HERE, 'bridge-lamp.ico')
DEST_GEAR = os.path.join(HERE, 'bridge-gear.ico')
GEAR_DXF = os.path.join(HERE, 'GearLedLayout.dxf')
BIOS_TEXT = os.path.join(HERE, 'bios-text.png')
SIZES = (16, 24, 32, 48, 64, 128, 256)
TEXT_FROM = 128         # 이보다 작으면 글자를 넣지 않습니다
RING_FROM = 32          # 이보다 작으면 테두리가 형태를 먹으므로 생략합니다
SS = 4                  # 수퍼샘플 배율

# BMS-BIOS.ico / DCS-BIOS2.ico 에서 실제로 뽑은 색입니다.
BMS_TOP, BMS_BOTTOM = (56, 134, 190), (6, 44, 74)
DCS_TOP, DCS_BOTTOM = (248, 168, 12), (236, 112, 0)
INK = (8, 26, 44)       # 외곽선과 그림자

# 원본을 따릅니다 — DCS-BIOS2.ico 의 DCS 는 굵은 이탤릭, BMS-BIOS.ico 의 BMS 는 직립.
ITALIC_FONTS = (r'C:\Windows\Fonts\arialbi.ttf',
                r'C:\Windows\Fonts\ariali.ttf',
                r'C:\Windows\Fonts\arialbd.ttf')
UPRIGHT_FONTS = (r'C:\Windows\Fonts\arialbd.ttf',
                 r'C:\Windows\Fonts\arial.ttf')

# 자리는 BMS-BIOS.ico 의 기체를 재서 가져왔습니다 (256px 기준 x 94..202, y 52..165).
# 크기는 거기서부터 키운 값으로, 모서리에도 글자에도 닿지 않는 선입니다.
# **이 두 값은 확정입니다 — 바꾸지 마십시오.**
JET_CENTER = (0.578, 0.424)
# BMS-BIOS.ico 에서 잰 값입니다. 흰 기체 마스크를 옮겨 가며 어두운 영역과
# 가장 많이 겹치는 자리를 찾았습니다 — 256px 기준 dx -56, dy -16 (일치율 0.50).
SHADOW_OFFSET = (-0.219, -0.062)
SHADOW_ALPHA = 90
MARK_CENTER = (0.52, 0.52)       # 기체 위에 겹치는 글리프 자리
TERM_GREEN = (30, 240, 2)        # bios-text.png 에서 뽑은 터미널 녹색
AMBER = (255, 176, 0)            # 표시등
LED_ON = (70, 225, 70)           # 켜진 칸
LED_OFF = (40, 55, 72)           # 꺼진 칸
GEAR_ART = (238, 248, 242)       # 패널 각인선
GEAR_GLOW = (120, 255, 150)      # LED 번짐
GEAR_LED = (60, 230, 90)         # LED 몸통 (진한 녹색)
GEAR_CORE = (228, 255, 232)      # LED 한가운데 흰 심
JET_FILL_A = (255, 250, 242)     # 기체 왼쪽 위 (주황 쪽)
JET_FILL_B = (214, 228, 243)     # 기체 오른쪽 아래 (파랑 쪽)
JET_SHADE = (96, 120, 150)
JET_SHADE_ALPHA = 180
JET_SHADE_WIDTH = 0.020
JET_SHADE_BLUR = 0.010
JET_SCALE = 0.70
TILT = -32                       # 기체와 기어 판을 함께 기울이는 각도

# F-16 평면형. 기수가 위를 향하고 x=50 에 대칭인 100 x 146 상자 안의 좌표입니다.
#
# 손으로 그린 게 아니라 미 국방부의 F-16 3면도(퍼블릭 도메인, Wikimedia Commons
# "General Dynamics F-16 Fighting Falcon 3-view line drawing.png")의 상면도에서
# 실루엣을 떠 왔습니다. 바깥 여백에서 채우기를 돌려 기체 안쪽을 얻고, 행마다
# 중심선을 품은 구간만 남겨 떨어져 나온 날개끝 발사대를 버린 뒤, 오른쪽 윤곽을
# Douglas-Peucker 로 305점에서 24점으로 줄였습니다 (원본 마스크와 IoU 0.957).
#
# 끝점의 x 가 50 이 아닌 것은 오타가 아닙니다 — 기수와 노즐의 실제 두께입니다.
HALF = [
    (50.72, 0.00), (50.72, 4.78), (54.55, 15.79), (55.98, 30.62),
    (58.85, 45.93), (63.16, 56.94), (64.59, 68.90), (67.46, 71.77),
    (92.82, 91.39), (95.22, 92.82), (98.09, 93.30), (98.09, 102.39),
    (100.00, 103.35), (100.00, 104.78), (62.68, 105.26), (62.68, 116.75),
    (77.03, 128.71), (77.99, 129.67), (77.99, 132.06), (56.94, 132.54),
    (55.98, 140.19), (51.67, 140.67), (51.67, 143.54), (50.72, 145.45),
]
JET = HALF + [(100 - x, y) for x, y in reversed(HALF[:-1])]


def gradient(size, top, bottom):
    """위에서 아래로 흐르는 세로 그라디언트."""
    img = Image.new('RGB', (1, size))
    px = img.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        px[0, y] = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
    return img.resize((size, size), Image.BILINEAR)


def jet_mask(size):
    """기체 실루엣 — 기수가 오른쪽 위를 향하도록 돌려서 돌려줍니다."""
    w = round(max(x for x, _ in JET) * SS) + 1
    h = round(max(y for _, y in JET) * SS) + 1
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in JET], fill=255)
    m = m.rotate(TILT, resample=Image.BICUBIC, expand=True)
    # 회전하면 상자 모서리에 빈 공간이 생깁니다. 그 상자로 크기를 맞추면 기체가
    # 요청한 것보다 작아지므로, 실제 그려진 영역만 잘라 기준으로 삼습니다.
    m = m.crop(m.getbbox())
    scale = size / max(m.size)
    return m.resize((max(round(m.size[0] * scale), 1),
                     max(round(m.size[1] * scale), 1)), Image.LANCZOS)


def fitted_font(draw, text, width, italic=True):
    """`text` 가 `width` 에 들어가는 가장 큰 글꼴."""
    path = next((p for p in (ITALIC_FONTS if italic else UPRIGHT_FONTS)
                 if os.path.isfile(p)), None)
    if path is None:
        return None
    size = 8
    while size < 400:
        font = ImageFont.truetype(path, size + 2)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] > width:
            break
        size += 2
    return ImageFont.truetype(path, size)


def label(img, text, width, cx, cy, align='center', stroke=False, italic=True):
    """`text` 를 올립니다. cx/cy/width 는 변 길이에 대한 비율.

    `stroke` 면 그림자 대신 외곽선을 두릅니다. 흰 기체와 색 바탕에 걸치는 글자는
    한 가지 색으로는 어느 한쪽에서 반드시 묻히기 때문입니다.
    """
    s = img.size[0]
    layer = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = fitted_font(d, text, round(s * width), italic)
    if font is None:
        return
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    x = round(s * cx) - (w if align == 'right' else w // 2 if align == 'center' else 0)
    tx, ty = x - box[0], round(s * cy) - h // 2 - box[1]
    if stroke:
        d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255),
               stroke_width=max(round(s * 0.016), 1), stroke_fill=INK + (255,))
    else:
        off = max(round(s * 0.012), 1)
        d.text((tx + off, ty + off), text, font=font, fill=INK + (190,))
        d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    img.alpha_composite(layer)


def bios_mark(s, width=0.66, center=(0.47, 0.495), prompt=False):
    """`bios-text.png` 의 픽셀 글꼴 BIOS 를 마스크로 돌려줍니다.

    격자를 떠서 코드에 박는 것도 해 봤지만 모듈 경계가 딱 떨어지지 않아 글자가
    뭉개졌습니다. 원본이 2172px 라 1024 캔버스에 올리기에 해상도가 남습니다.
    """
    red, green, _ = Image.open(BIOS_TEXT).convert('RGB').split()
    mark = ImageChops.darker(Image.eval(green, lambda v: 255 if v > 120 else 0),
                             Image.eval(red, lambda v: 255 if v < 160 else 0))
    if prompt:
        # 'BIOS' 와 '>_' 사이의 빈 구간은 원본에서 x 1303..1528 입니다.
        mark = mark.crop((1415, 0, mark.size[0], mark.size[1]))
    # 원본에 압축 잡티가 있어 크게 쓰면 블록 가장자리가 지저분합니다. 블록보다
    # 훨씬 작은 창의 중앙값 필터로 점만 걷어냅니다. 모듈 격자까지 줄였다 되키우는
    # 방법도 해 봤지만 모듈이 정수가 아니라 글자가 뭉개졌습니다.
    mark = mark.filter(ImageFilter.MedianFilter(9))
    mark = mark.crop(mark.getbbox())
    w = round(s * width)
    h = max(round(w * mark.size[1] / mark.size[0]), 1)
    mark = mark.resize((w, h), Image.LANCZOS)
    out = Image.new('L', (s, s), 0)
    out.paste(mark, (round(s * center[0]) - w // 2, round(s * center[1]) - h // 2))
    return out


# 획을 두 칸으로 둡니다. 한 칸이면 위아래 블록이 모서리로만 닿아 점선처럼 보입니다.
PROMPT_GRID = (
    '##.......',
    '.##......',
    '..##.....',
    '...##....',
    '..##.....',
    '.##......',
    '##..#####',
)


def prompt_mark(s, width=0.40, center=(0.38, 0.60)):
    """'>_' 를 격자에서 바로 그립니다.

    bios-text.png 의 같은 글자를 오려 키워도 봤지만, 계단이 한 칸씩이라 크게
    쓰면 획이 아니라 흩어진 블록으로 보입니다. 모양은 그대로 두고 다시 그립니다.
    """
    cols, rows = len(PROMPT_GRID[0]), len(PROMPT_GRID)
    cell = max(round(s * width / cols), 1)
    mark = Image.new('L', (cols * cell, rows * cell), 0)
    d = ImageDraw.Draw(mark)
    for r, line in enumerate(PROMPT_GRID):
        for c, ch in enumerate(line):
            if ch == '#':
                d.rectangle([c * cell, r * cell,
                             (c + 1) * cell - 1, (r + 1) * cell - 1], fill=255)
    out = Image.new('L', (s, s), 0)
    out.paste(mark, (round(s * center[0]) - mark.size[0] // 2,
                     round(s * center[1]) - mark.size[1] // 2))
    return out


def read_gear_dxf():
    """GearLedLayout.dxf 에서 닫힌 폴리라인과 원을 읽습니다.

    실제 패널의 기어 LED 판 도면입니다. 폴리라인은 윤곽선이 아니라 **각인 홈의
    테두리**라서, 선으로 긋지 않고 안을 채워야 판에 새겨진 모양이 나옵니다.
    원 셋은 LED 구멍입니다.
    """
    raw = [x.strip() for x in open(GEAR_DXF, encoding='latin-1').read().splitlines()]
    polys, circles, i = [], [], 0
    while i < len(raw) - 1:
        if raw[i] == '0' and raw[i + 1] in ('LWPOLYLINE', 'CIRCLE'):
            kind, j = raw[i + 1], i + 2
            pts, pend, circ = [], None, [None, None, None]
            while j < len(raw) - 1 and raw[j] != '0':
                code, val = raw[j], raw[j + 1]
                if kind == 'LWPOLYLINE':
                    if code == '10':
                        pend = float(val)
                    elif code == '20' and pend is not None:
                        pts.append((pend, float(val)))
                        pend = None
                elif code in ('10', '20', '40'):
                    circ[{'10': 0, '20': 1, '40': 2}[code]] = float(val)
                j += 2
            (polys if kind == 'LWPOLYLINE' else circles).append(
                pts if kind == 'LWPOLYLINE' else circ)
            i = j
        else:
            i += 2
    return polys, circles


def gear_marks(s, height=0.70, center=JET_CENTER):
    """(각인 무늬, LED 세 개) 마스크."""
    polys, circles = read_gear_dxf()
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    scale = s * height / (y1 - y0)
    w, h = (x1 - x0) * scale, (y1 - y0) * scale
    ox, oy = s * center[0] - w / 2, s * center[1] - h / 2

    def place(x, y):                      # DXF 는 y 가 위로 자랍니다
        return ox + (x - x0) * scale, oy + h - (y - y0) * scale

    art = Image.new('L', (s, s), 0)
    d = ImageDraw.Draw(art)
    for p in polys:
        if len(p) > 2:
            d.polygon([place(*q) for q in p], fill=255)
    # 각인 홈이 0.5mm 남짓이라 그대로 줄이면 사라집니다. 조금 불려 둡니다.
    art = art.filter(ImageFilter.MaxFilter(max(round(s * 0.004), 1) * 2 + 1))

    led = Image.new('L', (s, s), 0)
    dl = ImageDraw.Draw(led)
    for cx, cy, r in circles:
        x, y = place(cx, cy)
        rr = r * scale * 1.30             # 실제 돔이 구멍보다 큽니다
        dl.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)

    # 기체와 같은 각도로 눕힙니다. 두 마스크를 같은 중심으로 돌려야 LED 가 제자리에
    # 남습니다.
    pivot = (s * center[0], s * center[1])
    art = art.rotate(TILT, resample=Image.BICUBIC, center=pivot)
    led = led.rotate(TILT, resample=Image.BICUBIC, center=pivot)
    return art, led


def led_lamp(s, center=(0.50, 0.50), width=0.185):
    """LED 부품 — 돔, 플랜지, 다리 두 개, 빛살.

    처음에는 원 하나에 빛살을 두른 표시등이었는데 해처럼 보였습니다. 부품 모양이
    'LED' 라는 말을 훨씬 분명하게 합니다.
    """
    m = Image.new('L', (s, s), 0)
    d = ImageDraw.Draw(m)
    w = s * width
    cx, cy = s * center[0], s * center[1]
    top, body_bot = cy - w * 0.62, cy + w * 0.20
    d.pieslice([cx - w / 2, top, cx + w / 2, top + w], 180, 360, fill=255)
    d.rectangle([cx - w / 2, top + w / 2, cx + w / 2, body_bot], fill=255)
    fl = w * 0.62                                        # 플랜지
    d.rounded_rectangle([cx - fl, body_bot - w * 0.12, cx + fl, body_bot + w * 0.12],
                        radius=w * 0.11, fill=255)
    leg = w * 0.14
    for k in (-1, 1):
        x = cx + k * w * 0.26
        d.rounded_rectangle([x - leg / 2, body_bot + w * 0.10,
                             x + leg / 2, body_bot + w * 0.72],
                            radius=leg / 2, fill=255)
    t = max(round(w * 0.14), 1)
    for a in (205, 230, 258, 282, 310, 335):
        rad = math.radians(a)
        d.line([(cx + math.cos(rad) * w * 0.80, cy - w * 0.10 + math.sin(rad) * w * 0.80),
                (cx + math.cos(rad) * w * 1.22, cy - w * 0.10 + math.sin(rad) * w * 1.22)],
               fill=255, width=t)
    return m


def led_grid(s, center=(0.50, 0.52), width=0.30):
    """경고등 패널. 켜진 칸과 꺼진 칸 두 장을 돌려줍니다."""
    lit = Image.new('L', (s, s), 0)
    dark = Image.new('L', (s, s), 0)
    w = s * width
    h = w * 0.52
    x0, y0 = s * center[0] - w / 2, s * center[1] - h / 2
    gap = w * 0.045
    cw, ch = (w - gap * 3) / 4, (h - gap) / 2
    on = {(0, 0), (0, 2), (0, 3), (1, 1), (1, 3)}
    for r in range(2):
        for c in range(4):
            x, y = x0 + c * (cw + gap), y0 + r * (ch + gap)
            ImageDraw.Draw(lit if (r, c) in on else dark).rounded_rectangle(
                [x, y, x + cw, y + ch], radius=s * 0.010, fill=255)
    return lit, dark


def usb_mark(s):
    """USB 기호. 브리지가 실제로 쓰는 연결이라 비유가 아니라 사실입니다."""
    m = Image.new('L', (s, s), 0)
    d = ImageDraw.Draw(m)
    cx, cy = s * MARK_CENTER[0], s * MARK_CENTER[1]
    L, t, br = s * 0.17, s * 0.030, s * 0.095
    d.line([(cx, cy + L), (cx, cy - L)], fill=255, width=round(t))
    d.ellipse([cx - t * 1.5, cy + L - t * 1.5,
               cx + t * 1.5, cy + L + t * 1.5], fill=255)      # 둥근 끝
    d.line([(cx, cy - L * 0.15), (cx - br, cy - L * 0.62)], fill=255, width=round(t))
    d.rectangle([cx - br - t * 1.2, cy - L * 0.62 - t * 1.2,
                 cx - br + t * 1.2, cy - L * 0.62 + t * 1.2], fill=255)   # 네모 끝
    d.line([(cx, cy - L * 0.15), (cx + br, cy - L * 0.62)], fill=255, width=round(t))
    d.polygon([(cx + br + t * 1.6, cy - L * 0.62),
               (cx + br - t * 1.0, cy - L * 0.62 - t * 1.5),
               (cx + br - t * 1.0, cy - L * 0.62 + t * 1.5)], fill=255)   # 세모 끝
    d.polygon([(cx, cy - L - t * 0.2), (cx - t * 1.7, cy - L + t * 2.2),
               (cx + t * 1.7, cy - L + t * 2.2)], fill=255)    # 화살촉
    return m


def stamp(img, shape, fill=(255, 255, 255), outline=True, shadow=False):
    """글리프를 찍되 어두운 외곽선을 둘러, 흰 기체 위에서도 읽히게."""
    s = img.size[0]
    if outline:
        r = max(round(s * 0.013), 1)
        edge = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    edge.paste(INK + (255,), (dx, dy), shape)
        img.alpha_composite(edge)
    if shadow:
        # 테두리 없이 쓸 때. 녹색과 주황이 밝기가 비슷해 글자가 묻히는 것을
        # 윤곽을 두르지 않고 밑에 깔아 둔 그림자로만 막습니다.
        off = max(round(s * 0.009), 1)
        drop = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        drop.paste(INK + (140,), (off, off), shape)
        img.alpha_composite(drop)
    img.paste(tuple(fill) + (255,), (0, 0), shape)


def render(size, text=True, wordmark=True, usb=False, pixel=False,
           prompt=False, led=False, lamp=False, gear=False):
    """한 크기 분량의 RGBA 이미지."""
    s = size * SS
    img = gradient(s, DCS_TOP, DCS_BOTTOM).convert('RGBA')

    # 오른쪽 아래 삼각형만 BMS 파랑으로 덮습니다.
    tri = Image.new('L', (s, s), 0)
    ImageDraw.Draw(tri).polygon([(s, 0), (s, s), (0, s)], fill=255)
    img.paste(gradient(s, BMS_TOP, BMS_BOTTOM).convert('RGBA'), (0, 0), tri)

    # 경계선 — 두 색이 맞닿는 자리를 또렷하게.
    seam = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(seam).line([(0, s), (s, 0)], fill=(255, 255, 255, 70),
                              width=max(round(s * 0.012), 1))
    img.alpha_composite(seam)

    if gear:
        # 기체 자리를 실제 패널의 기어 LED 판이 대신합니다 — 그 자체가 기체 모양입니다.
        art, leds = gear_marks(s)
        drop = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        drop.paste(INK + (160,), (round(s * 0.006), round(s * 0.006)), art)
        img.alpha_composite(drop)
        img.paste(Image.new('RGBA', (s, s), GEAR_ART + (255,)), (0, 0), art)
        # 켜진 LED 처럼 보이게 합니다 — 넓게 번지는 빛, 그 안에 진한 녹색,
        # 가운데에 흰 심. 사진의 램프가 이 순서로 밝아집니다.
        if size >= RING_FROM:
            for blur, alpha in ((0.042, 120), (0.017, 205)):
                bloom = leds.filter(ImageFilter.GaussianBlur(s * blur))
                bloom = Image.eval(bloom, lambda v, a=alpha: v * a // 255)
                img.paste(Image.new('RGBA', (s, s), GEAR_GLOW + (255,)), (0, 0), bloom)
        img.paste(Image.new('RGBA', (s, s), GEAR_LED + (255,)), (0, 0), leds)
        core = leds.filter(ImageFilter.MinFilter(max(round(s * 0.007), 1) * 2 + 1))
        img.paste(Image.new('RGBA', (s, s), GEAR_CORE + (255,)), (0, 0), core)
        if size >= TEXT_FROM and text:
            label(img, 'DCS', 0.40, 0.10, 0.12, align='left')
            label(img, 'BMS', 0.40, 0.90, 0.88, align='right', italic=False)
        mask = Image.new('L', (s, s), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                               radius=round(s * 0.20), fill=255)
        img.putalpha(mask)
        return img.resize((size, size), Image.LANCZOS)

    big = size < TEXT_FROM

    # 글자가 빠지는 작은 크기에서는 기체가 아이콘 전체를 채웁니다. 글자가 들어가면
    # BMS-BIOS.ico 의 기체와 같은 자리, 같은 크기로 앉습니다 (원본에서 잰 값).
    # 밝은 주황 위에서도 형태가 살도록 어두운 테두리를 깔아 줍니다.
    jet = jet_mask(round(s * (0.70 if big else JET_SCALE)))
    cx, cy = (0.50, 0.50) if big else JET_CENTER
    jx = round(s * cx) - jet.size[0] // 2
    jy = round(s * cy) - jet.size[1] // 2
    if size >= RING_FROM:
        # BMS-BIOS.ico 처럼 기체 뒤로 같은 실루엣을 왼쪽 아래에 깔아 둡니다.
        # 반투명이라 주황 쪽과 파랑 쪽에서 각각 그 색이 어두워집니다.
        ghost = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        ghost.paste(INK + (SHADOW_ALPHA,),
                    (jx + round(s * SHADOW_OFFSET[0]),
                     jy + round(s * SHADOW_OFFSET[1])), jet)
        img.alpha_composite(ghost)

    # 순백으로 채우면 기체만 그림에서 떠 보입니다. 주황 쪽은 따뜻하게, 파랑 쪽은
    # 차갑게 흐르는 대각 그라디언트로 채워 양쪽 색에 걸치게 하고, 오른쪽 아래
    # 가장자리에만 음영을 넣어 테두리 없이도 형태가 서게 합니다.
    full = Image.new('L', (s, s), 0)
    full.paste(jet, (jx, jy))
    fill = Image.new('RGB', (s, s))
    px = fill.load()
    for y in range(s):
        base = y / (2.0 * s)
        for x in range(0, s, 8):          # 8px 씩 — 픽셀마다 계산하면 느립니다
            t = base + x / (2.0 * s)
            c = tuple(round(a + (b - a) * t) for a, b in zip(JET_FILL_A, JET_FILL_B))
            for k in range(x, min(x + 8, s)):
                px[k, y] = c
    img.paste(fill.convert('RGBA'), (0, 0), full)

    if size >= RING_FROM:
        d = max(round(s * JET_SHADE_WIDTH), 1)
        inner = Image.new('L', (s, s), 0)
        inner.paste(full, (-d, -d))
        band = ImageChops.subtract(full, inner)
        band = band.filter(ImageFilter.GaussianBlur(max(s * JET_SHADE_BLUR, 0.5)))
        band = ImageChops.darker(band, full)      # 실루엣 밖으로 번지지 않게
        band = Image.eval(band, lambda v: v * JET_SHADE_ALPHA // 255)
        img.paste(Image.new('RGBA', (s, s), JET_SHADE + (255,)), (0, 0), band)

    if size >= TEXT_FROM and text:
        # 각 구석이 자기 색 위에서 제 심 이름을 답니다. 두 쪽에 공통인 BIOS 는
        # 기체에 걸치므로 흰 기체와 색 바탕 양쪽에서 읽히도록 외곽선을 씁니다.
        label(img, 'DCS', 0.40, 0.10, 0.12, align='left')
        label(img, 'BMS', 0.40, 0.90, 0.88, align='right', italic=False)
        if led:
            # 브리지가 실제로 하는 일 — 심 상태를 읽어 패널 등을 켭니다.
            on, off = led_grid(s)
            stamp(img, off, LED_OFF)
            stamp(img, on, LED_ON)
        elif lamp:
            stamp(img, led_lamp(s), AMBER)
        elif prompt:
            stamp(img, prompt_mark(s), TERM_GREEN, outline=False, shadow=True)
        elif pixel:
            stamp(img, bios_mark(s), TERM_GREEN, outline=False, shadow=True)
        elif usb:
            # 흰 기체 위에 흰 기호를 올리면 외곽선으로만 버텨 잘 안 보입니다.
            stamp(img, usb_mark(s), INK, outline=False)
        elif wordmark:
            label(img, 'BIOS', 0.34, 0.46, 0.60, stroke=True)

    # 둥근 모서리로 잘라냅니다.
    mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                           radius=round(s * 0.20), fill=255)
    img.putalpha(mask)
    return img.resize((size, size), Image.LANCZOS)


def write_ico(dest, **kw):
    frames = [render(n, **kw) for n in SIZES]
    frames[-1].save(dest, format='ICO',
                    sizes=[(n, n) for n in SIZES], append_images=frames[:-1])
    sys.stderr.write('%s  (%s)\n' % (dest, ', '.join('%d' % n for n in SIZES)))


def main():
    write_ico(DEST)
    write_ico(DEST_PLAIN, wordmark=False)   # BIOS 없이 심 이름만
    write_ico(DEST_USB, usb=True)           # BIOS 대신 USB 기호
    write_ico(DEST_TERM, pixel=True)        # 픽셀 글꼴 BIOS >_
    write_ico(DEST_PROMPT, prompt=True)     # '>_' 만 크게
    write_ico(DEST_LED, led=True)           # 경고등 패널
    write_ico(DEST_LAMP, lamp=True)         # 표시등 하나
    write_ico(DEST_GEAR, gear=True)         # 실제 기어 LED 판
    return 0


if __name__ == '__main__':
    sys.exit(main())
