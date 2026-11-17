# Strefa projektanta Schedpol × Leroy Merlin — makieta

Klikalna makieta portalu dla projektantów sieci Leroy Merlin (koncepcja A „Biblioteka”):
wyszukiwarka po numerze referencyjnym LM, katalog z filtrami, karta produktu z plikami do pobrania,
Centrum plików z paczkami serii, teczka plików oraz karty produktów PDF (A4) dla 371 indeksów.

**Podgląd:** https://bartek-schedpol.github.io/portal-lm-projektanci/

> Makieta poglądowa — nie jest działającym serwisem. Pobieranie plików innych niż karty PDF jest symulowane.
> Ceny i dostępność produktów: w systemie sklepu Leroy Merlin. Zdjęcia aranżacyjne są wizualizacjami poglądowymi.

## Struktura

| Folder | Zawartość |
|---|---|
| `a-biblioteka/` | makieta portalu (HTML/CSS/JS bez frameworków, router na hashach) |
| `karta/` | szablon karty produktu A4 — podgląd: `karta/index.html?ref=<nr ref. LM>` |
| `assets/data.js` | 371 indeksów i 23 serie (generowane z materiałów Schedpol) |
| `assets/lm.js` | gama, EAN i kod dostawcy z eksportu referencji LM (26.03.2026) |
| `assets/rysunki.js`, `assets/img/rys/` | rysunki techniczne do kart |
| `assets/karty/` | wygenerowane karty produktów PDF — **wersja robocza, do przebudowy** |
| `assets/fonts/` | Roboto i Roboto Condensed (licencja Apache 2.0) |
| `_narzedzia/` | skrypty Pythona do odświeżenia danych, zasobów i kart (wymagają materiałów źródłowych spoza repozytorium) |

## Uruchomienie lokalne

```
python -m http.server 8766
```
i otwórz http://localhost:8766/ (makieta działa też po otwarciu `a-biblioteka/index.html` z dysku).

Skrót klawiszowy `H` chowa pasek prezentera, strzałki ← → przełączają ekrany.

© SCHEDPOL Sp. z o.o. Materiały produktowe (zdjęcia, rysunki, opisy) są własnością Schedpol i nie podlegają licencji open source.
Znaki Sensea i Leroy Merlin należą do ich właścicieli.
