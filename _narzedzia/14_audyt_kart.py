# -*- coding: utf-8 -*-
"""Audyt danych i zdjęć kart produktów w STANIE KOŃCOWYM (data.js + lm.js + packshoty.js: IM/FIX nadpisują zdjęcie, kolor, kształt).
Porównanie z eksportem referencji LM (EAN, gama, wymiar w nazwie) i zgodność packshotu z serią / kolorem / kształtem (wg ścieżki źródłowej).
Wynik: _narzedzia/audyt_kart.txt"""
import json, os, re, unicodedata
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); A = os.path.join(ROOT, 'assets')
MAT = os.path.join(os.path.dirname(ROOT), 'materiały')


def js_var(txt, name):
    m = re.search(r'var %s = (\{.*?\});\n' % name, txt, re.S); return json.loads(m.group(1)) if m else {}


d = json.loads(open(os.path.join(A, 'data.js'), encoding='utf-8').read().split('=', 1)[1].split(';\n')[0])
lmt = open(os.path.join(A, 'lm.js'), encoding='utf-8').read(); lm = js_var(lmt, 'L')
pk = open(os.path.join(A, 'packshoty.js'), encoding='utf-8').read()
IMG, IM, FIX = js_var(pk, 'IMG'), js_var(pk, 'IM'), js_var(pk, 'FIX')
man = json.load(open(os.path.join(A, 'img-manifest.json'), encoding='utf-8'))
SRC = {k: v.get('src', '') for k, v in man.items()}; SRC.update({k: v.get('src', '') for k, v in IMG.items()})
wb = openpyxl.load_workbook(os.path.join(MAT, '2026-03-26T13-41-37-moje-referencje.xlsx'), read_only=True, data_only=True)
ref = {str(r[10]): r for r in list(wb.worksheets[0].iter_rows(values_only=True))[1:] if r[10]}


def n(s): return ' ' + unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().lower().replace('_', ' ').replace('-', ' ').replace('\\', ' ').replace('(', ' ').replace(')', ' ') + ' '


def has(s, ts): return any((' %s ' % t in s) if len(t) <= 3 else (t in s) for t in ts)


FAM = {'Sinergid': ['sinegrid', 'sinergid'], 'Go Baby': ['go baby', 'gobaby'], 'Magnetic': ['magnetic', 'magneic'], 'Frigo': ['frigo', 'frgio'],
       'Obudowa uniwersalna': ['zabudowa', 'obudowa'], 'Panele do brodzików': ['panel'], 'Maskownica Balans/Integral': ['maskownic'], 'Nogi Ipsilon': ['nogi'],
       'Wall Comfort': ['scianka', 'wall'], 'Nośnik': ['nosnik']}
COL = {'biały kamień': ['white stone', 'ws', 'bialy kamien'], 'czarny kamień': ['black stone', 'bs', 'czarny kamien'],
       'szary kamień': ['grey stone', 'gs', 'szary kamien', 'greystone', 'szary'], 'kaszmirowy kamień': ['kaszmir', 'cas', 'cashmere'],
       'cementowy kamień': ['cement', 'cs'], 'biały gładki': ['smooth white', 'sw', 'bialy gladki', 'smooth'], 'biały mat': ['white', 'bialy', 'w'],
       'czarny mat': ['black', 'czarny', 'bm', 'b'], 'czarny': ['black', 'czarn', 'prome'], 'stal': ['harmony', 'prime']}
SHP = {'kwadratowy': ['kwadrat', 'kwardat', 'kw', 'kwa'], 'prostokątny': ['prostok', 'pro', 'pr', 'rect', 'prostokat'],
       'półokrągły': ['polokr', 'r55', 'okragl', 'pol', '14k', 'pokrgy'], 'pięciokątny': ['pieciok', 'pie', '5k', '5']}
out = []; stat = {'ok': 0}
for q in d['products']:
    p = dict(q); r = p['ref']; e = []
    if r in IM: p['im'] = IM[r]
    f = FIX.get(r) or {}
    if f.get('shape'): p['shape'] = f['shape']
    if f.get('c'): p['c'] = f['c']
    L = lm.get(r, {}); R = ref.get(r)
    ean = L.get('ean') or p.get('ean'); g = L.get('g') or p.get('g')
    if R is None:
        e.append('brak na liście referencji LM (26.03.2026)')
    else:
        if str(R[11]) != str(ean): e.append('EAN portal %s ≠ LM %s' % (ean, R[11]))
        if str(R[16] or '') != str(g or ''): e.append('gama portal %s ≠ LM %s' % (g, R[16]))
        nm = n(R[13])
        if isinstance(p.get('a'), (int, float)) and isinstance(p.get('b'), (int, float)):
            dims = re.findall(r'(\d{2,3})\s*x\s*(\d{2,3})', nm)
            if dims and not any({int(x), int(y)} == {int(p['a']), int(p['b'])} for x, y in dims):
                e.append('wymiar portal %sx%s ≠ nazwa LM „%s”' % (p['a'], p['b'], R[13]))
    src = SRC.get(p['im'])
    if src is None:
        e.append('brak zdjęcia %s' % p['im'])
    else:
        s = n(src) + n(p['im'])
        ft = FAM.get(p['fam'], [n(p['fam']).strip().split()[0]])
        if not has(s, ft): e.append('seria: zdjęcie %s (%s)' % (p['im'], src[:90]))
        c = p.get('c') or ''
        if c in COL and p['cat'] in ('brodzik', 'wanna', 'panel ścienny', 'odpływ liniowy') and not has(s, COL[c]):
            e.append('kolor „%s”: zdjęcie %s (%s)' % (c, p['im'], src[-80:]))
        if p['cat'] == 'brodzik' and p.get('shape'):
            found = [k for k, v in SHP.items() if has(s, v)]
            if found and p['shape'] not in found: e.append('kształt %s: zdjęcie %s → %s (%s)' % (p['shape'], p['im'], '/'.join(found), src[-80:]))
    if e: out.append('%s  %s %s %s×%s %s\n    - ' % (r, p['fam'], p.get('shape') or '', p.get('a'), p.get('b'), p.get('c') or '') + '\n    - '.join(e))
    else: stat['ok'] += 1
open(os.path.join(HERE, 'audyt_kart.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('produktów:', len(d['products']), ' bez uwag:', stat['ok'], ' z uwagami:', len(out))
