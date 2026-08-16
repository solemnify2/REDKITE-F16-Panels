#!/usr/bin/env python3
"""Scan BMS shared memory — snapshot comparison mode.
Press Enter to take snapshot BEFORE toggling, toggle in BMS, press Enter again to compare."""
import time, struct, mmap, ctypes

SHM_NAMES = ["FalconSharedMemoryArea", "FalconSharedMemoryArea2"]
SHM_SIZE = 4096

def open_shm(name):
    try:
        h = ctypes.windll.kernel32.OpenFileMappingW(0x0004, False, name)
        if not h: return None
        ctypes.windll.kernel32.CloseHandle(h)
        return mmap.mmap(-1, SHM_SIZE, tagname=name, access=mmap.ACCESS_READ)
    except: return None

def snapshot(shms):
    snap = {}
    for name, s in shms.items():
        s.seek(0)
        snap[name] = s.read(SHM_SIZE)
    return snap

def compare(snap1, snap2):
    """Compare two snapshots, show only likely bit-flag changes (not float noise)."""
    results = []
    for name in snap1:
        for off in range(0, len(snap1[name]) - 3, 4):
            old = struct.unpack_from('<I', snap1[name], off)[0]
            new = struct.unpack_from('<I', snap2[name], off)[0]
            if old != new:
                diff = old ^ new
                # Count number of bits changed
                bits = bin(diff).count('1')
                results.append((name, off, old, new, diff, bits))
    return results

print("Waiting for BMS shared memory...")
shms = {}
while not shms:
    for name in SHM_NAMES:
        s = open_shm(name)
        if s: shms[name] = s
    if not shms: time.sleep(1)

print(f"Connected: {list(shms.keys())}\n")

try:
    while True:
        input(">>> Press Enter to take BEFORE snapshot (do NOT toggle yet)...")
        before = snapshot(shms)
        print("    Snapshot taken.")

        input(">>> Now toggle the switch in BMS, then press Enter...")
        after = snapshot(shms)
        print("    Snapshot taken.\n")

        results = compare(before, after)

        # Sort by number of bits changed (fewer bits = more likely a flag)
        results.sort(key=lambda r: r[5])

        print(f"  {'SHM':<30s}  {'Offset':>6s}  {'Before':>12s}  {'After':>12s}  {'Diff':>12s}  Bits")
        print(f"  {'-'*30}  {'-'*6}  {'-'*12}  {'-'*12}  {'-'*12}  ----")
        for name, off, old, new, diff, bits in results:
            short = name.replace("FalconSharedMemory", "")
            marker = " <<<" if bits <= 3 else ""
            print(f"  {short:<30s}  {off:4d}    0x{old:08X}    0x{new:08X}    0x{diff:08X}   {bits:2d}{marker}")

        print(f"\n  Total changes: {len(results)}  (<<< = likely bit flags, 1-3 bits changed)\n")

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    for s in shms.values(): s.close()
