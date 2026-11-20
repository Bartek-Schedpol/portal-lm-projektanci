# -*- coding: utf-8 -*-
"""Odczyt położenia odpływu (okrąg Ø90) z rysunków technicznych etykiet (et-*.png) — Frigo, Ipsilon.

Rzut z góry = największy obrys na rysunku; odpływ = okrąg o promieniu ~45 mm w skali rzutu.
Wynik: _narzedzia/odplyw_rysunki.json {ref: {fx, fy, w_mm, h_mm, r_px}}  (fx, fy = środek odpływu jako ułamek
szerokości/wysokości rzutu, oś y w dół, tak jak na rysunku) + podglądy kontrolne w _kontrola_odplyw/.
"""
import json, os, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
A = os.path.join(ROOT, 'assets')
data = json.loads(open(os.path.join(A, 'data.js'), encoding='utf-8').read().split('=', 1)[1].split(';\n')[0])
rys = json.loads(open(os.path.join(A, 'rysunki.js'), encoding='utf-8').read().split('window.SP.rys =', 1)[1].strip().rstrip(';').split(';\n')[0])
KO = os.path.join(HERE, '_kontrola_odplyw'); os.makedirs(KO, exist_ok=True)
FAMS = set(sys.argv[1:]) or {'Frigo', 'Ipsilon'}
out = {}
for p in data['products']:
    if p['cat'] != 'brodzik' or p['fam'] not in FAMS or p['ref'] not in rys: continue
    f = rys[p['ref']]['f']
    if not f.startswith('et-'): continue
    img = cv2.imread(os.path.join(A, 'img', 'rys', f), cv2.IMREAD_UNCHANGED)
    if img.ndim == 3 and img.shape[2] == 4:          # przezroczyste tło -> białe
        a = img[:, :, 3:4] / 255.0
        img = (img[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    g = cv2.resize(g, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    bw = (g < 160).astype(np.uint8) * 255
    cl = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(cl, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # obrys rzutu: największy prostokąt otaczający o proporcjach zbliżonych do a×b (nie widok z boku)
    want = [float(p['a']), float(p['b'])]
    best = None
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w < g.shape[1] * 0.2 or h < g.shape[0] * 0.2: continue
        r = w / h
        err = min(abs(r - want[0] / want[1]), abs(r - want[1] / want[0]))
        if err > 0.18: continue
        if best is None or w * h > best[2] * best[3]: best = (x, y, w, h)
    if not best:
        out[p['ref']] = {'err': 'brak obrysu', 'f': f}; continue
    x, y, w, h = best
    wmm = want[0] if abs(w / h - want[0] / want[1]) <= abs(w / h - want[1] / want[0]) else want[1]
    hmm = want[1] if wmm == want[0] else want[0]
    pxmm = w / (wmm * 10)
    r = 45 * pxmm
    roi = g[y:y + h, x:x + w]
    cs = cv2.HoughCircles(cv2.GaussianBlur(roi, (3, 3), 0), cv2.HOUGH_GRADIENT, dp=1, minDist=r * 0.8, param1=120, param2=18,
                          minRadius=int(r * 0.7), maxRadius=int(r * 1.35))
    if cs is None:
        out[p['ref']] = {'err': 'brak okręgu', 'f': f}; continue
    cs = cs[0]
    # okrąg odpływu: najbliższy oczekiwanemu promieniowi, z dala od krawędzi obrysu (nie łuk R55)
    cand = [c for c in cs if c[0] > r and c[1] > r and c[0] < w - r and c[1] < h - r]
    if not cand: cand = list(cs)
    c = min(cand, key=lambda c: abs(c[2] - r))
    out[p['ref']] = {'fx': round(float(c[0]) / w, 4), 'fy': round(float(c[1]) / h, 4), 'w_mm': wmm * 10, 'h_mm': hmm * 10,
                     'r_px': round(float(c[2]), 1), 'r_exp': round(r, 1), 'f': f, 'shape': p['shape']}
    vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 160, 0), 3)
    cv2.circle(vis, (int(x + c[0]), int(y + c[1])), int(c[2]), (0, 0, 255), 4)
    cv2.imwrite(os.path.join(KO, p['ref'] + '.jpg'), cv2.resize(vis, None, fx=0.25, fy=0.25))
json.dump(out, open(os.path.join(HERE, 'odplyw_rysunki.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), 'błędy:', sum(1 for v in out.values() if 'err' in v))
for k, v in out.items():
    if 'err' in v: print(' ', k, v)
