# -*- coding: utf-8 -*-
"""Sygnatury brył z paczki „008 Modele 3D”: wymiary (cm), wypełnienie rzutu z góry (kwadrat ~1,0 / ćwierćkole R55 ~0,8 /
pięciokąt ~0,87), wysokość rantu i głębokość niecki (profil przekroju przez środek). Wynik: _narzedzia/sygnatury_bryl.json."""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'materiały', '008 Modele 3D')


def load_obj(path):
    v = []
    with open(path, encoding='latin-1') as f:
        for line in f:
            if line.startswith('v '):
                p = line.split()
                v.append((float(p[1]), float(p[2]), float(p[3])))
    return np.array(v)


def hull_area(pts):
    pts = sorted(set(map(tuple, np.round(pts, 2))))
    if len(pts) < 3:
        return 0.0
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    return abs(sum(h[i][0] * h[i - 1][1] - h[i - 1][0] * h[i][1] for i in range(len(h)))) / 2


def signature(path):
    v = load_obj(path)
    if len(v) == 0:
        return None
    mn, mx = v.min(0), v.max(0)
    d = mx - mn
    up = int(np.argmin(d))                     # oś pionowa = najmniejszy wymiar (brodziki są płaskie) — dla wanien/paneli sprawdzamy niżej
    ax = [i for i in range(3) if i != up]
    top = v[:, ax]
    fill = hull_area(top) / (d[ax[0]] * d[ax[1]]) if d[ax[0]] * d[ax[1]] else 0
    # profil: najniższy punkt powierzchni w środkowym pasie (dno niecki) względem góry
    z = v[:, up] - mn[up]
    c = (mn + mx) / 2
    band = (np.abs(v[:, ax[0]] - c[ax[0]]) < d[ax[0]] * 0.15) & (np.abs(v[:, ax[1]] - c[ax[1]]) < d[ax[1]] * 0.15)
    inner = z[band]
    depth = float(d[up] - inner.max()) if inner.size else None   # różnica między rantem a najwyższym punktem w środku
    w, l = sorted([float(d[ax[0]]), float(d[ax[1]])])
    return {'w': round(l, 1), 'l': round(w, 1), 'h': round(float(d[up]), 1), 'fill': round(fill, 3), 'depth': round(depth, 1) if depth is not None else None,
            'nv': int(len(v))}


out = {}
for dp, dn, fn in os.walk(SRC):
    for f in fn:
        if f.lower().endswith('.obj'):
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, SRC)
            try:
                out[rel] = signature(p)
            except Exception as e:
                out[rel] = {'err': str(e)}
json.dump(out, open(os.path.join(HERE, 'sygnatury_bryl.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out))
