# -*- coding: utf-8 -*-
"""Krok 1 korekty EmpCo „Przeglądu oferty LM”: kopia CDR -> zrzut wszystkich tekstów (strona, id, pozycja, treść) do JSON.
Oryginał 2025.09 zostaje nietknięty; pracujemy na kopii „Przegląd Produktów LM 2026.11 A4.cdr”."""
import json, os, shutil, sys, time
import win32com.client as wc

MAT = r'C:\Users\bkokoszanek\Desktop\Claude Apk\18. Leroy Merlin - Portal\materiały'
SRC = os.path.join(MAT, 'Przegląd oferty (Leroy Merlin) 2025.09 A4.cdr')
DST = os.path.join(MAT, 'Przegląd Produktów LM 2026.11 A4.cdr')
OUT = sys.argv[1]

if not os.path.exists(DST):
    shutil.copy2(SRC, DST)

app = wc.gencache.EnsureDispatch('CorelDRAW.Application.25')
app.Visible = True
while app.Documents.Count > 0:
    d = app.Documents.Item(1); d.Dirty = False; d.Close()
t = time.time()
doc = app.OpenDocument(DST)
doc.Unit = 3  # mm
print('otwarte', round(time.time() - t), 's, stron:', doc.Pages.Count)

rows = []
def walk(shapes, page, layer, path):
    for i in range(1, shapes.Count + 1):
        s = shapes.Item(i)
        try:
            typ = s.Type
        except Exception:
            continue
        if typ == 7:  # group
            walk(s.Shapes, page, layer, path + [s.StaticID])
        elif typ == 6:  # text
            try:
                txt = s.Text.Story.Text
            except Exception:
                txt = ''
            rows.append({'p': page, 'id': s.StaticID, 'layer': layer, 'grp': path, 'x': round(s.LeftX, 1), 'y': round(s.TopY, 1),
                         'w': round(s.SizeWidth, 1), 'h': round(s.SizeHeight, 1), 'art': s.Text.Type, 't': txt})
        elif typ in (5, 16):  # bitmap / ole
            rows.append({'p': page, 'id': s.StaticID, 'layer': layer, 'grp': path, 'x': round(s.LeftX, 1), 'y': round(s.TopY, 1),
                         'w': round(s.SizeWidth, 1), 'h': round(s.SizeHeight, 1), 'bmp': 1, 't': ''})
        elif typ == 20 or typ == 3:  # powerclip container? curve: skip
            try:
                if s.PowerClip is not None:
                    walk(s.PowerClip.Shapes, page, layer, path + [s.StaticID])
            except Exception:
                pass

# strony główne (master) też — tam bywa stopka
for pi in range(0, doc.Pages.Count + 1):
    pg = doc.Pages.Item(pi) if pi else doc.MasterPage
    for li in range(1, pg.Layers.Count + 1):
        L = pg.Layers.Item(li)
        walk(L.Shapes, pi, L.Name, [])
json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('teksty:', sum(1 for r in rows if 'bmp' not in r), 'bitmapy:', sum(1 for r in rows if 'bmp' in r))
