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
분할과 판만 남기고 글자를 뺍니다 — 색 두 개와 모양은 그 크기에서도 읽힙니다.

가운데 그림은 **실제 패널의 기어 LED 판**입니다 (`GearLedLayout.dxf`). 그 자체가
위에서 본 기체 모양이고, 켜진 LED 세 개가 브리지가 하는 일을 그대로 보여 줍니다.
그리다 만 F-16 실루엣을 쓰던 때가 있었는데, 실물 도면이 있으니 그쪽이 낫습니다.

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
GEAR_DXF = os.path.join(HERE, os.pardir, 'docs', 'GearLedLayout.dxf')
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
SHADOW_OFFSET = (-0.035, -0.010)
SHADOW_ALPHA = 130
GEAR_ART = (178, 242, 196)       # 패널 각인선 — 실물처럼 녹색을 띱니다
GEAR_GLOW = (120, 255, 150)      # LED 번짐
GEAR_LED = (60, 230, 90)         # LED 몸통 (진한 녹색)
GEAR_CORE = (200, 255, 210)      # LED 한가운데 밝은 심
TILT = -32                       # 기어 판을 눕히는 각도

def gradient(size, top, bottom):
    """위에서 아래로 흐르는 세로 그라디언트."""
    img = Image.new('RGB', (1, size))
    px = img.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        px[0, y] = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
    return img.resize((size, size), Image.BILINEAR)


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


def render(size, text=True, wordmark=True):
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

    big = size < TEXT_FROM
    art, leds = gear_marks(s, 0.80 if big else 0.70,
                           (0.50, 0.50) if big else JET_CENTER)

    if size >= RING_FROM:
        # BMS-BIOS.ico 가 기체 뒤에 두던 그림자. 가는 선뿐이라 멀리 떼면 그림자가
        # 아니라 흩어진 복제본으로 보여, 바짝 붙입니다.
        ghost = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        ghost.paste(INK + (SHADOW_ALPHA,),
                    (round(s * SHADOW_OFFSET[0]), round(s * SHADOW_OFFSET[1])), art)
        img.alpha_composite(ghost)

    # 가는 선이 바탕에 붙어 보이므로 바로 뒤에 짧은 그림자를 둡니다.
    drop = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    drop.paste(INK + (160,), (round(s * 0.006), round(s * 0.006)), art)
    img.alpha_composite(drop)

    img.paste(Image.new('RGBA', (s, s), GEAR_ART + (255,)), (0, 0), art)

    # 켜진 LED — 넓게 번지는 빛, 그 안에 진한 녹색, 가운데에 밝은 심.
    # 사진의 램프가 이 순서로 밝아집니다.
    if size >= RING_FROM:
        for blur, alpha in ((0.042, 120), (0.017, 205)):
            bloom = leds.filter(ImageFilter.GaussianBlur(s * blur))
            bloom = Image.eval(bloom, lambda v, a=alpha: v * a // 255)
            img.paste(Image.new('RGBA', (s, s), GEAR_GLOW + (255,)), (0, 0), bloom)
    img.paste(Image.new('RGBA', (s, s), GEAR_LED + (255,)), (0, 0), leds)
    core = leds.filter(ImageFilter.MinFilter(max(round(s * 0.016), 1) * 2 + 1))
    img.paste(Image.new('RGBA', (s, s), GEAR_CORE + (255,)), (0, 0), core)

    if size >= TEXT_FROM and text:
        # 각 구석이 자기 색 위에서 제 심 이름을 답니다.
        label(img, 'DCS', 0.40, 0.10, 0.12, align='left')
        label(img, 'BMS', 0.40, 0.90, 0.88, align='right', italic=False)
        if wordmark:
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
    write_ico(DEST)                         # BIOS 워드마크 포함
    write_ico(DEST_PLAIN, wordmark=False)   # 심 이름만
    return 0


if __name__ == '__main__':
    sys.exit(main())
