# -*- coding: utf-8 -*-
"""Zrzuty ekranów makiet i PDF opracowania (Edge w trybie bezokienkowym, osobny profil tymczasowy).

Wymaga działającego podglądu:  python -m http.server 8766 --directory "<...>\\koncepcja-portalu"
Użycie:
  python 6_zrzuty_i_pdf.py zrzuty            -> koncepcja-portalu\\zrzuty\\*.png  (1440×900, bez paska prezentera)
  python 6_zrzuty_i_pdf.py kontrola <folder> -> wysokie zrzuty kontrolne + błędy konsoli (do przeglądu jakości)
  python 6_zrzuty_i_pdf.py pdf               -> „Portal LM — koncepcja i plan funkcjonalny.pdf”
"""
import os, sys, io, subprocess, tempfile, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = "http://localhost:8766/"
EDGE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"   # Chrome: Edge 157 bez okna nie drukuje PDF (11.2026)
if not os.path.exists(EDGE):
    EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SHOTS = [
    ("a-1-start", "a-biblioteka/index.html?clean=1#/start"),
    ("a-2-katalog", "a-biblioteka/index.html?clean=1#/katalog"),
    ("a-3-produkt", "a-biblioteka/index.html?clean=1#/produkt?ref=89189409"),
    ("a-4-pliki", "a-biblioteka/index.html?clean=1#/pliki"),
    ("b-1-pulpit", "b-pracownia/index.html?clean=1#/pulpit"),
    ("b-2-dobor", "b-pracownia/index.html?clean=1#/dobor?w=100&d=80"),
    ("b-3-produkt", "b-pracownia/index.html?clean=1#/produkt?ref=89189409"),
    ("b-4-specyfikacja", "b-pracownia/index.html?clean=1#/specyfikacja"),
    ("c-1-start", "c-showroom/index.html?clean=1#/start"),
    ("c-2-kolekcje", "c-showroom/index.html?clean=1#/kolekcje"),
    ("c-3-seria", "c-showroom/index.html?clean=1#/seria?fam=Balans"),
    ("c-4-akademia", "c-showroom/index.html?clean=1#/akademia"),
]


def run(args, profile):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--disable-extensions", "--force-prefers-reduced-motion",
           "--user-data-dir=" + profile, "--enable-logging=stderr", "--log-level=0"] + args
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    cons = [l for l in p.stderr.splitlines() if "CONSOLE" in l]
    return cons


def shot(url, out, w, h, profile, budget=9000):
    return run(["--window-size=%d,%d" % (w, h), "--virtual-time-budget=%d" % budget, "--screenshot=" + out, BASE + url], profile)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "zrzuty"
    profile = tempfile.mkdtemp(prefix="edge-makiety-")
    try:
        if mode == "zrzuty":
            out = os.path.join(ROOT, "zrzuty"); os.makedirs(out, exist_ok=True)
            for name, url in SHOTS:
                cons = shot(url, os.path.join(out, name + ".png"), 1440, 900, profile)
                print(name, "OK" if os.path.exists(os.path.join(out, name + ".png")) else "BRAK", "| konsola:", len(cons))
        elif mode == "kontrola":
            out = sys.argv[2]; os.makedirs(out, exist_ok=True)
            only = sys.argv[3] if len(sys.argv) > 3 else ""
            for name, url in SHOTS:
                if only and not name.startswith(only):
                    continue
                for tag, (w, h) in (("d", (1440, 2600)), ("m", (500, 2600))):  # Edge bez okna nie renderuje węższego układu niż ~500 px
                    cons = shot(url, os.path.join(out, "%s_%s.png" % (name, tag)), w, h, profile)
                    errs = [c for c in cons if "error" in c.lower() or "uncaught" in c.lower() or "failed" in c.lower()]
                    print(name, tag, "| komunikaty konsoli:", len(cons), "| błędy:", len(errs))
                    for e in errs[:6]:
                        print("    ", e[e.find("CONSOLE"):][:300])
        elif mode == "pdf":
            pdf = os.path.join(ROOT, "Portal LM — koncepcja i plan funkcjonalny.pdf")
            run(["--virtual-time-budget=12000", "--no-pdf-header-footer", "--print-to-pdf=" + pdf, BASE + "index.html?druk=1"], profile)
            print("PDF:", pdf, os.path.getsize(pdf) if os.path.exists(pdf) else "BRAK")
    finally:
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
