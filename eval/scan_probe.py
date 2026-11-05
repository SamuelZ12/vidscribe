#!/usr/bin/env python3
"""Contact sheets for one window of a video, as used in the scan probe (docs/measurements.md, "Scan probe").

usage: scan_probe.py VIDEO START END OUTDIR [--method scene|even5|fill10] [--grid 4]
  scene:  last frame of each scene (same cut detection and dedupe as vidscribe's scene frames)
  even5:  one tile every 5 s
  fill10: scene tiles plus even fill so no gap exceeds 10 s
Writes OUTDIR/sheetNN.jpg (1280x720 grids) and prints one line per sheet: path, then tile times in reading order.
Needs only ffmpeg and system python3.
"""
import argparse, math, os, re, subprocess, tempfile

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('start', type=float); ap.add_argument('end', type=float); ap.add_argument('outdir')
ap.add_argument('--method', default='fill10', choices=['scene', 'even5', 'fill10']); ap.add_argument('--grid', type=int, default=4)
a = ap.parse_args()

def scenes(vid):
    fd, scf = tempfile.mkstemp(suffix='.txt'); os.close(fd)
    raw = subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-i', vid, '-an', '-vf',
        f"fps=2,scale=160:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file={scf},scale=9:8,format=gray",
        '-f', 'rawvideo', '-'], capture_output=True).stdout
    meta = open(scf).read(); os.unlink(scf)
    pts = [float(x) for x in re.findall(r'pts_time:([\d.]+)', meta)]
    score = [float(x) for x in re.findall(r'scene_score=([\d.]+)', meta)]
    nf = min(len(raw)//72, len(pts), len(score))
    def dhash(i):
        b = raw[i*72:(i+1)*72]
        return sum(1 << (r*8+c) for r in range(8) for c in range(8) if b[r*9+c] > b[r*9+c+1])
    cuts = [0] + [i for i in range(1, nf) if score[i] > 0.3] + [nf]
    out, seen = [], []
    for s, e in zip(cuts, cuts[1:]):
        i = e - 1; th = raw[i*72:(i+1)*72]
        if e - s < 2 or max(th) - min(th) < 12: continue
        h = dhash(i)
        if any(bin(h ^ k).count('1') <= 6 for k in seen): continue
        seen.append(h); out.append(pts[i])
    return out

s0, s1 = a.start, a.end
if a.method == 'even5':
    ts = [s0 + 5*(i+0.5) for i in range(int((s1-s0)/5))]
else:
    ts = sorted(t for t in scenes(a.video) if s0 <= t < s1)
    if a.method == 'fill10':
        pts = [s0] + ts + [s1]
        for p, q in zip(pts, pts[1:]):
            k = math.ceil((q-p)/10) - 1
            ts += [p + (q-p)*j/(k+1) for j in range(1, k+1)]
        ts.sort()

g = a.grid; n = g*g
tiles = os.path.join(a.outdir, 'tiles'); os.makedirs(tiles, exist_ok=True)
for i, t in enumerate(ts):
    subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-ss', f'{t:.2f}', '-i', a.video, '-frames:v', '1',
                    '-vf', f'scale={1280//g}:{720//g}', '-q:v', '3', f'{tiles}/{i:03d}.jpg'], check=False)
subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-framerate', '1', '-i', f'{tiles}/%03d.jpg',
                '-vf', f'tile={g}x{g}:padding=2:color=white', '-q:v', '3', f'{a.outdir}/sheet%02d.jpg'], check=True)
mmss = lambda t: f"{int(t//60)}:{t % 60:04.1f}"
for k in range(math.ceil(len(ts)/n)):
    print(f"{a.outdir}/sheet{k+1:02d}.jpg\t" + ' '.join(mmss(t) for t in ts[k*n:(k+1)*n]))
