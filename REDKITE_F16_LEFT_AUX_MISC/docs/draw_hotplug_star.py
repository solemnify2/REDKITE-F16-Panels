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
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

SDA_C = '#e67e22'; SCL_C = '#2980b9'; V33_C = '#e74c3c'; GND_C = '#1a1a1a'
BLK = '#1a1a1a'; GRN = '#27ae60'; GRY = '#7f8c8d'; LGRY = '#ecf0f1'

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
t(150, 196, 'Teensy 4.1 — MCP23017 x4  Star Topology', BLK, 16)
t(150, 191, 'I2C Star Bus + Hotplug + Pull-up', GRY, 12)

BRANCH_BASE = [152, 112, 72, 32]

# ════════════════════════════════════════════════════════════
#  TEENSY
# ════════════════════════════════════════════════════════════
box(5, 78, 25, 44, 'TEENSY\n4.1', 'Master')

# Teensy outputs (wider spacing for pull-up room)
Y_SDA = 114; Y_SCL = 106; Y_33V = 96; Y_GND = 88

ln([(30, Y_SDA), (65, Y_SDA)], SDA_C, 2.5)
ln([(30, Y_SCL), (65, Y_SCL)], SCL_C, 2.5)
ln([(30, Y_33V), (65, Y_33V)], V33_C, 2.5)
ln([(30, Y_GND), (65, Y_GND)], GND_C, 2.5)

t(31, Y_SDA+3, 'Pin18', SDA_C, 8, 'left')
t(31, Y_SCL+3, 'Pin19', SCL_C, 8, 'left')
t(31, Y_33V+3, '3.3V', V33_C, 8, 'left')
t(31, Y_GND+3, 'GND', GND_C, 8, 'left')

# ════════════════════════════════════════════════════════════
#  PULL-UPS between Teensy and split (x=38~58)
# ════════════════════════════════════════════════════════════
# 4.7K SDA→3.3V at x=40: between SDA(114) and SCL(106)
PU1 = 40
dot(PU1, Y_SDA, SDA_C)
ln([(PU1, Y_SDA), (PU1, Y_SDA-2)], SDA_C, 1.5)
sbox(PU1-5, Y_SDA-6, 10, 4, '4.7K', '#c0392b')  # box from 108 to 112 (between SDA 114 and SCL 106)
ln([(PU1, Y_SDA-6), (PU1, Y_33V)], V33_C, 1.5)
dot(PU1, Y_33V, V33_C)

# 4.7K SCL→3.3V at x=48: between SCL(106) and 3.3V(96)
PU2 = 48
dot(PU2, Y_SCL, SCL_C)
ln([(PU2, Y_SCL), (PU2, Y_SCL-2)], SCL_C, 1.5)
sbox(PU2-5, Y_SCL-6, 10, 4, '4.7K', '#c0392b')  # box from 100 to 104 (between SCL 106 and 3.3V 96)
ln([(PU2, Y_SCL-6), (PU2, Y_33V)], V33_C, 1.5)
dot(PU2, Y_33V, V33_C)

# 10µF 3.3V→GND at x=56
dot(56, Y_33V, V33_C)
ln([(56, Y_33V), (56, Y_33V-2)], V33_C, 1.5)
sbox(51, Y_33V-6, 10, 4, '10uF', '#d35400')
ln([(56, Y_33V-6), (56, Y_GND)], GND_C, 1.5)
dot(56, Y_GND, GND_C)
t(50, Y_33V-7, '+', V33_C, 7, 'right')

# ════════════════════════════════════════════════════════════
#  VERTICAL BUS BARS (split point, x=65)
# ════════════════════════════════════════════════════════════
BAR_SDA = 65; BAR_SCL = 69; BAR_33V = 73; BAR_GND = 77

top_y = BRANCH_BASE[0] + 22
bot_y = BRANCH_BASE[3] + 2
ln([(BAR_SDA, top_y), (BAR_SDA, bot_y)], SDA_C, 3)
ln([(BAR_SCL, top_y), (BAR_SCL, bot_y)], SCL_C, 3)
ln([(BAR_33V, top_y), (BAR_33V, bot_y)], V33_C, 3)
ln([(BAR_GND, top_y), (BAR_GND, bot_y)], GND_C, 3)

t(BAR_SDA, top_y+4, 'SDA', SDA_C, 9)
t(BAR_SCL, top_y+4, 'SCL', SCL_C, 9)
t(BAR_33V, top_y+4, '3.3V', V33_C, 9)
t(BAR_GND, top_y+4, 'GND', GND_C, 9)

# ════════════════════════════════════════════════════════════
#  4 BRANCHES
# ════════════════════════════════════════════════════════════
MCP_ADDRS = ['0x20', '0x21', '0x22', '0x23']
MCP_COLORS = ['#27ae60', '#2980b9', '#8e44ad', '#c0392b']
PANEL_NAMES = ['Panel 1', 'Panel 2', 'Panel 3', 'Panel 4']

MCP_X = 240; MCP_W = 30; MCP_H = 24
COMP_X = 218  # component column (100R + 100nF, same x)

for i, (by, addr, mc, pname) in enumerate(zip(BRANCH_BASE, MCP_ADDRS, MCP_COLORS, PANEL_NAMES)):
    sda = by + 22; scl = by + 16; v33 = by + 8; gnd = by + 2

    # Tap dots on bars
    dot(BAR_SDA, sda, SDA_C); dot(BAR_SCL, scl, SCL_C)
    dot(BAR_33V, v33, V33_C); dot(BAR_GND, gnd, GND_C)

    # Horizontal lines to component column / MCP
    ln([(BAR_SDA, sda), (COMP_X, sda)], SDA_C, 1.8)
    ln([(BAR_SCL, scl), (COMP_X, scl)], SCL_C, 1.8)
    ln([(BAR_33V, v33), (MCP_X, v33)], V33_C, 1.8)
    ln([(BAR_GND, gnd), (MCP_X, gnd)], GND_C, 1.8)

    # Hotplug connector point (x=83, between split and LAN)
    conn_x = 83
    for sig_y, sig_c in [(sda, SDA_C), (scl, SCL_C), (v33, V33_C), (gnd, GND_C)]:
        ax.plot(conn_x, sig_y, 'x', color=sig_c, markersize=7, markeredgewidth=2.5, zorder=5)
    if i == 0:
        t(conn_x, top_y + 8, 'HOTPLUG\nCONNECTOR', GRY, 7)

    # LAN cable box
    ax.add_patch(FancyBboxPatch((88, by-1), 117, 27, boxstyle="round,pad=0.5",
                 facecolor='none', edgecolor=GRY, linewidth=1, linestyle='--'))
    t(146, by+27, f'LAN Cat5e  #{i+1}', GRY, 9)

    # Signal labels inside LAN
    t(105, sda, 'SDA', SDA_C, 9); t(105, scl, 'SCL', SCL_C, 9)
    t(105, v33, '3.3V', V33_C, 9); t(105, gnd, 'GND', GND_C, 9)

    # 100R on SDA/SCL (at COMP_X)
    sbox(COMP_X, sda-2, 10, 4, '100R', '#e67e22')
    ln([(COMP_X+10, sda), (MCP_X, sda)], SDA_C, 1.8)
    sbox(COMP_X, scl-2, 10, 4, '100R', '#e67e22')
    ln([(COMP_X+10, scl), (MCP_X, scl)], SCL_C, 1.8)

    # 100nF between 3.3V and GND (same column COMP_X, above GND line)
    cap_cx = COMP_X + 7
    cap_bot = gnd + 1.5  # 1.5 above GND
    cap_top = cap_bot + 3  # 3-unit tall box → top at gnd+4.5, 3.5 below v33
    dot(cap_cx, v33, V33_C)
    ln([(cap_cx, v33), (cap_cx, cap_top)], V33_C, 1.5)
    sbox(cap_cx-5, cap_bot, 10, 3, '100nF', '#2980b9')
    ln([(cap_cx, cap_bot), (cap_cx, gnd)], GND_C, 1.5)
    dot(cap_cx, gnd, GND_C)

    # MCP23017
    sbox(MCP_X, by, MCP_W, MCP_H, f'MCP23017\n{addr}', mc)
    t(MCP_X + MCP_W/2, by - 4, pname, GRY, 10)

    # RESET pin → VDD: short stub on left side between SCL and 3.3V lines
    rst_y = (scl + v33) / 2  # midpoint between SCL and 3.3V
    ln([(MCP_X, rst_y), (MCP_X - 6, rst_y)], V33_C, 1.5)
    t(MCP_X - 8, rst_y, 'RST', V33_C, 7, 'right')
    # connect to 3.3V line
    ln([(MCP_X - 6, rst_y), (MCP_X - 6, v33)], V33_C, 1.5)
    dot(MCP_X - 6, v33, V33_C)

    # GPIO outputs: 16 wires fanning out from MCP right side
    gpio_start = MCP_X + MCP_W
    gpio_end = gpio_start + 15
    for j in range(16):
        gy = by + 2 + j * (MCP_H - 4) / 15  # spread across MCP height
        ln([(gpio_start, gy), (gpio_end, gy)], GRN, 0.8)
    t(gpio_end + 2, by + MCP_H/2, '16\nGPIO', GRN, 10, 'left')

# ════════════════════════════════════════════════════════════
#  LEGEND
# ════════════════════════════════════════════════════════════
box(235, 3, 55, 24, '', '', '#2c3e50', '#f8f9fa')
t(262, 24, 'SIGNAL COLORS', BLK, 11)
ln([(238, 20), (248, 20)], SDA_C, 3); t(253, 20, 'SDA', SDA_C, 10, 'left')
ln([(238, 16), (248, 16)], SCL_C, 3); t(253, 16, 'SCL', SCL_C, 10, 'left')
ln([(238, 12), (248, 12)], V33_C, 3); t(253, 12, '3.3V', V33_C, 10, 'left')
ln([(238, 8), (248, 8)], GND_C, 3); t(253, 8, 'GND', GND_C, 10, 'left')

# ════════════════════════════════════════════════════════════
#  ANNOTATION
# ════════════════════════════════════════════════════════════
box(5, 3, 150, 26, '', '', '#e67e22', '#fef9f0')
t(80, 26, 'STAR BUS — HOTPLUG PROTECTION', '#e67e22', 12)
t(80, 21, '100R x2 per branch : SDA, SCL series — near MCP', BLK, 9)
t(80, 16, '4.7K x2 : SDA, SCL pull-up — between Teensy & split', BLK, 9)
t(80, 11, '10uF x1 : bulk cap  |  100nF x4 : bypass per MCP', '#c0392b', 9)
t(80, 6, 'RESET pin : tie to VDD (3.3V) — do not float', V33_C, 9)

box(160, 3, 60, 24, '', '', GRN, '#f0faf0')
t(190, 19, '4 x MCP23017', GRN, 11)
t(190, 10, '= 64 GPIO', GRN, 13)

plt.tight_layout()
out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, 'hotplug_wiring_star.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved: {out_path}")
