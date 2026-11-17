# -*- coding: utf-8 -*-
"""Zasoby kart produktów: gama/EAN z eksportu LM, znaki marek i gwarancji, rysunki techniczne.

Wejście (folder "18. Leroy Merlin - Portal\\materiały"):
  - 2026-03-26T13-41-37-moje-referencje.xlsx      eksport referencji z systemu LM (gama, EAN, kod dostawcy)
  - Etykiety Frigo i Ipsilon\\*\\SNS*.pdf          etykiety Sensea: logo, znak „YEAR Guarantee”, rysunek z wymiarami danego rozmiaru
  - Przegląd oferty (Leroy Merlin) 2025.09a A4.pdf  znaki „LAT GWARANCJI” Schedpol
  - 2026 - Paczka Ecommerce LEROY MERLIN\\...      rysunki techniczne pozostałych serii
Wyjście:
  assets/lm.js        nadpisuje p.g (gama) i dopisuje p.ean, p.sup wg eksportu LM
  assets/znaki/*.png  logo Sensea, znaki gwarancji
  assets/img/rys/*    rysunki techniczne;  assets/rysunki.js  (SP.rys: nr ref. → plik)
Użycie: python 8_zasoby_kart.py
"""
import os, sys, io, json, glob, re
import fitz, openpyxl
from PIL import Image, ImageOps

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(os.path.dirname(ROOT), "materiały")
ECOM = "\\\\?\\" + os.path.abspath(os.path.join(MAT, "2026 - Paczka Ecommerce LEROY MERLIN"))   # długie ścieżki Windows
ETYK = os.path.join(MAT, "Etykiety Frigo i Ipsilon")
PRZEGLAD = os.path.join(MAT, "Przegląd oferty (Leroy Merlin) 2025.09a A4.pdf")
XLSX = os.path.join(MAT, "2026-03-26T13-41-37-moje-referencje.xlsx")
OUT_Z = os.path.join(ROOT, "assets", "znaki")
OUT_R = os.path.join(ROOT, "assets", "img", "rys")


def products():
    s = io.open(os.path.join(ROOT, "assets", "data.js"), encoding="utf-8").read()
    return json.loads(s[s.index("window.SP = ") + 12: s.index(";\n\n/* ---- pomocnicze")])["products"]


# ---------- 1. eksport LM ----------
# Kształty, w których arkusz tytułów rozjeżdża się z nazwą w systemie LM, a LM ma rację (sprawdzone z etykietą/wymiarem).
# Uwaga: 95495956 („BALANS KW 120X90”) — błąd po stronie LM, w danych zostaje „prostokątny”.
SHAPE_FIX = {"45256512": "pięciokątny", "88758947": "pięciokątny", "82763748": "pięciokątny", "88758948": "pięciokątny",
             "82763752": "pięciokątny", "86448669": "prostokątny"}
def lm_export(P):
    ws = openpyxl.load_workbook(XLSX, data_only=True).active
    head = [str(c or "").strip() for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    ix = {k: head.index(k) for k in ("Referencja produktu", "GTIN (EAN)", "Referencja Dostawcy", "Nazwa produktu", "Gama")}
    L = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        ref = str(r[ix["Referencja produktu"]] or "").strip()
        if ref:
            L[ref] = {"g": str(r[ix["Gama"]] or "").strip(), "ean": str(r[ix["GTIN (EAN)"]] or "").strip(),
                      "sup": str(r[ix["Referencja Dostawcy"]] or "").strip(), "n": str(r[ix["Nazwa produktu"]] or "").strip()}
    refs = {p["ref"] for p in P}
    only_lm = {k: v["n"] for k, v in L.items() if k not in refs}
    only_data = sorted(refs - set(L))
    js = ("/* Wygenerowano z eksportu referencji LM (26.03.2026): gama, EAN, kod dostawcy. Ma pierwszeństwo przed przeglądem oferty. */\n"
          "(function (SP) {\n  var L = " + json.dumps({k: {x: v[x] for x in ("g", "ean", "sup")} for k, v in L.items() if k in refs}, ensure_ascii=False) + ";\n"
          "  SP.lmDate = '26.03.2026';\n  SP.lmOnly = " + json.dumps(only_lm, ensure_ascii=False) + ";\n"
          "  var SHAPE = " + json.dumps(SHAPE_FIX, ensure_ascii=False) + ";  /* kształt wg nazwy w systemie LM (arkusz tytułów był błędny) */\n"
          "  SP.products.forEach(function (p) { var x = L[p.ref]; if (x) { p.g = x.g; p.ean = x.ean; p.sup = x.sup; } else { p.g = ''; p.lmMissing = true; }\n"
          "    if (SHAPE[p.ref]) p.shape = SHAPE[p.ref]; });\n"
          "})(window.SP);\n")
    io.open(os.path.join(ROOT, "assets", "lm.js"), "w", encoding="utf-8").write(js)
    print("Eksport LM: %d ref.; tylko w eksporcie: %s; brak w eksporcie: %s" % (len(L), only_lm, only_data))
    return L


# ---------- 2. znaki ----------
def png_clip(page, rect, out, dpi=600):
    pix = page.get_pixmap(dpi=dpi, clip=rect, alpha=True)
    pix.save(out)
    return pix.width, pix.height


def znaki():
    os.makedirs(OUT_Z, exist_ok=True)
    fr = fitz.open(os.path.join(ETYK, "FRIGO 20.01.2025", "SNS4630.pdf"))[0]
    ip = fitz.open(os.path.join(ETYK, "IPSILON 18.10.2024", "SNS2248.pdf"))[0]
    logo = fitz.Rect()
    for d in fr.get_drawings():
        r = d["rect"]
        if r.y0 > 15 and r.y1 < 95 and r.x0 > 90 and r.x1 < 420:
            logo.include_rect(r)
    out = {"sensea": png_clip(fr, logo, os.path.join(OUT_Z, "sensea.png"))}
    badge = fitz.Rect(529.3, 489.6, 578.6, 538.9)           # granatowy znak „YEAR Guarantee” z etykiet
    out["gw-sensea-10"] = png_clip(fr, badge, os.path.join(OUT_Z, "gw-sensea-10.png"))
    out["gw-sensea-7"] = png_clip(ip, badge, os.path.join(OUT_Z, "gw-sensea-7.png"))
    po = fitz.open(PRZEGLAD)
    for key, pg, rect in (("gw-10", 12, fitz.Rect(512.7, 34.2, 579.7, 101.2)), ("gw-31", 20, fitz.Rect(515.9, 34.2, 582.9, 101.2)),
                          ("gw-7", 2, fitz.Rect(755.7, 177.4, 803.5, 226.2))):
        out[key] = png_clip(po[pg], rect, os.path.join(OUT_Z, key + ".png"))
    print("Znaki:", out)


# ---------- 3. rysunki ----------
def label_bound(page):
    D = page.get_drawings()
    ne = [d["rect"].y0 for d in D if d["rect"].y0 > 760 and d["rect"].width > 250 and d["rect"].height < 10 and "f" in d["type"]]
    box = [d["rect"].y0 - 16 for d in D if 780 < d["rect"].y0 < 1000 and d["rect"].width > 100 and d["rect"].height > 25 and "f" in d["type"]]
    yne = min(ne + box + [905])                            # nad linią „Ne contient pas…” i szarym polem piktogramów
    A = [d for d in D if 680 < d["rect"].y0 and d["rect"].y1 < yne - 1 and d["rect"].x0 > 110 and d["rect"].x1 < 370]
    S = fitz.Rect()
    for d in A:
        if "s" in d["type"] and d["rect"].y0 > 700:
            S.include_rect(d["rect"])
    u = fitz.Rect(S)
    for d in A:
        r = d["rect"]
        if "s" in d["type"]:
            continue
        cy = (r.y0 + r.y1) / 2
        rot = r.height > r.width * 1.2 and r.height > 9
        if (S.y0 - 2 <= cy <= S.y1 + 10 and S.x0 - 30 <= r.x0 and r.x1 <= S.x1 + 30) or \
           (rot and S.y0 - 22 <= r.y0 and r.y1 <= S.y1 + 10 and S.x0 - 30 <= r.x0 <= S.x1 + 30):
            u.include_rect(r)
    return u + (-4, -4, 4, 4)


def trim_save(im, out, maxpx=1700):
    im = im.convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageOps.invert(ImageOps.grayscale(Image.composite(im, bg, Image.new("L", im.size, 255))))
    box = diff.point(lambda v: 255 if v > 18 else 0).getbbox()
    if box:
        pad = int(max(im.size) * 0.015)
        im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad)))
    im.thumbnail((maxpx, maxpx), Image.LANCZOS)
    im.save(out, "PNG", optimize=True) if out.endswith(".png") else im.save(out, "JPEG", quality=86, optimize=True)
    return im.size


def open_src(path):
    if path.lower().endswith(".pdf"):
        pg = fitz.open(path)[0]
        pix = pg.get_pixmap(dpi=200)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    return im.convert("RGB")


import unicodedata


def _n(s):
    return unicodedata.normalize("NFC", s).lower().strip()


def E(*parts):
    """Ścieżka w paczce e-commerce odporna na NFC/NFD i wielkość liter w nazwach folderów."""
    cur = ECOM
    for part in parts:
        try:
            hit = [x for x in os.listdir(cur) if _n(x) == _n(part)]
        except OSError:
            return os.path.join(cur, *parts[parts.index(part):])
        cur = os.path.join(cur, hit[0] if hit else part)
    return cur
SHAPE = {"kwadratowy": "kw", "prostokątny": "pr", "półokrągły": "po", "pięciokątny": "pi"}
ECOM_MAP = {
    ("Balans", "kw"): E("BALANS", "RYSUNEK TECHNICZNY - WSZYTSKIE BRODZIKI", "BALANS 35mm 2021 (M3) kwadrat.png"),
    ("Balans", "pr"): E("BALANS", "RYSUNEK TECHNICZNY - WSZYTSKIE BRODZIKI", "BALANS LM 2026 - prostokąt.png"),
    ("Comfo", "kw"): E("COMFO", "1. Kwadrat", "3. Rysunek techniczny", "Rysunek_techniczny_Comfo_2500x2500px-300dpi_kwadrat_JPG.jpg"),
    ("Comfo", "po"): E("COMFO", "2. Półokragły", "3. Rysunek techniczny", "Rysunek_techniczny_Comfo_2500x2500px_300dpi_półokrągły_JPG.jpg"),
    ("Comfo", "pr"): E("COMFO", "3.Prostokąt", "2022 Rys tech Eko prostokąt 80x100cm.pdf"),
    ("Consist", "kw"): E("CONSIST", "Kwadrat", "3. Rys. Techniczny", "Rysunek_techniczny_Consist_2500x2500px_300dpi_kwadrat_JPG.jpg"),
    ("Consist", "pr"): E("CONSIST", "Prosotkąt", "3.Rys Techniczny", "Rysunek_techniczny_Consist_2500x2500px_300dpi_prostokąt_PDF.jpg"),
    ("Corrina", "kw"): E("CORRINA", "Kwadrat", "3. Rys techniczny", "Rysunek_techniczny_Corrina_2500x2500px_300dpi_kwadrat_JPG.jpg"),
    ("Dafne", "po"): E("DAFNE", "Półokrągły", "3. Rys techniczny", "Rysunek_techniczny_Dafne_2500x2500px_300dpi_półokrągły_JPG.jpg"),
    ("Dante", "kw"): E("DANTE", "1. Kwadrat", "3. Rys techniczny", "Rysunek_techniczny_Dante_2500x2500px_300dpi_kwadrat-JPG.jpg"),
    ("Dante", "po"): E("DANTE", "2. Półokrągły", "3. Rys. Techniczny", "Rysunek_techniczny_Dante_2500x2500px-300dpi_półokrągły_JPG.jpg"),
    ("Go Baby", "po"): E("GO BABY", "Półokragły", "3. Rys techniczny", "Rysunek_techniczny_Go_Baby_2500x2500px-300dpi_półokrągły_JPG.jpg"),
    ("Grawello", "kw"): E("GRAWELLO", "1. Kwdrat", "3. Rys techniczny", "Rysunek_Techniczny_Grawello_2500x2500p_300dpi_kwadrat_JPG.jpg"),
    ("Grawello", "po"): E("GRAWELLO", "2. Półokrągły", "3. Rys techniczny", "Rysunek_techniczny_Grawello_2500x2500px_300dpi_półokragły_JPG.jpg"),
    ("Grawello", "pr"): E("GRAWELLO", "3. Prostokąt", "3. Rys techniczny", "Rysunek_techniczny_Grawello_2500x2500px_300dpi_prostokąt-JPG.jpg"),
    ("Integral", "kw"): E("INTEGRAL", "White Stone", "1. Kwdrat", "3. Rys techniczny", "Rysunek_techniczny_Integral_2500x2500px_300dpi_JPG.jpg"),
    ("Integral", "pr"): E("INTEGRAL", "White Stone", "2. Prostokąt", "3. Rys techniczny", "Rysunek_techniczny_Integral_2500x2500px_300dpi_prostokąt_JPG.jpg"),
    ("Magnetic", "kw"): E("MAGNETIC", "2. Biały gładki", "1. KWADRAT", "2. RYSUNEK TECHNICZNY", "Rysunek_techniczny_Magnetic_Smooth-White_2500x2500px_300dpi_kwadrat_JPG.jpg"),
    ("Magnetic", "po"): E("MAGNETIC", "2. Biały gładki", "2. PÓŁOKRĄGŁY", "2. RYSUNEK TECHNICZNY", "Rysunek_techniczny_Magnetic_Smooth_White_2500x2500px_300dpi_półokragły_JPG.jpg"),
    ("Magnetic", "pr"): E("MAGNETIC", "2. Biały gładki", "3. PROSTOKĄT", "2. RYSUNEK TECHNICZNY", "Rysunek_techniczny_Magnetic_2500x2500px_300dpi_prostokąt_JPG.jpg"),
    ("Sinergid", "kw"): E("SINEGRID", "Sinegrid biały gładki", "1. kwadrat", "2. rysunek techniczny", "Rysunek_techniczny_sinegrid_Smooth_White_2500x2500px_300dpi_kwadrat_JPG.jpg"),
    ("Sinergid", "po"): E("SINEGRID", "Sinegrid biały gładki", "2. półokrągły", "2. rysunek techniczny", "Rysunek_techniczny_sinegrid_Smooth_White_2500x2500px_300dpi_półokrągły_JPG.jpg"),
    ("Sinergid", "pr"): E("SINEGRID", "Sinegrid biały gładki", "3. prostokąt", "2. rysunek techniczny", "Rysunek_Techniczny_Sinegrid_2500x2500px-300dpi_prostokąt_JPG.jpg"),
    ("Tebe", "kw"): E("TEBE", "Czarny Mat", "1. Kwadrat", "3. Rys techniczny", "Caspar New kwadratowe srodek Syfon 2023.jpg"),
    ("Tebe", "po"): E("TEBE", "Czarny Mat", "2. Półokrągły", "3. Rys techniczny", "Rysunek_techniczny_Tebe_Black_Stone_2500x2500p;x_300dpi_JPG.jpg"),
    ("Torres", "pr"): E("TORRES", "TORRES BIAŁY MAT", "3. Rys techniczny", "Rysunek_techniczny_torres_White_Mat_2500x2500p;x_300dpi_JPG.jpg"),
    ("Frigo", "kw"): E("FRIGO - sensea", "FRIGO BIAŁY GŁADKI", "GOTOWE PACZKI - PLIKI 300 DPI", "FRIGO BIAŁY GŁADKI KWADRAT", "3. RYS. TECHNICZNY", "RYS TECH. FRIGO KWADRAT 2026.png"),
    ("Frigo", "pr"): E("FRIGO - sensea", "FRIGO BIAŁY GŁADKI", "GOTOWE PACZKI - PLIKI 300 DPI", "FRIGO BIAŁY GŁADKI PROSTOKĄT", "3. RYS. TECHNICZNY", "RYS TECH. FRIGO BIAŁY GŁADKI PROSTOKĄT 2026 jpg.jpg"),
    ("Frigo", "po"): E("FRIGO - sensea", "FRIGO BIAŁY GŁADKI", "GOTOWE PACZKI - PLIKI 300 DPI", "FRIGO BIAŁY GŁADKI PÓŁOKRĄGŁY", "3. RYS. TECHNICZNY", "RYS TECH. FRIGO PÓŁOKRĄGŁY 2026. JPG.jpg"),
}


def ecom_file(p):
    fam, sh = p["fam"], SHAPE.get(p.get("shape") or "", "")
    if (fam, sh) in ECOM_MAP:
        return ECOM_MAP[(fam, sh)]
    if fam == "Ipsilon":
        f = {"kw": E("IPSILON", "IPSILON BIAŁY GŁADKI", "GOTOWE PACZKI - min. 2500x2500 300dpi", "IPSILON BIAŁY GŁADKI KWADRAT", "1. RYS. TECHNICZNY", "Rysunek techniczny ipsilon kwadrat JPG.jpg"),
             "po": E("IPSILON", "IPSILON Rysunki techniczne", "Ipsilon rys tech okragly 2020.png"),
             "pr": E("IPSILON", "IPSILON Rysunki techniczne", "IPSILON prostokąt 2022.png"),
             "pi": E("IPSILON", "IPSILON Rysunki techniczne", "Ipsilon %dx%d 2600px.png" % (p["a"], p["a"]))}
        return f.get(sh)
    if fam == "Frigo" and sh == "pi":
        return E("FRIGO - sensea", "FRIGO BIAŁY GŁADKI", "GOTOWE PACZKI - PLIKI 300 DPI", "FRIGO BIAŁY GŁADKI PIĘCIOKĄT", "3. RYS. TECHNICZNY",
                 "frigo pięciokąt %dx%d%s" % (p["a"], p["a"], ".jpg" if p["a"] == 80 else " jpg.jpg"))
    if fam == "Harmony":
        sub = "HARMONY PRIME" if "Prime" in p["s"] else "HARMONY"
        if "Black" in p["s"] or (p.get("c") == "czarny"):
            sub += " BLACK"
        f = glob.glob(E("ODPŁYWY LINIOWE", sub, "3. Rys techniczny", "*JPG.jpg"))
        return f[0] if f else None
    if fam == "Wall Comfort":
        thick = str(p.get("h")) == "6"
        d = E("ŚCIANKA", "2. Thick (6cm)", "1. Smooth White", "3. Rys techniczny") if thick else E("ŚCIANKA", "1. Thin (1cm)", "1. Smooth White Thin (1 cm)", "3. Rys techniczny")
        f = glob.glob(os.path.join(d, "*JPG.jpg"))
        return f[0] if f else None
    if fam == "Najazd":
        return E("NAJAZD DO BRODZIKÓW", "Najazd do brodzików - Smooth White", "3. rys. tech", "Rysunek_techniczny_najazd_podjazd_do_brodzików_2500x2500px_300dpi_JPG.jpg")
    if fam == "Maskownica Balans/Integral":
        return E("MASKOWNICE DO BRODZIKÓW BALANSINTEGRAL", "1.Maskownica złota", "3. Rys techniczny", "Rysunek_techniczny_Maskownica_Złota_2500x2500px_300dpi_JPG.jpg")
    if fam == "Nośnik":
        if p["ref"] in ("90151712", "90151713"):
            return E("NOŚNIK DO WANNY", "1.2 Nośnik do PROSTOKĄTNYCH wanien z podcięciem na stopy_led", "3. Rys techniczny",
                     "Rysunek_techniczny_nośnik_do_wanien_prostokątnych_z_podcięciem_na_stopy_led_2500x2500px_300dpi-JPG.jpg")
        if p["ref"] == "44054682":
            return E("NOŚNIK DO WANNY", "2. NOŚNIK DO WANIEN PÓŁOKRĄGŁYCH GAMA X", "3. Rys techniczny", "_Rysunek_techniczny_Elementy_nosnika_do_wanien_półokrągłych_2500x2500px_300dpi_JPG.jpg")
        return None                                         # 43732724: w paczce tylko „Nośniki Stabilsound – montaż” (inna technologia)
    return None


def rysunki(P, L):
    os.makedirs(OUT_R, exist_ok=True)
    R, cache, braki = {}, {}, []
    for p in P:
        sup = (L.get(p["ref"]) or {}).get("sup", "")
        lab = None
        if p["fam"] in ("Frigo", "Ipsilon") and sup:
            cand = glob.glob(os.path.join(ETYK, "*", sup.replace("/", "-") + ".pdf"))
            lab = cand[0] if cand else None
        if lab:
            key = "et-" + os.path.basename(lab)[:-4].lower()
            if key not in cache:
                pg = fitz.open(lab)[0]
                pix = pg.get_pixmap(dpi=300, clip=label_bound(pg))
                im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                cache[key] = trim_save(im, os.path.join(OUT_R, key + ".png"))
            R[p["ref"]] = {"f": key + ".png", "w": cache[key][0], "h": cache[key][1], "src": "etykieta " + os.path.basename(lab)}
            continue
        src = ecom_file(p)
        if not src or not os.path.exists(src):
            braki.append((p["ref"], p["fam"], p.get("shape"), src and os.path.basename(src)))
            continue
        key = "ec-" + re.sub(r"[^a-z0-9]+", "-", (p["fam"] + "-" + os.path.basename(src)).lower().encode("ascii", "ignore").decode())[:70].strip("-")
        if key not in cache:
            cache[key] = trim_save(open_src(src), os.path.join(OUT_R, key + ".png"))
        R[p["ref"]] = {"f": key + ".png", "w": cache[key][0], "h": cache[key][1], "src": "paczka e-commerce: " + os.path.relpath(src, ECOM)}
    js = "/* Wygenerowano: rysunki techniczne dla kart produktów (8_zasoby_kart.py). */\nwindow.SP.rys = " + json.dumps(R, ensure_ascii=False) + ";\n"
    io.open(os.path.join(ROOT, "assets", "rysunki.js"), "w", encoding="utf-8").write(js)
    n_et = sum(1 for v in R.values() if v["src"].startswith("etykieta"))
    print("Rysunki: %d indeksów (%d z etykiet, %d z paczki), plików: %d" % (len(R), n_et, len(R) - n_et, len(cache)))
    print("Bez rysunku (%d):" % len(braki))
    for b in braki:
        print("  ", b)


if __name__ == "__main__":
    P = products()
    L = lm_export(P)
    znaki()
    rysunki(P, L)
