# -*- coding: utf-8 -*-
"""Dobór packshotu do indeksu wg serii + koloru + kształtu (zdjęcia już w assets/img, źródła w img-manifest.json).
Zmienia pole „im” w assets/data.js tylko tam, gdzie obecne zdjęcie ma inny kształt albo kolor, a istnieje lepsze.
Uruchom:  python 15_packshot_ksztalt.py [--zapisz]"""
import io, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(os.path.dirname(HERE), 'assets')
man = json.load(open(os.path.join(A, 'img-manifest.json'), encoding='utf-8'))
p = os.path.join(A, 'data.js'); S = io.open(p, encoding='utf-8').read()
d = json.loads(S.split('=', 1)[1].split(';\n')[0])
have = set(d['img'])


def n(s): return unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().lower().replace('_', ' ').replace('-', ' ')


FAM = {'Sinergid': ['sinegrid', 'sinergid'], 'Go Baby': ['go baby', 'gobaby'], 'Magnetic': ['magnetic', 'magneic'], 'Frigo': ['frigo', 'frgio']}
COL = {'biały kamień': ['white stone', ' ws ', 'bialy kamien', 'ws'], 'czarny kamień': ['black stone', ' bs ', 'czarny kamien', 'bs'],
       'szary kamień': ['grey stone', ' gs ', 'szary kamien', 'greystone', 'gs'], 'kaszmirowy kamień': ['kaszmir', 'cas', 'cashmere'],
       'cementowy kamień': ['cement', ' cs ', 'cs'], 'biały gładki': ['smooth white', ' sw ', 'bialy gladki', 'sw'], 'biały mat': ['white', 'bial'],
       'czarny mat': ['black mat', 'czarny mat', 'black', 'bm'], 'biały': ['white', 'bial', 'sw']}
SHP = {'kwadratowy': ['kwadrat', 'kwardat', ' kw '], 'prostokątny': ['prostok', ' pro ', ' pr ', 'rect'],
       'półokrągły': ['polokr', 'r55', 'okragl', ' pol ', '1 4k', '14k'], 'pięciokątny': ['pieciok', ' pie ', '5k', ' 5 ']}
OTHER_COL = lambda c: [t for k, v in COL.items() if k != c for t in v if len(t) > 3]


def toks(key):
    m = man.get(key, {}); return ' ' + n(m.get('src', '')) + ' ' + n(key) + ' '


def has(s, ts): return any((' %s ' % t.strip() in s) if len(t.strip()) <= 3 else (t in s) for t in ts)


changes = []
for q in d['products']:
    if q['cat'] != 'brodzik' or not q.get('shape'): continue
    fam = FAM.get(q['fam'], [n(q['fam'])]); col = COL.get(q.get('c') or '', []); shp = SHP[q['shape']]
    def score(k):
        s = toks(k)
        if man.get(k, {}).get('kind') != 'pack' or k not in have: return -1
        if not has(s, fam): return -1
        sc = 0
        if col and has(s, col): sc += 4
        elif col: return -1
        if has(s, shp): sc += 3
        elif any(has(s, v) for kk, v in SHP.items() if kk != q['shape']): sc -= 5
        if 'packshot' in s: sc += 1
        if '#2' in man[k].get('src', '') or ' 2 ' in s[-8:]: sc -= 1
        return sc
    cur = score(q['im'])
    best = max(man, key=score)
    if score(best) > cur and score(best) >= 7:
        changes.append((q['ref'], q['im'], best, q['fam'], q['shape'], q.get('c')))
print('do zmiany:', len(changes))
import collections
for (o, b), k in collections.Counter((c[1], c[2]) for c in changes).most_common():
    print('%3d  %s -> %s' % (k, o, b))
if '--zapisz' in sys.argv:
    for ref, old, new, *_ in changes:
        m = re.search(r'\{"ref":"%s"[^{}]*\}' % ref, S); o = json.loads(m.group(0)); o['im'] = new
        S = S[:m.start()] + json.dumps(o, ensure_ascii=False, separators=(',', ':')) + S[m.end():]
    io.open(p, 'w', encoding='utf-8', newline='').write(S); print('zapisano')
