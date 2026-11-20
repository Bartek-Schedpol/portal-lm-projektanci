# -*- coding: utf-8 -*-
"""Pomiar położenia odpływu w modelach OBJ z paczki „008 Modele 3D” (Blender, tryb wsadowy).

Wynik: _narzedzia/odplyw_modeli.json  {ścieżka_obj: {dims:[x,y,z] cm, drain:[x,y] cm od lewego-dolnego narożnika obrysu, how}}
Odpływ = (1) mała osobna część wewnątrz obrysu (maskownica/kratka) albo
         (2) skupisko ścianek pionowych otworu (Ø ok. 9 cm) z dala od obrzeża brodzika.
Uruchom: blender -b --factory-startup --python 12_odplyw_modeli.py -- lista.json wynik.json
"""
import json, math, sys
import bpy, bmesh, mathutils

args = sys.argv[sys.argv.index('--') + 1:]
paths = json.load(open(args[0], encoding='utf-8'))
out = {}


def hull2d(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def dist_hull(p, H):
    best = 1e9
    for i in range(len(H)):
        a, b = H[i], H[(i + 1) % len(H)]
        ax, ay = b[0] - a[0], b[1] - a[1]
        L = ax * ax + ay * ay or 1e-9
        t = max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L))
        best = min(best, math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay))
    return best


for path in paths:
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.obj_import(filepath=path)
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        # luźne części
        bm.verts.ensure_lookup_table()
        parts = []
        seen = set()
        for v in bm.verts:
            if v.index in seen: continue
            stack = [v]; comp = []
            seen.add(v.index)
            while stack:
                x = stack.pop(); comp.append(x)
                for e in x.link_edges:
                    w = e.other_vert(x)
                    if w.index not in seen:
                        seen.add(w.index); stack.append(w)
            parts.append(comp)
        def box(vs):
            xs = [v.co.x for v in vs]; ys = [v.co.y for v in vs]; zs = [v.co.z for v in vs]
            return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
        boxes = [box(p) for p in parts]
        big = max(range(len(parts)), key=lambda i: (boxes[i][1][0] - boxes[i][0][0]) * (boxes[i][1][1] - boxes[i][0][1]))
        (x0, y0, z0), (x1, y1, z1) = boxes[big]
        H = hull2d([(round(v.co.x, 1), round(v.co.y, 1)) for v in parts[big]])
        res = {'dims': [round(x1 - x0, 1), round(y1 - y0, 1), round(z1 - z0, 1)], 'hull': [[round(p[0] - x0, 1), round(p[1] - y0, 1)] for p in H]}
        # (1) małe części w obrysie
        small = []
        for i, (a, b) in enumerate(boxes):
            if i == big: continue
            cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            w = max(b[0] - a[0], b[1] - a[1])
            if x0 < cx < x1 and y0 < cy < y1 and 3 < w < 40 and b[2] > z0 + 0.4 * (z1 - z0):
                small.append((w, cx, cy))
        if small:
            w, cx, cy = max(small)
            res.update(drain=[round(cx - x0, 1), round(cy - y0, 1)], how='część %.0f cm' % w)
        else:
            # (2) ścianki pionowe otworu odpływu
            cells = {}
            for f in bm.faces:
                if abs(f.normal.z) > 0.4: continue
                c = f.calc_center_median()
                if c.z < z0 + 0.25 * (z1 - z0): continue
                if dist_hull((c.x, c.y), H) < 9: continue
                k = (int((c.x - x0) // 3), int((c.y - y0) // 3))
                cells[k] = cells.get(k, 0) + f.calc_area()
            if cells:
                best, sc = None, -1
                for (i, j) in cells:
                    s = sum(cells.get((i + di, j + dj), 0) for di in (-2, -1, 0, 1, 2) for dj in (-2, -1, 0, 1, 2))
                    if s > sc: best, sc = (i, j), s
                pts = [(k, a) for k, a in cells.items() if abs(k[0] - best[0]) <= 2 and abs(k[1] - best[1]) <= 2]
                tot = sum(a for _, a in pts)
                cx = sum((k[0] + .5) * 3 * a for k, a in pts) / tot
                cy = sum((k[1] + .5) * 3 * a for k, a in pts) / tot
                res.update(drain=[round(cx, 1), round(cy, 1)], how='otwór %.0f cm2' % tot)
            else:
                res['how'] = 'brak'
        out[path] = res
        bm.free()
    except Exception as e:
        out[path] = {'err': str(e)}
json.dump(out, open(args[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
