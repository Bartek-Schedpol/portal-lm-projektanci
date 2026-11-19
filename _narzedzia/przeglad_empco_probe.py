# -*- coding: utf-8 -*-
"""Zrzut obiektów najwyższego poziomu (każdy typ) z otwartego dokumentu Corela: strona, id, typ, bbox, kolor wypełnienia."""
import json, sys
import win32com.client as wc

app = wc.gencache.EnsureDispatch('CorelDRAW.Application.25')
doc = app.ActiveDocument
doc.Unit = 3
pages = [int(x) for x in sys.argv[2].split(',')]
out = []
for pi in pages:
    pg = doc.Pages.Item(pi)
    for li in range(1, pg.Layers.Count + 1):
        L = pg.Layers.Item(li)
        for i in range(1, L.Shapes.Count + 1):
            s = L.Shapes.Item(i)
            fill = ''
            try:
                if s.Fill.Type == 1:
                    c = s.Fill.UniformColor
                    fill = c.HexValue
            except Exception:
                pass
            n = 0
            try:
                n = s.Shapes.Count if s.Type == 7 else 0
            except Exception:
                pass
            txt = ''
            if s.Type == 6:
                txt = s.Text.Story.Text[:60]
            out.append({'p': pi, 'L': L.Name, 'id': s.StaticID, 'type': s.Type, 'n': n, 'x': round(s.LeftX, 1), 'y': round(s.TopY, 1),
                        'w': round(s.SizeWidth, 1), 'h': round(s.SizeHeight, 1), 'fill': fill, 't': txt, 'name': s.Name})
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out))
