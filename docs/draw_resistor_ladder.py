"""Generate resistor ladder circuit diagram for rotary switch → analog pin."""
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.set_xlim(0, 400)
ax.set_ylim(0, 250)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Resistor Ladder — Rotary Switch to Analog Pin', fontsize=14, fontweight='bold', pad=15)

# Colors
C_WIRE = '#333333'
C_RES = '#CC6600'
C_SW = '#2266AA'
C_TEENSY = '#44AA44'
C_GND = '#888888'

# ---- Rotary switch box ----
sw_x, sw_y, sw_w, sw_h = 30, 80, 100, 140
ax.add_patch(patches.FancyBboxPatch((sw_x, sw_y), sw_w, sw_h, boxstyle="round,pad=5",
             facecolor='#DDEEFF', edgecolor=C_SW, linewidth=2))
ax.text(sw_x + sw_w/2, sw_y + sw_h + 8, 'Rotary Switch', ha='center', fontsize=11, fontweight='bold', color=C_SW)
ax.text(sw_x + sw_w/2, sw_y + sw_h - 5, '(6-pos example)', ha='center', fontsize=8, color=C_SW)

# Switch positions (COM at bottom, positions 1-6 going up)
positions = 6
pos_labels = ['COM', 'Pos 1', 'Pos 2', 'Pos 3', 'Pos 4', 'Pos 5', 'Pos 6']
pos_ys = []
for i in range(positions + 1):
    y = sw_y + 10 + i * (sw_h - 20) / positions
    pos_ys.append(y)
    label = pos_labels[i]
    ax.text(sw_x + 10, y, label, ha='left', va='center', fontsize=8, color=C_SW)
    # Pin dot
    ax.plot(sw_x + sw_w, y, 'o', color=C_SW, markersize=4, zorder=5)

# ---- Resistor chain (1kΩ each) ----
chain_x = sw_x + sw_w  # start from switch right edge
res_x_start = 160
res_x_end = 200

# COM connects to pulldown and analog pin line
com_y = pos_ys[0]
# Horizontal bus line from COM to right
bus_x_end = 350
ax.plot([chain_x, bus_x_end], [com_y, com_y], color=C_WIRE, linewidth=2)

# Each position connects through cumulative 1kΩ resistors
for i in range(1, positions + 1):
    py = pos_ys[i]
    # Horizontal line from switch to resistor chain junction
    jx = res_x_start + (i - 1) * 30  # junction x position

    # Draw horizontal line from switch pin
    ax.plot([chain_x, jx], [py, py], color=C_WIRE, linewidth=1.5)

    # Draw 1kΩ resistor symbol (zigzag simplified as box)
    rx1 = jx - 10
    rx2 = jx + 10
    ry = py
    ax.add_patch(patches.FancyBboxPatch((rx1, ry - 5), 20, 10, boxstyle="round,pad=1",
                 facecolor='#FFEECC', edgecolor=C_RES, linewidth=1.5))
    ax.text(jx, ry, '1kΩ', ha='center', va='center', fontsize=6, fontweight='bold', color=C_RES)

    # Vertical line down to bus
    ax.plot([jx, jx], [py - 5, com_y], color=C_WIRE, linewidth=1, linestyle='--', alpha=0.3)

# ---- Simplified: show series chain instead ----
# Clear and redraw with proper series chain
ax.clear()
ax.set_xlim(0, 480)
ax.set_ylim(0, 280)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Resistor Ladder — Rotary Switch to Analog Pin', fontsize=14, fontweight='bold', pad=15)

# Rotary switch
sw_x, sw_y, sw_w, sw_h = 20, 60, 80, 170
ax.add_patch(patches.FancyBboxPatch((sw_x, sw_y), sw_w, sw_h, boxstyle="round,pad=5",
             facecolor='#DDEEFF', edgecolor=C_SW, linewidth=2))
ax.text(sw_x + sw_w/2, sw_y + sw_h + 8, 'Rotary Switch', ha='center', fontsize=10, fontweight='bold', color=C_SW)

# Positions: COM at bottom, 1-6 up
n = 6
com_y = sw_y + 15
pos_gap = (sw_h - 30) / n
pos_ys = [com_y]
for i in range(1, n + 1):
    pos_ys.append(com_y + i * pos_gap)

# Draw positions
for i, y in enumerate(pos_ys):
    label = 'COM' if i == 0 else f'{i}'
    ax.text(sw_x + 8, y, label, ha='left', va='center', fontsize=8, color=C_SW)
    ax.plot(sw_x + sw_w, y, 'o', color=C_SW, markersize=4, zorder=5)

# Series resistor chain: COM → 1kΩ → Pos1 → 1kΩ → Pos2 → ...
# Layout: horizontal chain at y=40
chain_y = 40
chain_start_x = sw_x + sw_w + 20

# COM goes down to chain
ax.plot([sw_x + sw_w, sw_x + sw_w + 20], [com_y, com_y], color=C_WIRE, linewidth=1.5)
ax.plot([sw_x + sw_w + 20, sw_x + sw_w + 20], [com_y, chain_y], color=C_WIRE, linewidth=1.5)

# Draw chain horizontally
res_w = 30
gap = 15
junctions = []  # x positions of junctions between resistors
x = chain_start_x

# First junction (COM)
junctions.append(x)
ax.plot([chain_start_x, x], [chain_y, chain_y], color=C_WIRE, linewidth=1.5)

for i in range(n):
    # Resistor box
    rx = x + gap/2
    ax.add_patch(patches.Rectangle((rx, chain_y - 6), res_w, 12,
                 facecolor='#FFEECC', edgecolor=C_RES, linewidth=1.5, zorder=3))
    ax.text(rx + res_w/2, chain_y, '1kΩ', ha='center', va='center', fontsize=6, fontweight='bold', color=C_RES)

    # Wire before resistor
    ax.plot([x, rx], [chain_y, chain_y], color=C_WIRE, linewidth=1.5)
    # Wire after resistor
    next_x = rx + res_w + gap/2
    ax.plot([rx + res_w, next_x], [chain_y, chain_y], color=C_WIRE, linewidth=1.5)

    x = next_x
    junctions.append(x)

# Connect each position to its junction via vertical line
for i in range(1, n + 1):
    jx = junctions[i]
    py = pos_ys[i]
    # Vertical from junction up
    ax.plot([jx, jx], [chain_y, py], color=C_WIRE, linewidth=1, linestyle=':', alpha=0.5)
    # Horizontal to switch pin
    ax.plot([sw_x + sw_w, jx], [py, py], color=C_WIRE, linewidth=1.5)
    ax.plot(jx, chain_y, 'o', color=C_WIRE, markersize=3, zorder=5)

# ---- 4.7kΩ Pulldown ----
pd_x = junctions[0] - 5
pd_y_top = chain_y
pd_y_bot = 10
ax.plot([junctions[0], junctions[0]], [pd_y_top, pd_y_top - 8], color=C_WIRE, linewidth=1.5)
ax.add_patch(patches.Rectangle((pd_x - 10, pd_y_top - 22), 30, 14,
             facecolor='#FFEECC', edgecolor=C_RES, linewidth=1.5, zorder=3))
ax.text(pd_x + 5, pd_y_top - 15, '4.7kΩ', ha='center', va='center', fontsize=6, fontweight='bold', color=C_RES)
ax.plot([junctions[0], junctions[0]], [pd_y_top - 22, pd_y_bot], color=C_WIRE, linewidth=1.5)
# GND symbol
ax.plot([junctions[0] - 10, junctions[0] + 10], [pd_y_bot, pd_y_bot], color=C_GND, linewidth=2)
ax.plot([junctions[0] - 6, junctions[0] + 6], [pd_y_bot - 3, pd_y_bot - 3], color=C_GND, linewidth=1.5)
ax.plot([junctions[0] - 3, junctions[0] + 3], [pd_y_bot - 6, pd_y_bot - 6], color=C_GND, linewidth=1)
ax.text(junctions[0], pd_y_bot - 12, 'GND', ha='center', fontsize=8, color=C_GND)

# ---- Analog Pin connection ----
teensy_x = 440
# Extend chain to right → Analog Pin with spacing
ax.plot([x, teensy_x - 30], [chain_y, chain_y], color=C_WIRE, linewidth=1.5)
ax.annotate('', xy=(teensy_x - 5, chain_y), xytext=(teensy_x - 30, chain_y),
            arrowprops=dict(arrowstyle='->', color=C_TEENSY, lw=2))
ax.text(teensy_x, chain_y, 'Teensy\nAnalog Pin\n(A10~A12)', ha='left', va='center',
        fontsize=9, fontweight='bold', color=C_TEENSY,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#EEFFEE', edgecolor=C_TEENSY))

# ---- ADC formula ----
ax.text(210, 265, r'ADC = 1023 × 4700 / (k × 1000 + 4700)',
        ha='center', fontsize=10, fontstyle='italic', color='#555555',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F8F8F8', edgecolor='#CCCCCC'))
ax.text(210, 250, 'k = selected position (1~6)', ha='center', fontsize=8, color='#888888')

plt.tight_layout()
plt.savefig('docs/resistor_ladder_circuit.png', dpi=150, bbox_inches='tight', facecolor='white')
print('Saved docs/resistor_ladder_circuit.png')
