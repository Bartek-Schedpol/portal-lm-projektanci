# -*- coding: utf-8 -*-
"""Wybiera i optymalizuje zdjęcia z paczki materiałów do folderu makiet (assets/img)."""
import os, sys, io, json
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASES = {
    "p": "\\\\?\\" + ROOT + r"\materiały\2026 - Paczka Ecommerce LEROY MERLIN",
    "e": "\\\\?\\" + ROOT + r"\materiały\LEROY MERLIN - poprawki po Empco",
}
OUT = ROOT + r"\koncepcja-portalu\assets\img"
os.makedirs(OUT, exist_ok=True)

EXCL = ["szki", "szkic", "brief", "\\nie\\", "frigo - sensea\\frigo\\"]
index = {}
for k, b in BASES.items():
    lst = []
    for dp, dn, fn in os.walk(b):
        low = dp.lower() + "\\"
        if any(e in low for e in EXCL):
            continue
        for f in fn:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                lst.append(os.path.join(dp, f))
    index[k] = lst

def find(base, must, prefer=("png", "jpg")):
    must = [m.lower() for m in must]
    c = [p for p in index[base] if all(m in p[len(BASES[base]):].lower() for m in must)]
    if not c:
        return None
    def rank(p):
        ext = p.lower().rsplit(".", 1)[-1].replace("jpeg", "jpg")
        return (prefer.index(ext) if ext in prefer else 9, len(os.path.basename(p)), p)
    return sorted(c, key=rank)[0]

J = ("jpg", "png")
SPEC = [
    # --- sceny (hero / kwadrat) ---
    ("wc-po", "p", ["aranżacje", "po wall comfort"], "hero", J),
    ("wc-przed", "p", ["aranżacje", "przed wanna"], "hero", J),
    ("odplyw-scena", "p", ["odpływy liniowe\\aranżacje", "u01.png"], "hero", J),
    ("odplyw-detal", "p", ["odpływy liniowe\\aranżacje", "u02.0"], "sq", J),
    ("odplyw-black", "p", ["harmony black\\1. aranżacja", "wersja_1"], "sq", J),
    ("odplyw-prime", "p", ["harmony prime\\1. aranżacja", "wersja_1"], "sq", J),
    ("balans-ws-a", "p", ["balans biały kamień kwadrat\\3. aranżacja", "aranżacja 2"], "sq", J),
    ("balans-ws-b", "p", ["balans biały kamień kwadrat\\3. aranżacja", "aranżacja balans ws"], "sq", J),
    ("balans-bs-a", "p", ["balans czarny kamień kwadrat\\3. aranżacja", "struktura kamienista"], "sq", J),
    ("balans-bs-b", "p", ["balans czarny kamień kwadrat\\3. aranżacja", "aranżacja balans bs"], "sq", J),
    ("balans-cas", "p", ["balans kaszmirowy kamień kwadrat\\3. aranżacja"], "sq", J),
    ("balans-gs", "p", ["balans szary kamień kwadrat\\3. aranżacja"], "sq", J),
    ("consist", "p", ["consist\\kwadrat\\1. aranżacja"], "sq", J),
    ("consist-rect", "p", ["consist\\prosotkąt\\1. aranżacja"], "sq", J),
    ("integral-bs", "p", ["integral\\black stone\\1. kwadrat\\1. aranżacja"], "sq", J),
    ("integral-ws", "p", ["integral\\white stone\\1. kwdrat\\1. aranżacja"], "sq", J),
    ("ipsilon-sw", "p", ["ipsilon biały gładki kwadrat\\3. aranżacje"], "sq", J),
    ("ipsilon-bs", "p", ["ipsilon czarny kamień kwadrat\\3. aranżacje"], "sq", J),
    ("frigo-sw", "p", ["frigo - sensea\\frigo biały gładki", "kwadrat\\2. aranżacja", "kwadrat 1"], "sq", J),
    ("frigo-bs", "p", ["frigo - sensea\\frigo czarny kamień", "1. kwadrat\\1. aranżacja", "kwadrat.jpg"], "sq", J),
    ("tebe", "p", ["tebe\\czarny mat\\1. kwadrat\\1. aranżacja"], "sq", J),
    ("torres-w", "p", ["torres biały mat\\1. aranżacja"], "sq", J),
    ("torres-b", "p", ["torres czarny mat\\1. aranżacja"], "sq", J),
    ("obudowa-led", "p", ["zabudowa wanny\\1.", "1. z podcięciem", "aranżacja"], "sq", J),
    ("obudowa-pol", "p", ["zabudowa wanny\\2.", "1. z podcięciem", "aranżacja"], "sq", J),
    ("nosnik", "p", ["nośnik do wanny\\1.2", "aranżacja"], "sq", J),
    ("najazd-a", "p", ["najazd do brodzików - smooth white\\1. aranżacja", "#2"], "sq", J),
    ("najazd-b", "p", ["najazd do brodzików - smooth white\\1. aranżacja", "jpg.jpg"], "sq", J),
    ("comfo", "p", ["comfo\\1. kwadrat\\1. aranżacja"], "sq", J),
    ("dante", "p", ["dante\\2. półokrągły\\1. aranżacja"], "sq", J),
    ("grawello", "p", ["grawello\\2. półokrągły\\1. aranżacja", "jpg.jpg"], "sq", J),
    ("gobaby", "p", ["go baby\\półokragły\\1. aranżacja"], "sq", J),
    ("dafne", "p", ["dafne\\półokrągły\\1. aranżacja", "jpg.jpg"], "sq", J),
    ("corrina", "p", ["corrina\\kwadrat\\1. aranżacja", "jpg.jpg"], "sq", J),
    ("balans-zoom-ws", "p", ["balans biały kamień", "balans - zoom.jpg"], "sq", J),
    ("balans-zoom-bs", "p", ["balans czarny kamień", "balans - zoom (2)"], "sq", J),
    ("balans-cut", "p", ["balans biały kamień prostokąt\\5. dodatkowe", "balans 300 dpi jpg"], "sq", J),
    ("balans-feet", "p", ["rich content premium", "cisza i przyjemne"], "sq", J),
    ("balans-clean", "p", ["rich content premium", "czystość bez"], "sq", J),
    # --- tekstury / próbki powierzchni ---
    ("tex-white-stone", "p", ["balans biały kamień kwadrat\\5. zdjęcia dodatkowe", "tekstura"], "tex", J),
    ("tex-black-stone", "p", ["balans czarny kamień kwadrat\\zdjęcia dodatkowe", "tekstura"], "tex", J),
    ("tex-cashmere", "p", ["balans kaszmirowy kamień", "bezszwowy kaszmir"], "tex", J),
    ("tex-grey-stone", "p", ["balans szary kamień", "tekstura - szar"], "tex", J),
    ("wc-tex-sw", "p", ["ścianka\\1. thin (1cm)\\1. smooth white", "1. aranżacja"], "tex", J),
    ("wc-tex-bs", "p", ["ścianka\\1. thin (1cm)\\2. black stone", "1. aranżacja"], "tex", J),
    ("wc-tex-ws", "p", ["ścianka\\1. thin (1cm)\\3. white stone", "1. aranżacja"], "tex", J),
    ("wc-tex-gs", "p", ["ścianka\\1. thin (1cm)\\4. greystone", "1. aranżacja"], "tex", J),
    # --- rysunki / infografiki po EmpCo ---
    ("draw-balans-sq", "p", ["balans biały kamień kwadrat\\1. rys techniczny"], "draw", J),
    ("draw-balans-rect", "p", ["balans biały kamień prostokąt\\1. rys techniczny"], "draw", ("png", "jpg")),
    ("info-balans", "e", ["balans\\1. biały kamień\\1. kwadrat", "infografika"], "info", ("png", "jpg")),
    ("info-frigo", "e", ["frigo\\1. biały gładki\\4 kwadrat"], "info", ("png", "jpg")),
    ("info-ipsilon", "e", ["ipsilon\\4. biały gładki\\1. kwadrat"], "info", ("png", "jpg")),
    # --- packshoty (przezroczyste tło) ---
    ("p-balans-ws", "p", ["balans biały kamień kwadrat\\2. packshot", "#2 png"], "pack", None),
    ("p-balans-ws-top", "p", ["balans biały kamień kwadrat\\2. packshot", "#3 png"], "pack", None),
    ("p-balans-ws-rect", "p", ["balans biały kamień prostokąt\\2. packshot", "#2 png"], "pack", None),
    ("p-balans-bs", "p", ["balans czarny kamień kwadrat\\2. packshot", "kwadrat.png"], "pack", None),
    ("p-balans-cas", "p", ["balans kaszmirowy kamień kwadrat\\2. packshot", "kwadrat png.png"], "pack", None),
    ("p-balans-gs", "p", ["balans szary kamień kwadrat\\2. packshot", "300dpi. png.png"], "pack", None),
    ("p-magnetic-ws", "p", ["magnetic\\1. biała struktura\\1. kwadrat\\1. packshot", "png.png"], "pack", None),
    ("p-magnetic-sw", "p", ["magnetic\\2. biały gładki\\1. kwadrat\\1. packshot", "png.png"], "pack", None),
    ("p-magnetic-bs", "p", ["magnetic\\3. czarny strukturalny\\1. kwadrat\\1. packshot", "png.png"], "pack", None),
    ("p-magnetic-gs", "p", ["magnetic\\4. szary\\1. kwadrat", "pack"], "pack", None),
    ("p-magnetic-r55", "p", ["magnetic\\2. biały gładki\\2. półokrągły\\1. packshot", "png.png"], "pack", None),
    ("p-ipsilon-sw", "p", ["ipsilon biały gładki kwadrat\\2. packshot", "kwadrat png.png"], "pack", None),
    ("p-ipsilon-r55", "p", ["ipsilon biały gładki półokrągły\\2. packshot", "półokrągły. png.png"], "pack", None),
    ("p-ipsilon-5", "p", ["ipsilon biały gładki pięciokąt\\2. packshot", "pięciokąt. png.png"], "pack", None),
    ("p-ipsilon-rect", "p", ["ipsilon biały gładki prostokąt\\2. packshot", "prostokąt png.png"], "pack", None),
    ("p-ipsilon-bs", "p", ["ipsilon czarny kamień kwadrat", "pack"], "pack", None),
    ("p-ipsilon-gs", "p", ["ipsilon szary kamień kwadrat", "pack"], "pack", None),
    ("p-ipsilon-ws", "p", ["ipsilon biały kamień kwadrat", "pack"], "pack", None),
    ("p-frigo-sw", "p", ["frigo - sensea\\frigo biały gładki", "kwadrat\\1. packshot", "kwadrat png.png"], "pack", None),
    ("p-frigo-ws", "p", ["frigo - sensea\\frigo biały kamień", "kwadrat", "pack"], "pack", None),
    ("p-frigo-bs", "p", ["frigo - sensea\\frigo czarny kamień", "kwadrat", "pack"], "pack", None),
    ("p-frigo-gs", "p", ["frigo - sensea\\frigo szary kamień", "kwadrat", "pack"], "pack", None),
    ("p-sinegrid-sw", "p", ["sinegrid\\sinegrid biały gładki\\1. kwadrat", "pack"], "pack", None),
    ("p-sinegrid-bm", "p", ["sinegrid\\sinegrid black mat\\1. kwadrat", "pack"], "pack", None),
    ("p-sinegrid-ws", "p", ["sinegrid\\sinegrid white stone\\1. kwadrat", "pack"], "pack", None),
    ("p-integral-bs", "p", ["integral\\black stone\\1. kwadrat\\2. packshot", "png.png"], "pack", None),
    ("p-integral-ws", "p", ["integral\\white stone\\1. kwdrat\\2. packshot", "png.png"], "pack", None),
    ("p-consist", "p", ["consist\\kwadrat\\2. packshot", "kwadrat"], "pack", None),
    ("p-comfo", "p", ["comfo\\1. kwadrat\\2. packshot"], "pack", None),
    ("p-corrina", "p", ["corrina\\kwadrat\\2. packshot", "png #2"], "pack", None),
    ("p-dafne", "p", ["dafne\\półokrągły\\2. packshoty", "png.png"], "pack", None),
    ("p-dante", "p", ["dante\\2. półokrągły\\2. packshot"], "pack", None),
    ("p-gobaby", "p", ["go baby\\półokragły\\2. packshot", "png.png"], "pack", None),
    ("p-grawello", "p", ["grawello\\1. kwdrat\\2. packshot", "png.png"], "pack", None),
    ("p-tebe", "p", ["tebe\\czarny mat\\1. kwadrat", "pack"], "pack", None),
    ("p-torres-w", "p", ["torres biały mat", "pack"], "pack", None),
    ("p-torres-b", "p", ["torres czarny mat", "pack"], "pack", None),
    ("p-harmony", "p", ["odpływy liniowe\\harmony\\", "pack"], "pack", None),
    ("p-harmony-black", "p", ["odpływy liniowe\\harmony black\\", "pack"], "pack", None),
    ("p-harmony-prime", "p", ["odpływy liniowe\\harmony prime\\", "pack"], "pack", None),
    ("p-harmony-prime-black", "p", ["odpływy liniowe\\harmony prime black\\", "pack"], "pack", None),
    ("p-wall-sw", "p", ["ścianka\\1. thin (1cm)\\1. smooth white", "pack"], "pack", None),
    ("p-wall-bs", "p", ["ścianka\\1. thin (1cm)\\2. black stone", "pack"], "pack", None),
    ("p-wall-ws", "p", ["ścianka\\1. thin (1cm)\\3. white stone", "pack"], "pack", None),
    ("p-wall-gs", "p", ["ścianka\\1. thin (1cm)\\4. greystone", "pack"], "pack", None),
    ("p-wall6-sw", "p", ["ścianka\\2. thick (6cm)\\1. smooth white", "pack"], "pack", None),
    ("p-nosnik-wanna", "p", ["nośnik do wanny\\1.2", "pack"], "pack", None),
    ("p-nosnik-polokr", "p", ["nośnik do wanny\\2.", "pack"], "pack", None),
    ("p-nosnik-prost", "p", ["nośnik do wanny\\1.1", "pack"], "pack", None),
    ("p-obudowa-pr", "p", ["zabudowa wanny\\1.", "2. bez podcięcia", "pack"], "pack", None),
    ("p-obudowa-pol-led", "p", ["zabudowa wanny\\2.", "1. z podcięciem", "pack"], "pack", None),
    ("p-obudowa-pol", "p", ["zabudowa wanny\\2.", "2. bez podcięcia", "pack"], "pack", None),
    ("p-nosnik-brodzik", "p", ["nośnik dla brodzika", "pack"], "pack", None),
    ("p-obudowa", "p", ["zabudowa wanny\\1.", "1. z podcięciem", "pack"], "pack", None),
    ("p-najazd", "p", ["najazd do brodzików - smooth white", "pack"], "pack", None),
    ("p-maskownica-zlota", "p", ["maskownice", "1.maskownica złota", "pack"], "pack", None),
    ("p-maskownica-szczot", "p", ["maskownice", "2. maskownica złota szczotkowana", "pack"], "pack", None),
    ("p-maskownica-miedz", "p", ["maskownice", "3. maskownica", "pack"], "pack", None),
    ("p-panel-gobaby", "p", ["panele do brodzików\\1. panel go baby", "pack"], "pack", None),
    ("p-panel-dante", "p", ["panele do brodzików\\4. panel dante", "pack"], "pack", None),
    ("p-nogi", "p", ["nogi do brodzików"], "pack", None),
]

def flatten(im, bg=(255, 255, 255)):
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        b = Image.new("RGB", im.size, bg)
        b.paste(im, mask=im.split()[-1])
        return b
    return im.convert("RGB")

manifest, missing = {}, []
for name, base, must, kind, prefer in SPEC:
    src = find(base, must, prefer or ("png", "jpg"))
    if not src:
        missing.append(name); continue
    try:
        im = Image.open(src)
        ow, oh = im.size
        if kind == "pack":
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            if has_alpha:
                im = im.convert("RGBA")
                bb = im.getbbox()
                if bb: im = im.crop(bb)
                im.thumbnail((760, 760), Image.LANCZOS)
                fn = name + ".webp"; im.save(os.path.join(OUT, fn), "WEBP", quality=86, method=6)
            else:
                im = im.convert("RGB"); im.thumbnail((760, 760), Image.LANCZOS)
                fn = name + ".jpg"; im.save(os.path.join(OUT, fn), "JPEG", quality=84, optimize=True, progressive=True)
            alpha = has_alpha
        else:
            alpha = False
            im = flatten(im)
            mx = {"hero": 1920, "sq": 1200, "tex": 720, "draw": 1400, "info": 1400}[kind]
            im.thumbnail((mx, mx), Image.LANCZOS)
            q = {"hero": 80, "sq": 80, "tex": 82, "draw": 90, "info": 86}[kind]
            fn = name + ".jpg"; im.save(os.path.join(OUT, fn), "JPEG", quality=q, optimize=True, progressive=True)
        manifest[name] = {"file": fn, "w": im.width, "h": im.height, "kind": kind, "alpha": alpha,
                          "src": src[len(BASES[base]) + 1:], "base": base, "orig": [ow, oh]}
    except Exception as e:
        missing.append(name + " ERR " + str(e)[:80])

# flaga faktycznie przezroczystego tła (rogi z alfą bliską 0) — makiety używają jej do doboru sposobu wyświetlania
for n, m in manifest.items():
    tb = False
    if m["file"].endswith(".webp"):
        im2 = Image.open(os.path.join(OUT, m["file"])).convert("RGBA")
        w2, h2 = im2.size
        corners = [im2.getpixel(xy)[3] for xy in ((1, 1), (w2 - 2, 1), (1, h2 - 2), (w2 - 2, h2 - 2))]
        tb = sum(1 for a in corners if a < 20) >= 3
    m["tb"] = tb

json.dump(manifest, open(os.path.join(os.path.dirname(OUT), "img-manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
tot = sum(os.path.getsize(os.path.join(OUT, m["file"])) for m in manifest.values())
print("zapisano:", len(manifest), "plików,", round(tot / 1e6, 1), "MB | brak:", missing)

# arkusz kontrolny wyników
names = list(manifest)
cols, tw, th, pad = 8, 220, 220, 22
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + pad)), (225, 225, 225))
dr = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("arial.ttf", 12)
except Exception: font = ImageFont.load_default()
for i, n in enumerate(names):
    im = Image.open(os.path.join(OUT, manifest[n]["file"]))
    im = flatten(im, (200, 205, 210)); im.thumbnail((tw - 6, th - 6))
    x, y = (i % cols) * tw, (i // cols) * (th + pad)
    sheet.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
    dr.text((x + 3, y + th + 3), n + (" α" if manifest[n]["alpha"] else ""), fill="black", font=font)
sheet.save(sys.argv[1], quality=80)
