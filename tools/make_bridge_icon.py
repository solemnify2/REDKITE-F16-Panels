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
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit('Pillow 가 필요합니다:  pip install pillow')

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, 'bridge.ico')
DEST_PLAIN = os.path.join(HERE, 'bridge-plain.ico')
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
JET_SCALE = 0.70

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
    m = m.rotate(-32, resample=Image.BICUBIC, expand=True)
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

        ring = max(round(s * 0.012), 1)
        shade = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):
                if dx * dx + dy * dy <= ring * ring:
                    shade.paste(INK + (150,), (jx + dx, jy + dy), jet)
        img.alpha_composite(shade)
    img.paste((255, 255, 255, 255), (jx, jy), jet)

    if size >= TEXT_FROM and text:
        # 각 구석이 자기 색 위에서 제 심 이름을 답니다. 두 쪽에 공통인 BIOS 는
        # 기체에 걸치므로 흰 기체와 색 바탕 양쪽에서 읽히도록 외곽선을 씁니다.
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
    write_ico(DEST)
    write_ico(DEST_PLAIN, wordmark=False)   # BIOS 없이 심 이름만
    return 0


if __name__ == '__main__':
    sys.exit(main())
