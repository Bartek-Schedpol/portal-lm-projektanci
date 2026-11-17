import os
# -*- coding: utf-8 -*-
"""Buduje znormalizowany zbiór produktów LM (z arkusza tytułów + gama z PDF przeglądu oferty)."""
import json, re, sys, io, collections
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SP = sys.argv[1]
PDF = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), r"materiały\Przegląd oferty (Leroy Merlin) 2025.09a A4.pdf")

rows = json.load(open(SP + "/products.json", encoding="utf-8"))

# ---------- gama + wymiar z PDF (pozycyjnie: kod gamy na lewo od chipa z nr ref.) ----------
gama, pdfdim = {}, {}
doc = fitz.open(PDF)
for pno, page in enumerate(doc):
    words = page.get_text("words")  # x0,y0,x1,y1,text,...
    refs = [w for w in words if re.fullmatch(r"\d{8}", w[4])]
    for r in refs:
        cy = (r[1] + r[3]) / 2
        left = [w for w in words if abs((w[1] + w[3]) / 2 - cy) < 4 and w[2] <= r[0] + 1 and r[0] - w[2] < 30
                and re.fullmatch(r"(SFP/)?[ABCXL]", w[4])]
        if left:
            left.sort(key=lambda w: r[0] - w[2])
            gama[r[4]] = left[0][4]
        right = [w for w in words if abs((w[1] + w[3]) / 2 - cy) < 4 and w[0] >= r[2] - 1 and w[0] - r[2] < 26]
        if right:
            right.sort(key=lambda w: w[0])
            pdfdim[r[4]] = " ".join(w[4] for w in right[:3])

# ---------- normalizacja ----------
SERIES = {
    "BALANS": ("Balans", "brodzik", "kompozytowy", "Stabilsafe"),
    "Magnetic": ("Magnetic", "brodzik", "kompozytowy", "Stabilsafe"),
    "IPSILON": ("Ipsilon", "brodzik", "laminowany", "Standard Plus"),
    "FRIGO": ("Frigo", "brodzik", "zintegrowany", "Stabilsafe"),
    "Sinergid": ("Sinergid", "brodzik", "zintegrowany", "Stabilsafe"),
    "Integral": ("Integral", "brodzik", "zintegrowany", "Stabilsafe"),
    "Consist": ("Consist", "brodzik", "zintegrowany", "Stabilsafe"),
    "GRAWELLO": ("Grawello", "brodzik", "zintegrowany", "Stabilsafe"),
    "DANTE": ("Dante", "brodzik", "zintegrowany", "Stabilsafe"),
    "GO BABY": ("Go Baby", "brodzik", "zintegrowany", "Stabilsafe"),
    "DAFNE": ("Dafne", "brodzik", "laminowany", "Standard Plus"),
    "COMFO": ("Comfo", "brodzik", "laminowany", "Standard Plus"),
    "CORRINA": ("Corrina", "brodzik", "laminowany", "Standard Plus"),
    "TEBE": ("Tebe", "brodzik", "laminowany", "Standard Plus"),
    "TORRES": ("Torres", "wanna", "laminowana", "Standard Plus"),
    "ODPŁYW LINIOWY": ("Harmony", "odpływ liniowy", "", ""),
    "ŚCIANKA WALL COMFORT": ("Wall Comfort", "panel ścienny", "", ""),
    "NOSNIK": ("Nośnik", "nośnik", "EPS", ""),
    "ZABUDOWA DO WAN": ("Obudowa uniwersalna", "obudowa", "", ""),
    "OSLONA BALANS/INTEGRAL": ("Maskownica Balans/Integral", "akcesoria", "", ""),
    "PANEL GRAWELLO": ("Panel Grawello", "akcesoria", "", ""),
    "PANEL DANTE": ("Panel Dante", "akcesoria", "", ""),
    "PANEL GO BABY": ("Panel Go Baby", "akcesoria", "", ""),
    "PANEL DAFNE": ("Panel Dafne", "akcesoria", "", ""),
    "NAJAZD": ("Najazd", "akcesoria", "", ""),
    "NOGI IPSILON": ("Nogi Ipsilon", "akcesoria", "", ""),
}

def shape_of(t):
    tl = t.lower()
    if "kwadrat" in tl: return "kwadratowy"
    if "prostok" in tl: return "prostokątny"
    if "półokr" in tl or "polokr" in tl or "półokrąg" in tl: return "półokrągły"
    if "pięciok" in tl or "pieciok" in tl: return "pięciokątny"
    return ""

COLORS = [
    (r"bia\w+\s+kamie", "biały kamień", "White Stone", "RAL 9016", "#EDEDEA"),
    (r"czarn\w+\s+kamie", "czarny kamień", "Black Stone", "RAL 9004", "#2A2A2B"),
    (r"szar\w+\s+kamie", "szary kamień", "Grey Stone", "RAL 7012", "#575D5E"),
    (r"antracyt", "antracytowy kamień", "Grey Stone", "RAL 7012", "#575D5E"),
    (r"cement", "cementowy kamień", "Cement Stone", "RAL 7038", "#B0B3AF"),
    (r"kaszmir|beż", "kaszmirowy kamień", "Cashmere Stone", "RAL 9001", "#E9E0D2"),
    (r"czarn\w+\s+mat", "czarny mat", "Black Mat", "RAL 9005", "#1B1B1C"),
    (r"bia\w+\s+mat", "biały mat", "White Mat", "RAL 9003", "#F4F4F2"),
    (r"bia\w+\s+g[łl]adk", "biały gładki", "Smooth White", "RAL 9003", "#F7F7F5"),
    (r"z[łl]ot\w+\s+szczotk", "złota szczotkowana", "", "", "#C8A66B"),
    (r"z[łl]ot", "złota polerowana", "", "", "#D4B06A"),
    (r"miedz|miedź", "miedziana", "", "", "#B87A56"),
    (r"black", "czarny", "Black", "", "#1B1B1C"),
    (r"chrom", "chrom", "", "", "#C9CCCF"),
    (r"czarn", "czarny", "Black Stone", "RAL 9004", "#2A2A2B"),
    (r"szar", "szary kamień", "Grey Stone", "RAL 7012", "#575D5E"),
    (r"bia[łl]", "biały", "Smooth White", "RAL 9003", "#F7F7F5"),
]

def color_of(t):
    tl = t.lower()
    for rx, pl, en, ral, hx in COLORS:
        if re.search(rx, tl):
            return pl, en, ral, hx
    return "", "", "", ""

def dims_of(t):
    s = t.replace("×", "x").replace("X", "x").replace(",", ".")
    m = re.search(r"(\d{2,3}(?:-\d{2,3})?)\s*x\s*(\d{2,3})\s*(?:x\s*([\d.]+(?:/[\d.]+)?))?", s)
    if not m:
        m2 = re.search(r"(\d{3,4})\s*mm", s)
        if m2: return (int(m2.group(1)) // 10, None, None)
        return (None, None, None)
    a, b, h = m.group(1), int(m.group(2)), m.group(3)
    a = int(a) if a.isdigit() else a
    return (a, b, h)

out, issues = [], []
for r in rows:
    key = r["seria"]
    name, cat, tech, techname = SERIES.get(key, (key.title(), "inne", "", ""))
    title = re.sub(r"\s+", " ", r["new"] or r["old"]).strip()
    brand = "Sensea" if "sensea" in title.lower() else "Schedpol"
    sh = shape_of(title) if cat in ("brodzik", "wanna", "akcesoria", "obudowa") else ""
    cpl, cen, ral, hx = color_of(title)
    a, b, h = dims_of(title)
    if cat == "odpływ liniowy":
        t = title.lower()
        name = "Harmony Prime Black" if "prime black" in t else "Harmony Prime" if "prime" in t else "Harmony Black" if "black" in t else "Harmony"
        cpl, cen, ral, hx = ("czarny", "", "", "#1B1B1C") if "black" in t else ("stal", "", "", "#C9CCCF")
    if cat == "panel ścienny":
        m = re.search(r"210\s*x\s*100\s*x\s*(\d)", title.lower().replace("×", "x"))
        h = m.group(1) if m else h
        a, b = 210, 100
        if not cpl or cpl == "biały": cpl, cen, ral, hx = "biały gładki", "Smooth White", "RAL 9003", "#F7F7F5"
    item = {
        "ref": r["ref"], "s": name, "sk": key, "cat": cat, "tech": tech, "tn": techname, "brand": brand,
        "shape": sh, "a": a, "b": b, "h": h, "c": cpl, "ce": cen, "ral": ral, "hx": hx,
        "g": gama.get(r["ref"], ""), "pd": pdfdim.get(r["ref"], ""), "t": title,
    }
    if cat in ("brodzik", "wanna") and (a is None or not sh):
        issues.append(("BRAK wym./kształtu", item["ref"], title))
    if cat in ("brodzik", "wanna") and not cpl:
        issues.append(("BRAK koloru", item["ref"], title))
    out.append(item)

json.dump(out, open(SP + "/data_products.json", "w", encoding="utf-8"), ensure_ascii=False)
print("PRODUKTY:", len(out), "| z gamą z PDF:", sum(1 for o in out if o["g"]), "| refs w PDF:", len(gama))
print("kategorie:", collections.Counter(o["cat"] for o in out).most_common())
print("marki:", collections.Counter(o["brand"] for o in out).most_common())
print("kształty:", collections.Counter(o["shape"] for o in out).most_common())
print("kolory:", collections.Counter(o["c"] for o in out).most_common())
print("gamy:", collections.Counter(o["g"] for o in out).most_common())
print("serie:", collections.Counter(o["s"] for o in out).most_common())
print("--- PROBLEMY:", len(issues))
for i in issues[:40]: print("  ", i)
# kontrola: wymiar z tytułu vs wymiar z PDF
mis = 0
for o in out:
    if o["pd"] and o["a"] and isinstance(o["a"], int):
        nums = re.findall(r"\d+", o["pd"].replace(",", "."))[:2]
        if len(nums) == 2 and {int(nums[0]), int(nums[1])} != {o["a"], o["b"]}:
            mis += 1
            if mis <= 12: print("  ROZJAZD wym.:", o["ref"], "| tytuł:", o["a"], o["b"], "| PDF:", o["pd"], "|", o["t"][:70])
print("rozjazdów wymiarów tytuł↔PDF:", mis)
print("refs w PDF, których nie ma w arkuszu:", len(set(gama) - {o['ref'] for o in out}), sorted(set(gama) - {o['ref'] for o in out})[:30])
print("refs w arkuszu bez gamy w PDF:", len([o for o in out if not o['g']]))
