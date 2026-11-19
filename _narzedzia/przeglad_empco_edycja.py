# -*- coding: utf-8 -*-
"""Korekta EmpCo „Przeglądu oferty LM 2025.09” -> „Przegląd Produktów LM 2026.11”.
Działa na KOPII (materiały/Przegląd Produktów LM 2026.11 A4.cdr), otwartej w CorelDRAW 2024.
Bramka zapisu: Save() tylko gdy wszystkie operacje się udały. Potem eksport PDF (wszystkie strony).
Źródła okresów gwarancji: Karta gwarancyjna Stabilsafe v15.25 (pkt 4.1–4.8); Standard Plus 7 lat — decyzja zarządu."""
import os, sys
import win32com.client as wc

MAT = r'C:\Users\bkokoszanek\Desktop\Claude Apk\18. Leroy Merlin - Portal\materiały'
CDR = os.path.join(MAT, 'Przegląd Produktów LM 2026.11 A4.cdr')
PDF = os.path.join(MAT, 'Przegląd Produktów LM 2026.11 A4.pdf')
DRY = '--dry' in sys.argv

app = wc.gencache.EnsureDispatch('CorelDRAW.Application.25')
app.Visible = True
doc = None
for i in range(1, app.Documents.Count + 1):
    d = app.Documents.Item(i)
    if os.path.normcase(d.FullFileName) == os.path.normcase(CDR):
        doc = d
if doc is not None and doc.Dirty:          # po nieudanym przebiegu: odrzuć zmiany w pamięci
    doc.Dirty = False; doc.Close(); doc = None
if doc is None:
    doc = app.OpenDocument(CDR)
doc.Unit = 3
ok, bad = [], []

def shape(p, sid):
    pg = doc.Pages.Item(p)
    s = pg.Shapes.FindShape('', 0, sid, True)
    if s is None:
        raise RuntimeError('brak obiektu %s na str. %s' % (sid, p))
    return s

def op(desc, fn):
    try:
        fn(); ok.append(desc)
    except Exception as e:
        bad.append('%s: %s' % (desc, e))

def set_text(p, sid, txt):
    def f():
        s = shape(p, sid); s.Text.Story.Text = txt
    op('tekst %s/%s' % (p, sid), f)

def sub(p, sid, old, new):
    def f():
        st = shape(p, sid).Text.Story
        t = st.Text
        i = t.find(old)
        if i < 0:
            raise RuntimeError('nie ma „%s” w „%s”' % (old, t[:60]))
        st.Range(i, i + len(old)).Text = new
    op('podmiana %s/%s „%s”' % (p, sid, old[:20]), f)

def delete(p, sid):
    op('usuń %s/%s' % (p, sid), lambda: shape(p, sid).Delete())

def delete_region(p, x0, x1, ytop, ybot, keep=()):
    def f():
        pg = doc.Pages.Item(p)
        L = pg.ActiveLayer if pg.Layers.Count == 0 else pg.Layers.Item(pg.Layers.Count)
        n = 0
        for li in range(1, pg.Layers.Count + 1):
            sh = pg.Layers.Item(li).Shapes
            ids = []
            for i in range(1, sh.Count + 1):
                s = sh.Item(i)
                if s.StaticID in keep:
                    continue
                if s.LeftX >= x0 and s.LeftX + s.SizeWidth <= x1 and s.TopY <= ytop and s.TopY - s.SizeHeight >= ybot:
                    ids.append(s.StaticID)
            objs = [sh.Item(i) for i in range(1, sh.Count + 1) if sh.Item(i).StaticID in ids]
            for o in objs:
                try:
                    o.Delete(); n += 1
                except Exception:
                    pass
        print('  str.%s: usunięto %d obiektów z obszaru' % (p, n))
    op('usuń obszar str.%s' % p, f)

def replace_image(p, sid, src_p, src_id):
    """Wstaw kopię zdjęcia src w miejsce sid (dopasowanie z zachowaniem proporcji, środek), sid usuń."""
    def f():
        t = shape(p, sid)
        x, y, w, h = t.LeftX, t.TopY, t.SizeWidth, t.SizeHeight
        layer = t.Layer
        d = shape(src_p, src_id).Duplicate()
        d.MoveToLayer(layer)
        sw, sh = d.SizeWidth, d.SizeHeight
        k = min(w / sw, h / sh)
        d.SetSize(sw * k, sh * k)
        d.SetPosition(x + (w - sw * k) / 2, y - (h - sh * k) / 2)
        t.Delete()
    op('zdjęcie %s/%s <- %s/%s' % (p, sid, src_p, src_id), f)

FOOT_SRC = (8, 24938)   # styl istniejącego przypisu „*Klasa antypoślizgowości…”
def footnote(p, txt, x=25.8, y=18.2):
    def f():
        src = shape(*FOOT_SRC)
        for k, line in enumerate(txt.split('\r')):     # osobny obiekt na wiersz (tekst ozdobny nie łamie się poprawnie)
            d = src.Duplicate()
            d.MoveToLayer(doc.Pages.Item(p).Layers.Item(doc.Pages.Item(p).Layers.Count))
            d.Text.Story.Text = line
            d.SetPosition(x, y - k * (2.4 if p == 7 else 2.6))
    op('przypis str.%s' % p, f)

WARUNEK = 'Warunek: montaż zgodnie z instrukcją, przez osobę o odpowiednich kwalifikacjach. Gwarancja nie ogranicza ustawowych praw kupującego.'
GW = {
    'SS': 'Gwarancja producenta wg karty gwarancyjnej Stabilsafe v15.25: 10 lat na wytrzymałość na nacisk wg PN-EN 14527, 5 lat na stałość barwy płyty akrylowej.\r' + WARUNEK,
    'SP': 'Gwarancja producenta, technologia Standard Plus: 7 lat na stałość barwy płyty akrylowej.\r' + WARUNEK,
    'H':  'Gwarancja producenta wg karty gwarancyjnej Stabilsafe v15.25: 5 lat na wytrzymałość na nacisk wg PN-EN 1253-1.\r' + WARUNEK,
    'WC': 'Gwarancja producenta wg karty gwarancyjnej Stabilsafe v15.25: 5 lat na stałość barwy płyty akrylowej.\r' + WARUNEK,
    'OB': 'Gwarancja producenta wg karty gwarancyjnej Stabilsafe v15.25: 5 lat na trwałość obudowy.\r' + WARUNEK,
    'N':  'Gwarancja producenta wg karty gwarancyjnej Stabilsafe v15.25: 31 lat na trwałość materiału EPS.\r' + WARUNEK,
    'ALL': 'Gwarancja producenta: Stabilsafe® — 10 lat na wytrzymałość na nacisk wg PN-EN 14527 i 5 lat na stałość barwy (karta Stabilsafe v15.25);\rStandard Plus — 7 lat na stałość barwy. Warunek: montaż zgodnie z instrukcją, przez osobę o odpowiednich kwalifikacjach.\rGwarancja nie ogranicza ustawowych praw kupującego.',
}
BADGE = {'SS': ('wytrzymałość na nacisk', 'wg PN-EN 14527'), 'SP': ('stałość barwy', 'płyty akrylowej'), 'H': ('wytrzymałość na nacisk', 'wg PN-EN 1253-1'),
         'WC': ('stałość barwy', 'płyty akrylowej'), 'OB': ('trwałość', 'obudowy'), 'N': ('trwałość', 'materiału EPS')}
def badge(p, line1_id, line2_id, kind):
    set_text(p, line1_id, BADGE[kind][0]); set_text(p, line2_id, BADGE[kind][1])

# ---------- str. 1 — okładka
# (tytuł „przegląd oferty” zostaje — nazwa pliku i portalu: „Przegląd Produktów LM”)

# ---------- str. 2 — firma
sub(2, 24354, 'Zrównoważona produkcja w Polsce', 'Produkcja w Polsce — od formy do gotowego wyrobu')
sub(2, 24354, 'Bezkompromisowa trwałość i bezpieczeństwo', 'Brodziki badane wg PN-EN 14527')
sub(2, 24354, 'Stabilna rodzinna firma od ponad 40 lat', 'Rodzinna firma od 1981 roku')
delete_region(2, 8.0, 114.0, 84.5, 31.0)          # zdjęcie dłoni z mchem, liść, FSC/QR, „EKO-ODPOWIEDZIALNY”, „ZRÓWNOWAŻONY ROZWÓJ”

# ---------- str. 3 — technologie
delete(3, 46436); delete(3, 46439)                 # ikony liścia przy Stabilsafe
badge(3, 46482, 46481, 'SS')
badge(3, 46473, 46472, 'SP')
footnote(3, GW['ALL'], x=90)

# ---------- str. 4 — produkt na zamówienie
set_text(4, 24067, 'klasa B (EN 16165)')

# ---------- str. 5 — „Potwierdzona jakość”: przebudowa (zostaje nagłówek, stopka, tytuł)
KEEP5 = (47590, 47591, 47592, 47593, 47594, 47595, 46577, 40223, 12734, 46572)
def font_of(p, sid):
    st = shape(p, sid).Text.Story
    return st.Font, st.Size
body_font = {}
def grab():
    body_font['f'], _ = font_of(5, 12157)
    body_font['h'], _ = font_of(5, 12156)
op('czcionki str.5', grab)
delete_region(5, -60, 360, 400.0, 26.0, keep=KEEP5)
def build5():
    L = doc.Pages.Item(5).Layers.Item(doc.Pages.Item(5).Layers.Count)
    bf, hf = body_font.get('f', 'Lato'), body_font.get('h', 'Lato')
    lead = L.CreateParagraphText(15, 182, 282, 168, 'Brodziki Schedpol i Sensea w ofercie Leroy Merlin projektujemy i badamy według norm europejskich. Poniżej parametry, które można sprawdzić w dokumentacji wyrobu.', 0, 0, bf, 11)
    cols = [
        (15, 'PN-EN 14527 — BRODZIKI', 'Norma określa wymagania i metody badań brodzików:\r• zdolność do czyszczenia\r• prawidłowe odprowadzanie wody\r• wymiary przyłączeniowe (PN-EN 251)\r• stabilność dna i wytrzymałość na obciążenia\r• odporność na odczynniki chemiczne i środki plamiące\r• odporność na zmiany temperatury'),
        (82, 'ANTYPOŚLIZGOWOŚĆ', 'Brodziki o strukturze kamienia: klasa A — DIN EN 16165:2023 (załącznik A), badanie boso.\rNa zamówienie dostępne powłoki antypoślizgowe klasy B i C.'),
        (149, 'GWARANCJA PRODUCENTA', 'Stabilsafe® (karta gwarancyjna Stabilsafe v15.25): 10 lat na wytrzymałość na nacisk wg PN-EN 14527 i 5 lat na stałość barwy płyty akrylowej.\rStandard Plus: 7 lat na stałość barwy płyty akrylowej.\rNośniki EPS: 31 lat na trwałość materiału.\rWarunek: montaż zgodnie z instrukcją, przez osobę o odpowiednich kwalifikacjach. Gwarancja nie ogranicza ustawowych praw kupującego.'),
        (216, 'DOKUMENTACJA', 'Karty produktów PDF z rysunkiem technicznym, instrukcje montażu i karty gwarancyjne dla każdego indeksu Leroy Merlin — w Strefie projektanta Schedpol.\rModele 3D brodzików: biblioteka CAD Decor.'),
    ]
    for x, h, t in cols:
        hd = L.CreateParagraphText(x, 160, x + 62, 150, h, 0, 0, hf, 11)
        hd.Text.Story.Bold = True
        try:
            hd.Text.Story.Fill.UniformColor.RGBAssign(0x78, 0xBE, 0x20)
        except Exception:
            pass
        b = L.CreateParagraphText(x, 148, x + 62, 40, t, 0, 0, bf, 9)
        b.Text.Story.Bold = False
op('str.5 nowa treść', build5)

# ---------- str. 6 — kamienista struktura
sub(6, 24347, ' i Antibac', '')
sub(6, 24347, 'POWIERZCHNIA ANTYBAKTERYJNA', 'POWIERZCHNIA')

# ---------- warstwa „higieniczna” -> „użytkowa” (przekroje)
for p, sid in [(7, 23455), (8, 25537), (9, 19654), (10, 25518), (11, 25496), (12, 25482), (13, 43480), (14, 19461), (15, 22383), (19, 20061)]:
    set_text(p, sid, 'użytkowa')

# ---------- str. 7, 8 — Balans, Magnetic (Stabilsafe)
for p, ids, leaf in [(7, (19076, 19075, 19074, 19073, 19072, 19077), (24388, 24389)), (8, None, (25520, 25521))]:
    for l in leaf:
        delete(p, l)
for sid, t in zip((19076, 19075, 19074, 19073, 19072), ('HYDROSZCZELNA', 'WARSTWA', 'OGRANICZA', 'PRZENIKANIE', 'WILGOCI')):
    set_text(7, sid, t)
delete(7, 19077)
badge(7, 20938, 20937, 'SS')
footnote(7, 'Gwarancja producenta (karta Stabilsafe v15.25): 10 lat na wytrzymałość\rna nacisk wg PN-EN 14527, 5 lat na stałość barwy płyty akrylowej.\rWarunek: montaż zgodnie z instrukcją, przez osobę o odpowiednich\rkwalifikacjach. Gwarancja nie ogranicza ustawowych praw kupującego.', x=205.0, y=33.6)
# str. 8 — blok 60%: identyfikatory wyszukiwane po treści
def fix60_p8():
    pg = doc.Pages.Item(8)
    found = {}
    for want in ('60% TRWALSZY', 'MATERIAŁ', 'KOMPOZYTOWY', 'PRZY NIŻSZEJ', 'WADZE O', '60%'):
        hits = pg.Shapes.FindShapes('', 6, True)
        for i in range(1, hits.Count + 1):
            s = hits.Item(i)
            if s.Text.Story.Text.strip() == want and s.LeftX > 240:
                found[want] = s
    if len(found) != 6:
        raise RuntimeError('str.8 znaleziono %d/6 linii bloku 60%%' % len(found))
    for want, t in zip(('60% TRWALSZY', 'MATERIAŁ', 'KOMPOZYTOWY', 'PRZY NIŻSZEJ', 'WADZE O'), ('HYDROSZCZELNA', 'WARSTWA', 'OGRANICZA', 'PRZENIKANIE', 'WILGOCI')):
        found[want].Text.Story.Text = t
    found['60%'].Delete()
op('str.8 blok 60%', fix60_p8)
badge(8, 22633, 22632, 'SS'); footnote(8, GW['SS'], y=12.0)

# ---------- str. 9, 10, 15 — „POWIERZCHNIA ANTYBAKTERYJNA ORAZ ŁATWA W UTRZYMANIU CZYSTOŚCI” + bakterie
for p, (pw, ab, oraz, wu, cz), bac in [(9, (13600, 13599, 13598, 13597, 13596), 23310), (10, (20736, 20735, 20734, 20733, 20732), 23316)]:
    set_text(p, ab, 'ŁATWA'); set_text(p, oraz, 'W UTRZYMANIU'); set_text(p, wu, 'CZYSTOŚCI'); delete(p, cz)
    replace_image(p, bac, 15, 23331)
    footnote(p, GW['SP'])
for sid in (22403, 22402, 22401, 22400, 22399, 22387, 22385, 22386, 22397, 22398):   # str. 15 — blok dubluje „EASY TO CLEAN” obok, usuwamy w całości
    delete(15, sid)

# ---------- str. 11–14 — Frigo, Consist/Sinergid, Integral/Grawello/Dante (Stabilsafe, zintegrowane)
P1114 = {11: (11218, 11221, 11257, 23342, 11258, (24392, 24393)), 12: (23374, 23377, 23370, 23395, 23393, (24394, 24395)),
         13: (43386, 43389, 43383, 43393, 43391, (43369, 43370)), 14: (23401, 23404, 23397, 23422, 23420, (24396, 24397))}
for p, (ochr, wygl, pct, bac, xback, leaf) in P1114.items():
    set_text(p, ochr, 'ŁATWA\rW UTRZYMANIU\rCZYSTOŚCI')
    set_text(p, wygl, 'WIELOWARSTWOWA\rKONSTRUKCJA\rWSPIERA IZOLACJĘ\rAKUSTYCZNĄ')
    delete(p, pct); delete(p, xback)
    replace_image(p, bac, 15, 23331)
    for l in leaf:
        delete(p, l)
    footnote(p, GW['SS'], y=12.0 if p in (12, 14) else 18.2)
badge(13, 43484, 43483, 'SS'); badge(14, 19499, 19498, 'SS')

# ---------- str. 15 — Tebe, Comfo, Dafne (Standard Plus)
badge(15, 22360, 22359, 'SP'); footnote(15, GW['SP'])

# ---------- str. 16 — Harmony
set_text(16, 41627, '5')
badge(16, 41624, 41623, 'H')
set_text(16, 41663, 'ANODOWANE\rALUMINIUM')
delete(16, 41644)
set_text(16, 43226, '- Korpus i maskownica z anodowanego aluminium.\r'
                    '- Maskownica 2w1: gładka lub do zabudowy płytkami.\r'
                    '- Regulacja położenia w pionie i poziomie.\r'
                    '- Przepływ syfonu: 42 l/min (Harmony) i 54 l/min (Harmony Prime).\r'
                    '- Zamknięcie wodne syfonu: 40 mm.')
footnote(16, GW['H'])

# ---------- str. 17 — Shower Express, Wall Comfort
set_text(17, 39230, 'Antypoślizgowa powierzchnia\rakrylowa brodzików\rklasy C wg DIN EN\r16165:2023\r(załącznik A).')
set_text(17, 15369, '5'); set_text(17, 15368, 'LAT')
badge(17, 15366, 15365, 'WC'); footnote(17, GW['WC'])

# ---------- str. 18 — panel Wall Comfort
set_text(18, 15416, 'Easy to Clean')
set_text(18, 15417, 'Montaż bez płytek\ri fugowania')
set_text(18, 15418, 'Hydroszczelna konstrukcja\rogranicza przenikanie\rwilgoci')
delete(18, 15429); delete(18, 15425)          # zdjęcie bakterii z krzyżykiem; zostaje dłoń z gąbką

# ---------- str. 19 — wanna Torres (Standard Plus)
delete(19, 26131)                                        # znak „40 LAT DOŚWIADCZENIA”
def kill_mip():
    s = doc.Pages.Item(19).Shapes.FindShape('', 0, 26136, True)
    if s is None:
        print('  str.19: znak „100% Made in Poland” usunięty razem z grupą 26131'); return
    grp = s.ParentGroup
    (grp if grp is not None else s).Delete()
op('usuń znak 100% Made in Poland', kill_mip)
set_text(19, 26154, 'sztywna konstrukcja\r- wzmocnienie stalowe')
set_text(19, 26156, 'powłoka\rantypoślizgowa')
delete(19, 26155)
set_text(19, 26160, 'Odkryj przyjemność\r               kąpieli')
badge(19, 20919, 20918, 'SP'); footnote(19, GW['SP'])

# ---------- str. 20 — obudowy (karta: 5 lat na trwałość)
set_text(20, 27530, '5')
badge(20, 27527, 27526, 'OB'); footnote(20, GW['OB'])

# ---------- str. 21–23 — nośniki EPS
for p, (l1, l2, a1, a2) in {21: (27149, 27148, 27199, 27198), 22: (29451, 29450, 29417, 29416)}.items():
    badge(p, l1, l2, 'N')
    set_text(p, a1, 'PODPARCIE WANNY')
    set_text(p, a2, 'NA CAŁEJ POWIERZCHNI')
    footnote(p, GW['N'])
set_text(21, 27239, 'Podparcie dna wanny na całej powierzchni\rnośnika')
badge(23, 30359, 30358, 'N'); footnote(23, GW['N'])

# ---------- str. 28 — kontakt: godziny BOK (informacja użytkownika 19.11.2026)
sub(28, 46947, '8:00-15:00', '8:00-16:00')

print('OK:', len(ok), ' BŁĘDY:', len(bad))
for b in bad:
    print('  !', b)
if bad or DRY:
    print('ZAPIS POMINIĘTY' + (' (dry run)' if DRY else ''))
    sys.exit(1 if bad else 0)
doc.Save()
s = doc.PDFSettings
s.PublishRange = 0
s.TextAsCurves = False
s.DownsampleColor = True; s.ColorResolution = 150
s.DownsampleGray = True; s.GrayResolution = 150
s.JPEGQualityFactor = 80
if os.path.exists(PDF):
    os.remove(PDF)
doc.PublishToPDF(PDF)
print('PDF:', PDF, os.path.getsize(PDF) // 1024, 'kB')
