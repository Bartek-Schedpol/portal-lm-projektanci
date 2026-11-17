import os
# -*- coding: utf-8 -*-
import fitz, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), r"materiały\Przegląd oferty (Leroy Merlin) 2025.09a A4.pdf")
out = sys.argv[1]
d = fitz.open(p)
pg = d[2]
box = fitz.Rect(650, 20, 842, 80)
gs = [g for g in pg.get_drawings() if g["rect"].intersects(box) and g["rect"].width < 200]
u = fitz.Rect()
for g in gs: u |= g["rect"]
pad = 1.0
x0, y0, w, h = u.x0 - pad, u.y0 - pad, u.width + 2*pad, u.height + 2*pad
def f(v): return f"{v:.3f}".rstrip("0").rstrip(".")
def hexc(c): return "#%02x%02x%02x" % tuple(int(round(v*255)) for v in c)
paths = {"brand": [], "ink": []}
for g in gs:
    dparts = []
    last = None
    for it in g["items"]:
        k = it[0]
        if k == "l":
            a, b = it[1], it[2]
            if last is None or abs(a.x-last.x) > 1e-3 or abs(a.y-last.y) > 1e-3:
                dparts.append(f"M{f(a.x-x0)} {f(a.y-y0)}")
            dparts.append(f"L{f(b.x-x0)} {f(b.y-y0)}"); last = b
        elif k == "c":
            a, c1, c2, b = it[1], it[2], it[3], it[4]
            if last is None or abs(a.x-last.x) > 1e-3 or abs(a.y-last.y) > 1e-3:
                dparts.append(f"M{f(a.x-x0)} {f(a.y-y0)}")
            dparts.append(f"C{f(c1.x-x0)} {f(c1.y-y0)} {f(c2.x-x0)} {f(c2.y-y0)} {f(b.x-x0)} {f(b.y-y0)}"); last = b
        elif k == "re":
            r = it[1]
            dparts.append(f"M{f(r.x0-x0)} {f(r.y0-y0)}H{f(r.x1-x0)}V{f(r.y1-y0)}H{f(r.x0-x0)}Z"); last = None
        elif k == "qu":
            q = it[1]
            dparts.append(f"M{f(q.ul.x-x0)} {f(q.ul.y-y0)}L{f(q.ur.x-x0)} {f(q.ur.y-y0)}L{f(q.lr.x-x0)} {f(q.lr.y-y0)}L{f(q.ll.x-x0)} {f(q.ll.y-y0)}Z"); last = None
    if not dparts or g.get("fill") is None: continue
    key = "ink" if sum(g["fill"]) < 0.1 else "brand"
    paths[key].append("".join(dparts) + "Z")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" role="img" aria-label="Schedpol — since 1981">'
       f'<path fill="#943330" fill-rule="evenodd" d="{" ".join(paths["brand"])}"/>'
       f'<path fill="currentColor" fill-rule="evenodd" d="{" ".join(paths["ink"])}"/></svg>')
open(out, "w", encoding="utf-8").write(svg)
print("svg bytes", len(svg), "viewBox", f(w), f(h), "brand paths", len(paths["brand"]), "ink paths", len(paths["ink"]))
# podgląd PNG
pm = pg.get_pixmap(matrix=fitz.Matrix(6, 6), clip=fitz.Rect(x0-4, y0-4, x0+w+4, y0+h+4))
pm.save(out.replace(".svg", "_ref.png"))
