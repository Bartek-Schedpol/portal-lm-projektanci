# -*- coding: utf-8 -*-
"""Logo z CorelDRAW z fontem SVG (<font><glyph>) → SVG z tekstem zamienionym na krzywe.
Przeglądarki nie obsługują fontów SVG, więc napis (np. „SINCE 1981”) bez konwersji znika.
Użycie: python logo_svg_do_krzywych.py <wejście.svg> <wyjście.svg>
"""
import re, sys, io

src, dst = sys.argv[1], sys.argv[2]
s = io.open(src, encoding="utf-8").read()
upm = float((re.search(r'units-per-em="([\d.]+)"', s) or [None, 1000])[1])
default_adv = float(re.search(r'<font [^>]*horiz-adv-x="([\d.]+)"', s).group(1))
glyphs = {}
for m in re.finditer(r'<glyph\s+unicode="([^"]*)"([^>]*?)/?>', s):
    attrs = m.group(2)
    adv = re.search(r'horiz-adv-x="([\d.]+)"', attrs)
    d = re.search(r'\sd="([^"]*)"', attrs)
    glyphs[m.group(1)] = (float(adv.group(1)) if adv else default_adv, d.group(1) if d else "")
classes = dict(re.findall(r"\.(\w+)\s*\{([^}]*)\}", s))


def text_to_path(m):
    x, y, cls, txt = float(m.group(1)), float(m.group(2)), m.group(3).split(), m.group(4)
    size = 16.0
    fill_cls = [c for c in cls if c.startswith("fil")]
    for c in cls:
        fs = re.search(r"font-size:([\d.]+)px", classes.get(c, ""))
        if fs:
            size = float(fs.group(1))
    k = size / upm
    out, cx = [], x
    for ch in txt:
        adv, d = glyphs.get(ch, (default_adv, ""))
        if d:
            out.append('<path class="%s" transform="translate(%.3f %.3f) scale(%.6f -%.6f)" d="%s"/>' % (" ".join(fill_cls), cx, y, k, k, d))
        cx += adv * k
    return "<g>" + "".join(out) + "</g>"


s = re.sub(r'<text x="([\d.]+)" y="([\d.]+)"\s+class="([^"]+)">([^<]*)</text>', text_to_path, s)
s = re.sub(r"<font\b.*?</font>", "", s, flags=re.S)          # font SVG niepotrzebny po konwersji
s = re.sub(r"\.fnt\d+\s*\{[^}]*\}", "", s)
io.open(dst, "w", encoding="utf-8").write(s)
print("OK:", dst, "glify:", len(glyphs), "upm:", upm)
