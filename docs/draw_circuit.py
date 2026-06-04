import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

fig, ax = plt.subplots(1, 1, figsize=(30, 20))
ax.set_xlim(0, 300)
ax.set_ylim(0, 200)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# Colors
RED = '#ff6b6b'
BLUE = '#4dabf7'
YEL = '#ffd43b'
GRN = '#51cf66'
PUR = '#da77f2'
WHT = '#e9ecef'
GRY = '#868e96'
DRK = '#1e2430'
BDR = '#495057'
ORG = '#ff922b'
CYA = '#22b8cf'

def box(x, y, w, h, label='', sub='', ec=BDR, fc=DRK):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.8",
                 facecolor=fc, edgecolor=ec, linewidth=2.5))
    if label:
        ly = y+h/2+3 if sub else y+h/2
        ax.text(x+w/2, ly, label, ha='center', va='center',
                fontsize=13, fontweight='bold', color=WHT)
        if sub:
            ax.text(x+w/2, y+h/2-3, sub, ha='center', va='center',
                    fontsize=9, color=GRY)

def sbox(x, y, w, h, label, fc=ORG):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.2",
                 facecolor=fc, edgecolor='white', linewidth=1.2))
    ax.text(x+w/2, y+h/2, label, ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')

def ln(pts, c=WHT, w=2, s='-'):
    ax.plot([p[0] for p in pts], [p[1] for p in pts],
            color=c, lw=w, ls=s, solid_capstyle='round', solid_joinstyle='round')

def dot(x, y, c=WHT):
    ax.plot(x, y, 'o', color=c, markersize=6, zorder=5)

def t(x, y, s, c=WHT, fs=11, ha='center', va='center'):
    ax.text(x, y, s, fontsize=fs, color=c, ha=ha, va=va, fontweight='bold')

def arr(x1, y1, x2, y2, c=WHT, w=2):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color=c, lw=w))

def leds(x, y):
    for i in range(3):
        ax.add_patch(plt.Circle((x+i*5.5, y), 2.2, color=GRN, alpha=0.85, zorder=3))
        ax.text(x+i*5.5, y, 'L', fontsize=7, ha='center', va='center',
                color='#1a1a1a', fontweight='bold')

# ════════════════════════════════════════════════════════════
#  TITLE
# ════════════════════════════════════════════════════════════
t(150, 197, 'REDKITE F16 PANELS — Backlight Circuit', WHT, 18)
t(150, 193, 'USB 3.0 5V → MT3608 12V → IRLML6244 PWM Dimming → 3-Series LED (220Ω)', GRY, 10)

# ════════════════════════════════════════════════════════════
#  POWER CHAIN (y=175~188)
# ════════════════════════════════════════════════════════════
box(15, 175, 28, 14, 'PC USB 3.0', '5V/900mA')
box(60, 175, 38, 14, 'TEENSY 4.1', 'Pin0=PWM, Pin18/19=I2C')
box(120, 178, 24, 10, 'MT3608', '5V→12V')

arr(43, 182, 60, 182, RED, 2.5)
t(52, 185, '5V', RED, 10)
arr(98, 185, 120, 185, RED, 2.5)
t(109, 188, 'VIN', RED, 9)
arr(144, 183, 160, 183, RED, 2.5)
t(155, 186, '12V', RED, 12)

# ════════════════════════════════════════════════════════════
#  12V BUS (y=168)
# ════════════════════════════════════════════════════════════
ln([(160, 183), (160, 168)], RED, 3)
ln([(15, 168), (285, 168)], RED, 4)
t(150, 171, '12V BUS', RED, 11)

# ════════════════════════════════════════════════════════════
#  GND BUS (y=22)
# ════════════════════════════════════════════════════════════
ln([(15, 22), (285, 22)], BLUE, 4)
t(150, 19, 'GND BUS', BLUE, 11)

# ════════════════════════════════════════════════════════════
#  Teensy outputs going DOWN
#  - PWM: x=80 vertical trunk
#  - SDA: x=88 vertical
#  - SCL: x=92 vertical
# ════════════════════════════════════════════════════════════

# PWM from Teensy down to y=168, then continue down
ln([(80, 175), (80, 168)], YEL, 2.5)
dot(80, 168, YEL)
t(82, 172, 'PWM', YEL, 8, 'left')

# PWM trunk: y=168 → y=55 (between panels, left of LAN)
ln([(80, 168), (80, 55)], YEL, 2.5)

# SDA from Teensy (Pin18) → down into LAN Pin 1 (y=145)
ln([(88, 175), (88, 145)], YEL, 1.5, '--')
t(86, 172, 'SDA', YEL, 7, 'right')

# SCL from Teensy (Pin19) → down into LAN Pin 3 (y=125)
ln([(92, 175), (92, 125)], YEL, 1.5, '--')
t(94, 172, 'SCL', YEL, 7, 'left')

# ════════════════════════════════════════════════════════════
#  MAIN PANEL (x=5~75, y=26~165)
# ════════════════════════════════════════════════════════════
box(5, 26, 72, 139, '', '', CYA, '#0d1620')
t(41, 162, 'MAIN PANEL', CYA, 15)
t(41, 157, '10 strips × (220Ω + 3 LEDs)', GRY, 9)

# 12V enters panel
ln([(35, 168), (35, 150)], RED, 2.5)
dot(35, 168, RED)

# Vertical 12V rail inside panel (x=15)
ln([(15, 150), (35, 150)], RED, 2)
ln([(15, 75), (15, 150)], RED, 2)

# LED strips
for i in range(5):
    y = 145 - i * 14
    ln([(15, y), (18, y)], RED, 1.5)
    sbox(18, y-2.5, 12, 5, '220Ω')
    leds(34, y)
    ln([(30, y), (31.8, y)], GRN, 1.5)
    ln([(45.2, y), (50, y)], PUR, 1.5)

t(55, 145, '×10', GRY, 12, 'left')

# Drain bus (x=50, vertical)
ln([(50, 72), (50, 145)], PUR, 2)
t(52, 108, 'D', PUR, 8, 'left')

# ──── MOSFET 1 (x=25~49, y=40~56) ────
#  G=left, D=top, S=bottom
box(25, 40, 24, 16, 'MOSFET 1', 'IRLML6244', '#e03131', '#3a1010')

# Drain: from drain bus down to MOSFET top
ln([(50, 72), (50, 62), (42, 62), (42, 56)], PUR, 2)
t(52, 67, 'D', PUR, 8, 'left')

# Source: MOSFET bottom to GND bus
ln([(42, 40), (42, 22)], BLUE, 2.5)
dot(42, 22, BLUE)
t(44, 32, 'S', BLUE, 8, 'left')

# Gate: from PWM trunk (x=80) leftward to MOSFET gate
#  PWM trunk at x=80, branch at y=48
ln([(80, 48), (70, 48)], YEL, 2)
sbox(60, 46, 10, 5, '220Ω')
ln([(60, 48), (49, 48)], YEL, 2)
dot(80, 48, YEL)
t(27, 48, 'G', YEL, 8, 'right')

# Pull-down: Gate → 10kΩ → GND
# branch down from gate wire at x=52
dot(52, 48, YEL)
ln([(52, 48), (52, 35)], YEL, 1.5)
sbox(48, 30, 10, 5, '10kΩ', '#495057')
ln([(52, 30), (52, 22)], BLUE, 1.5)
dot(52, 22, BLUE)

# ════════════════════════════════════════════════════════════
#  LAN CABLE (x=85~115, y=26~165)
# ════════════════════════════════════════════════════════════
box(85, 26, 32, 139, '', '', '#2f6878', '#0d1a20')
t(101, 162, 'LAN CABLE', WHT, 14)
t(101, 157, 'Cat5e RJ45', GRY, 9)

# Pin labels — left column (odd pins), right column (even pins)
pair_data = [
    ('Pair 1', 145, '1:SDA', YEL, '2:GND', BLUE),
    ('Pair 2', 125, '3:SCL', YEL, '6:GND', BLUE),
    ('Pair 3', 105, '4:12V', RED, '5:12V', RED),
    ('Pair 4', 85,  '7:PWM', YEL, '8:GND', BLUE),
]
for pair, y, l1, c1, l2, c2 in pair_data:
    t(101, y+6, pair, '#555555', 7)
    t(93, y, l1, c1, 9, 'left')
    t(107, y, l2, c2, 9, 'left')

# ── LAN connections (left side = from Teensy) ──

# 12V: from 12V bus into LAN
ln([(101, 168), (101, 165)], RED, 2)
dot(101, 168, RED)

# PWM: from PWM trunk (x=80) into LAN
ln([(80, 88), (85, 88)], YEL, 2, '--')
dot(80, 88, YEL)

# GND: from GND bus into LAN
ln([(101, 22), (101, 26)], BLUE, 2)
dot(101, 22, BLUE)

# ── LAN connections (right side = to MISC) ──
# These exit at x=117

# SDA out (y=145)
ln([(117, 145), (125, 145)], YEL, 1.5, '--')
# SCL out (y=125)
ln([(117, 125), (125, 125)], YEL, 1.5, '--')
# 12V out (y=105)
ln([(117, 105), (125, 105)], RED, 2)
# PWM out (y=85)
ln([(117, 85), (125, 85)], YEL, 2, '--')
# GND out (y=65)
ln([(117, 65), (125, 65)], BLUE, 1.5, '--')

# ════════════════════════════════════════════════════════════
#  MISC PANEL (x=125~285, y=26~165)
# ════════════════════════════════════════════════════════════
box(125, 26, 160, 139, '', '', CYA, '#0d1620')
t(205, 162, 'MISC PANEL', CYA, 15)
t(205, 157, 'MCP23017 + AMS1117 + 5 strips (15 LEDs)', GRY, 9)

# ── MISC top area: I2C protection → AMS1117 → MCP23017 ──
# --- I2C SDA line (y=150) ---
ln([(125, 145), (132, 145)], YEL, 1.5, '--')
ln([(132, 145), (132, 150)], YEL, 1.5)
t(130, 152, 'SDA', YEL, 8)
sbox(136, 148, 12, 5, '100Ω')
ln([(148, 150), (165, 150)], YEL, 2)

# --- I2C SCL line (y=142) ---
ln([(125, 125), (128, 125)], YEL, 1.5, '--')
ln([(128, 125), (128, 142)], YEL, 1.5)
t(130, 139, 'SCL', YEL, 8)
sbox(136, 140, 12, 5, '100Ω')
ln([(148, 142), (165, 142)], YEL, 2)

# --- MCP23017 ---
sbox(165, 138, 25, 18, 'MCP23017\n0x20', '#2b8a3e')
# MCP GND
ln([(190, 138), (195, 138)], BLUE, 1.5)
ln([(195, 138), (195, 22)], BLUE, 1.5)
dot(195, 22, BLUE)
t(197, 130, 'GND', BLUE, 7, 'left')

# --- Power: 12V from LAN → branch to strips & AMS1117 ---
ln([(125, 105), (130, 105)], RED, 2)
ln([(130, 105), (130, 133)], RED, 2)
dot(130, 105, RED)

# Branch right to LED strip 12V rail at x=145
ln([(130, 118), (145, 118)], RED, 1.5)
dot(130, 118, RED)

# Branch right to AMS1117 at y=133
ln([(130, 133), (205, 133)], RED, 2)
dot(130, 133, RED)

# 10µF input cap
sbox(208, 126, 10, 5, '10µF', '#3498db')
ln([(213, 133), (213, 131)], RED, 1.5)
ln([(213, 126), (213, 22)], BLUE, 1.5)
dot(213, 22, BLUE)

# AMS1117
sbox(220, 131, 22, 5, 'AMS1117-3.3', PUR)
ln([(205, 133), (220, 133)], RED, 1.5)

# 10µF output cap
sbox(248, 126, 10, 5, '10µF', '#3498db')
ln([(253, 133), (253, 131)], PUR, 1.5)
ln([(253, 126), (253, 22)], BLUE, 1.5)
dot(253, 22, BLUE)

ln([(242, 133), (248, 133)], PUR, 1.5)

# 3.3V to MCP VDD
ln([(253, 133), (260, 133)], PUR, 2)
ln([(260, 133), (260, 148)], PUR, 1.5)
ln([(260, 148), (190, 148)], PUR, 1.5)
t(255, 136, '3.3V', PUR, 9)

# ── LED Strips (middle area, y=82~118) ──

# 12V vertical rail for strips
ln([(145, 82), (145, 118)], RED, 2)

for i in range(5):
    y = 118 - i * 9
    ln([(145, y), (150, y)], RED, 1.5)
    sbox(150, y-2.5, 12, 5, '220Ω')
    leds(166, y)
    ln([(162, y), (163.8, y)], GRN, 1.5)
    ln([(177.2, y), (182, y)], PUR, 1.5)

t(185, 118, '×5', GRY, 12, 'left')

# Drain bus (x=182, vertical)
ln([(182, 68), (182, 118)], PUR, 2)
t(184, 95, 'D', PUR, 8, 'left')

# ──── MOSFET 2 (x=160~184, y=40~56) ────
box(160, 40, 24, 16, 'MOSFET 2', 'IRLML6244', '#e03131', '#3a1010')

# Drain: from drain bus down to MOSFET top
ln([(182, 68), (182, 62), (177, 62), (177, 56)], PUR, 2)
t(184, 65, 'D', PUR, 8, 'left')

# Source: MOSFET bottom to GND bus
ln([(177, 40), (177, 22)], BLUE, 2.5)
dot(177, 22, BLUE)
t(179, 32, 'S', BLUE, 8, 'left')

# Gate: from LAN PWM to MOSFET gate
ln([(125, 85), (135, 85)], YEL, 2, '--')
ln([(135, 85), (135, 48)], YEL, 2)
ln([(135, 48), (150, 48)], YEL, 2)
sbox(150, 46, 10, 5, '220Ω')
ln([(160, 48), (160, 48)], YEL, 2)
t(162, 48, 'G', YEL, 8, 'right')

# Pull-down: Gate → 10kΩ → GND
dot(155, 48, YEL)
ln([(155, 48), (155, 35)], YEL, 1.5)
sbox(151, 30, 10, 5, '10kΩ', '#495057')
ln([(155, 30), (155, 22)], BLUE, 1.5)
dot(155, 22, BLUE)

# GND from LAN
ln([(125, 65), (130, 65)], BLUE, 1.5, '--')
ln([(130, 65), (130, 22)], BLUE, 1.5)
dot(130, 22, BLUE)

# ════════════════════════════════════════════════════════════
#  LEGENDS (bottom strip, y=2~16)
# ════════════════════════════════════════════════════════════

# Legend 1: LAN
box(5, 2, 75, 16, '', '', BDR, DRK)
t(42, 15, 'LAN TWISTED PAIRS', WHT, 11)
for i, (pair, sig, c) in enumerate([
    ('Pair1 (Org):', 'SDA+GND', YEL),
    ('Pair2 (Grn):', 'SCL+GND', YEL),
    ('Pair3 (Blu):', '12V+12V', RED),
    ('Pair4 (Brn):', 'PWM+GND', YEL),
]):
    x = 8 if i < 2 else 45
    y = 10 - (i % 2) * 4
    t(x, y, pair, GRY, 8, 'left')
    t(x+18, y, sig, c, 8, 'left')

# Legend 2: Specs
box(90, 2, 85, 16, '', '', BDR, DRK)
t(132, 15, 'SPECIFICATIONS', WHT, 11)
for i, s in enumerate([
    'Main: 10 strips (30 LEDs) = 200mA',
    'MISC: 5 strips (15 LEDs) = 100mA',
    'Total 12V: 300mA (3.6W)',
    'USB 3.0: 900mA → 5V ~540mA → OK',
]):
    t(95, 10 - i*2.5, s, GRY if i > 1 else WHT, 8, 'left')

# Legend 3: MOSFET
box(185, 2, 100, 16, '', '', BDR, DRK)
t(235, 15, 'MOSFET IRLML6244 (SOT-23) ×2', WHT, 11)
for i, (pin, desc, c) in enumerate([
    ('G (Gate):', 'PWM → 220Ω → G', YEL),
    ('D (Drain):', 'LED cathode(−)', PUR),
    ('S (Source):', 'GND', BLUE),
    ('Pull-down:', '10kΩ G→GND', GRY),
]):
    x = 190 if i < 2 else 245
    y = 10 - (i % 2) * 4
    t(x, y, pin, c, 8, 'left')
    t(x+16, y, desc, WHT, 8, 'left')

plt.tight_layout()
out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, 'backlight_circuit.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#0d1117')
print(f"Saved: {out_path}")
