#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STL 에서 문서용 썸네일 PNG 를 만듭니다.

    python tools/render_stl.py "3d stl/ToggleCover"        폴더 전체
    python tools/render_stl.py "3d stl/ToggleCover/x.stl"  파일 하나

`<이름>.stl` 옆에 `<이름>.png` 를 같은 이름으로 남깁니다. 기존 썸네일과 같은
900 x 700, 음영 + 메시 선 모양입니다.

STEP 은 렌더하지 않습니다 — 모양이 STL 과 같으니 썸네일은 하나면 됩니다.

PIL 과 numpy 가 필요합니다:  pip install pillow numpy
"""
import os
import sys

try:
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit('Pillow 와 numpy 가 필요합니다:  pip install pillow numpy')

SIZE = (900, 700)
SS = 2                         # 수퍼샘플 — 가장자리 계단을 없앱니다
MARGIN = 0.10
FACE = (150, 163, 184)         # 면 바탕색
EDGE = (60, 66, 78)            # 메시 선
LIGHT = np.array([-0.4, -0.5, 0.77])   # 왼쪽 위 앞에서 비추는 빛
YAW, PITCH = 32.0, 22.0        # 보는 각도 (도)


def read_stl(path):
    """이진 STL 에서 삼각형 좌표 (n, 3, 3) 을 읽습니다."""
    with open(path, 'rb') as f:
        head = f.read(84)
        count = int.from_bytes(head[80:84], 'little')
        data = np.frombuffer(f.read(count * 50), dtype=np.uint8)
    if data.size != count * 50:
        raise SystemExit('%s: 삼각형 수가 헤더와 맞지 않습니다' % path)
    # 삼각형 하나는 법선 3 + 정점 9 = 12개 float 와 2바이트 속성입니다.
    chunk = data.reshape(count, 50)[:, 12:48].copy()
    return chunk.view('<f4').reshape(count, 3, 3)


def rotate(tris, yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return tris @ rz.T @ rx.T


def render(path, out):
    tris = rotate(read_stl(path), YAW, PITCH)

    # 화면 좌표로: x 는 오른쪽, z 는 위, y 는 깊이(클수록 멀리).
    w, h = SIZE[0] * SS, SIZE[1] * SS
    pts = tris[:, :, [0, 2]].copy()
    pts[:, :, 1] *= -1
    lo, hi = pts.reshape(-1, 2).min(axis=0), pts.reshape(-1, 2).max(axis=0)
    span = np.maximum(hi - lo, 1e-6)
    scale = min(w * (1 - 2 * MARGIN) / span[0], h * (1 - 2 * MARGIN) / span[1])
    offset = np.array([w, h]) / 2 - (lo + hi) / 2 * scale
    screen = pts * scale + offset

    # 면 법선과 밝기. 보는 쪽을 등진 면은 그리지 않습니다.
    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    normals = np.cross(e1, e2)
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.maximum(length, 1e-9)
    facing = normals[:, 1] < 0
    shade = np.clip(normals @ LIGHT, 0, 1) * 0.55 + 0.45

    # 뒤에서 앞으로 (화가 알고리즘). 깊이는 삼각형 중심의 y.
    depth = tris[:, :, 1].mean(axis=1)
    order = np.argsort(-depth)

    img = Image.new('RGB', (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    line = max(round(SS * 0.9), 1)
    for i in order:
        if not facing[i]:
            continue
        poly = [tuple(p) for p in screen[i]]
        c = tuple(int(v * shade[i]) for v in FACE)
        d.polygon(poly, fill=c, outline=EDGE, width=line)

    img = img.resize(SIZE, Image.LANCZOS).convert('RGBA')
    img.save(out)
    return img.size


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    target = sys.argv[1]
    files = ([target] if target.lower().endswith('.stl') else
             [os.path.join(target, n) for n in sorted(os.listdir(target))
              if n.lower().endswith('.stl')])
    if not files:
        raise SystemExit('STL 을 찾지 못했습니다: %s' % target)
    for f in files:
        out = f[:-4] + '.png'
        size = render(f, out)
        sys.stderr.write('%s  %s\n' % (out, size))
    return 0


if __name__ == '__main__':
    sys.exit(main())
