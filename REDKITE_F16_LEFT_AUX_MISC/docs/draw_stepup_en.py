import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

fig, ax = plt.subplots(1, 1, figsize=(22, 12))
ax.set_xlim(0, 220)
ax.set_ylim(0, 120)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

SDA_C = '#e67e22'; SCL_C = '#2980b9'; V33_C = '#e74c3c'; GND_C = '#1a1a1a'
BLK = '#1a1a1a'; GRN = '#27ae60'; GRY = '#7f8c8d'; LGRY = '#ecf0f1'
PUR = '#8e44ad'; V12_C = '#d35400'

def box(x, y, w, h, label='', sub='', ec='#2c3e50', fc=LGRY):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.8",
                 facecolor=fc, edgecolor=ec, linewidth=2.5))
    if label:
        ly = y+h/2+3 if sub else y+h/2
        ax.text(x+w/2, ly, label, ha='center', va='center',
                fontsize=13, fontweight='bold', color=BLK)
        if sub:
            ax.text(x+w/2, y+h/2-3, sub, ha='center', va='center',
                    fontsize=9, color=GRY)

def sbox(x, y, w, h, label, fc='#f39c12', ec='#2c3e50'):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.2",
                 facecolor=fc, edgecolor=ec, linewidth=1.2))
    ax.text(x+w/2, y+h/2, label, ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')

def ln(pts, c=BLK, w=2, s='-'):
    ax.plot([p[0] for p in pts], [p[1] for p in pts],
            color=c, lw=w, ls=s, solid_capstyle='round', solid_joinstyle='round')

def dot(x, y, c=BLK):
    ax.plot(x, y, 'o', color=c, markersize=5, zorder=5)

def t(x, y, s, c=BLK, fs=11, ha='center', va='center'):
    ax.text(x, y, s, fontsize=fs, color=c, ha=ha, va=va, fontweight='bold')

# ════════════════════════════════════════════════════════════
#  TITLE
# ════════════════════════════════════════════════════════════
t(110, 116, 'Step-Up Converter EN Pin Control via MOSFET', BLK, 16)
t(110, 111, 'USB 3.0 Required (5V 900mA)  |  EN: GND=ON, Float=OFF', GRY, 12)

# ════════════════════════════════════════════════════════════
#  GND BUS (bottom)
# ════════════════════════════════════════════════════════════
GND_Y = 20
ln([(15, GND_Y), (215, GND_Y)], GND_C, 3)
t(10, GND_Y, 'GND', GND_C, 10, 'right')

# ════════════════════════════════════════════════════════════
#  TEENSY 4.1 (left)
# ════════════════════════════════════════════════════════════
box(5, 55, 30, 40, 'TEENSY\n4.1', '')

# 5V output (VIN) → step-up input
ln([(35, 85), (80, 85)], V33_C, 2.5)
t(36, 88, 'VIN (USB 3.0 5V)', V33_C, 9, 'left')

# GPIO pin → MOSFET gate
GPIO_Y = 70
ln([(35, GPIO_Y), (60, GPIO_Y)], PUR, 2.5)
t(36, GPIO_Y+3, 'GPIO Pin', PUR, 9, 'left')

# Teensy GND
ln([(20, 55), (20, GND_Y)], GND_C, 2)
dot(20, GND_Y, GND_C)

# ════════════════════════════════════════════════════════════
#  MOSFET (center-bottom)
# ════════════════════════════════════════════════════════════
MOS_X = 85
MOS_Y = 35
sbox(MOS_X, MOS_Y, 25, 18, 'IRLML6244\nN-ch', '#2c3e50')

# Gate (top, left of center) ← GPIO via 1kΩ
ln([(60, GPIO_Y), (68, GPIO_Y)], PUR, 2)
sbox(68, GPIO_Y-2, 10, 4, '1K', '#e67e22')  # gate series resistor
G_X = MOS_X + 8   # top of MOSFET, left side
D_X = MOS_X + 17  # top of MOSFET, right side (equal spacing)
TOP_Y = MOS_Y + 18
ln([(78, GPIO_Y), (G_X, GPIO_Y), (G_X, TOP_Y)], PUR, 2)
t(G_X-2, TOP_Y+3, 'G', PUR, 9, 'right')

# Source (bottom) → GND
MOS_CX = MOS_X + 12  # center x of MOSFET
ln([(MOS_CX, MOS_Y), (MOS_CX, GND_Y)], GND_C, 2)
dot(MOS_CX, GND_Y, GND_C)
t(MOS_CX+3, MOS_Y-3, 'S', GND_C, 9, 'left')

# Drain (top, right of center) → EN pin
EN_Y = 70
ln([(D_X, TOP_Y), (D_X, EN_Y)], SCL_C, 2)
t(D_X+2, TOP_Y+3, 'D', SCL_C, 9, 'left')

# ════════════════════════════════════════════════════════════
#  STEP-UP CONVERTER (center-right)
# ════════════════════════════════════════════════════════════
STEP_X = 115
STEP_Y = 65
sbox(STEP_X, STEP_Y, 45, 30, 'Step-Up\nModule\n5V → 12V', '#c0392b')

# EN pin (left side, connected to MOSFET drain)
ln([(D_X, EN_Y), (STEP_X, EN_Y)], SCL_C, 2)
t(STEP_X-2, EN_Y+3, 'EN', SCL_C, 9, 'right')

# VIN (left side, top) ← Teensy 5V
ln([(80, 85), (STEP_X, 85)], V33_C, 2.5)
t(STEP_X-2, 85+3, 'VIN', V33_C, 9, 'right')

# GND (bottom)
ln([(137, STEP_Y), (137, GND_Y)], GND_C, 2)
dot(137, GND_Y, GND_C)
t(139, STEP_Y-2, 'GND', GND_C, 8, 'left')

# VOUT = 12V (right side) → LED strip
LED_X = 170
ln([(STEP_X+45, 85), (LED_X, 85)], V12_C, 2.5)
t(STEP_X+47, 88, '12V OUT', V12_C, 10, 'left')

# ════════════════════════════════════════════════════════════
#  LED STRIPS: up to 15 in parallel
# ════════════════════════════════════════════════════════════
# 12V bus line across top
ln([(LED_X, 85), (LED_X + 40, 85)], V12_C, 2.5)

def draw_strip(sx):
    """Draw one LED strip: 12V → LED×3 → 220R → GND"""
    ln([(sx, 85), (sx, 82)], V12_C, 1.5)
    sbox(sx-4, 76, 8, 5, 'LED', '#27ae60')
    ln([(sx, 76), (sx, 74)], GRN, 1.2)
    sbox(sx-4, 68, 8, 5, 'LED', '#27ae60')
    ln([(sx, 68), (sx, 66)], GRN, 1.2)
    sbox(sx-4, 60, 8, 5, 'LED', '#27ae60')
    ln([(sx, 60), (sx, 58)], GRN, 1.2)
    sbox(sx-4, 52, 8, 5, '220R', '#e67e22')
    ln([(sx, 52), (sx, GND_Y)], GND_C, 1.2)
    dot(sx, GND_Y, GND_C)

# Strip 1
draw_strip(LED_X)
# Strip 2
draw_strip(LED_X + 14)
# Dots indicating more strips
t(LED_X + 28, 67, '...', BLK, 14)
t(LED_X + 28, 55, '...', BLK, 14)
# Strip N
draw_strip(LED_X + 40)

# Label
t(LED_X + 20, 90, 'x15 max (parallel)', GRY, 9)

# ════════════════════════════════════════════════════════════
#  OPERATION LABELS
# ════════════════════════════════════════════════════════════
box(5, 2, 100, 14, '', '', '#2c3e50', '#f8f9fa')
t(55, 13, 'OPERATION', BLK, 10)
t(55, 9, 'GPIO HIGH → MOSFET ON → EN=GND → 12V ON', GRN, 8)
t(55, 5, 'GPIO LOW  → MOSFET OFF → EN=Float → 12V OFF', V33_C, 8)

# Parts list
box(115, 2, 90, 14, '', '', '#e67e22', '#fef9f0')
t(160, 13, 'PARTS', '#e67e22', 10)
t(160, 9, 'IRLML6244 (N-ch, Vgs~1V)  |  1K gate series', BLK, 8)
t(160, 5, '220R per LED strip  |  No pull-down (always connected)', BLK, 8)

plt.tight_layout()
out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, 'stepup_en_circuit.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved: {out_path}")
