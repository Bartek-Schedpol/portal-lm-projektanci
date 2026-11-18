/* ==========================================================================
   Koncepcja A — „Biblioteka” · logika makiety (czysty JS, bez zależności)
   Ekrany: #/start · #/katalog · #/produkt?ref=… · #/pliki
   ========================================================================== */
(function () {
  'use strict';

  // Diagnostyka makiety: błąd JS zostawia ślad w atrybucie <html data-js-error>.
  window.addEventListener('error', function (e) {
    document.documentElement.setAttribute('data-js-error', (e.message || 'błąd') + ' @' + (e.lineno || '?'));
  });

  const SP = window.SP, SPI = window.SPI, SPProto = window.SPProto;
  const app = document.getElementById('app');
  if (!SP || !SPI || !SPProto) {
    app.innerHTML = '<p class="noscript">Nie udało się wczytać zasobów makiety (folder assets).</p>';
    return;
  }

  /* ---------- stałe ---------- */
  const DEFAULT_REF = '89189409';
  const CAD = { name: 'Schedpol & Schedline', date: '04.2026', mb: 55.2 };
  const VERIFIED = '11.2026';
  const HINTS = ['89189406', 'Balans 80×100', 'czarny kamień', 'odpływ 80'];
  const FT = [
    { k: 'packshot', l: 'Packshoty' }, { k: 'aranżacja', l: 'Aranżacje' }, { k: 'rysunek', l: 'Rysunki' },
    { k: 'infografika', l: 'Infografiki' }, { k: 'opis', l: 'Opisy' }, { k: 'instrukcja', l: 'Instrukcje' },
    { k: 'zdjęcie dodatkowe', l: 'Zdjęcia dodatkowe' }, { k: 'film', l: 'Film' }, { k: 'karta', l: 'Karty produktów' }
  ];
  /* karta produktu PDF jest dla każdego indeksu — dopisz do liczników serii (ok. 0,2 MB na kartę) */
  SP.series.forEach(function (s) {
    if (!s.files) s.files = {};
    if (!s.files.karta) { s.files.karta = s.n; s.mb = (s.mb || 0) + s.n * 0.2; }
  });
  const FT_MAIN = ['packshot', 'aranżacja', 'rysunek', 'infografika', 'opis'];
  const CAT_REP = {
    'brodzik': 'p-balans-ws', 'wanna': 'p-torres-w', 'odpływ liniowy': 'p-harmony', 'panel ścienny': 'p-wall6-sw',
    'nośnik': 'p-nosnik-wanna', 'obudowa': 'p-obudowa', 'akcesoria': 'p-maskownica-zlota'
  };
  const TITLE = {
    'Nośnik': 'Nośnik uniwersalny do wanien',
    'Obudowa uniwersalna': 'Obudowa uniwersalna do wanien',
    'Maskownica Balans/Integral': 'Maskownica do brodzików Balans / Integral',
    'Najazd': 'Najazd do brodzików',
    'Nogi Ipsilon': 'Nogi do brodzików Ipsilon'
  };

  /* ---------- pomocnicze ---------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function ic(n, size, sw) { return SPI.icon(n, { size: size || 18, sw: sw || 1.5 }); }
  function H(screen, params) { return esc(SPProto.href(screen, params || {})); }
  function nf(n, d) {
    const k = d == null ? 1 : d;
    return Number(n).toLocaleString('pl-PL', { minimumFractionDigits: k, maximumFractionDigits: k });
  }
  function plural(n, one, few, many) {
    n = Math.abs(n);
    if (n === 1) return one;
    const d = n % 10, h = n % 100;
    return (d >= 2 && d <= 4 && !(h >= 12 && h <= 14)) ? few : many;
  }
  function pliki(n) { return n + ' ' + plural(n, 'plik', 'pliki', 'plików'); }
  function indeksy(n) { return n + ' ' + plural(n, 'indeks', 'indeksy', 'indeksów'); }
  function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }
  function lcFirst(s) { return s ? s.charAt(0).toLowerCase() + s.slice(1) : s; }
  function norm(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l');
  }
  function mbLabel(mb) {
    if (!mb) return '0 MB';
    if (mb >= 1000) return nf(mb / 1000, 1) + ' GB';
    if (mb < 0.1) return Math.max(1, Math.round(mb * 1000)) + ' KB';
    return nf(mb, 1) + ' MB';
  }
  function hash(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function rnd(seed, min, max) { return min + (hash(seed) % 1000) / 1000 * (max - min); }
  function typeMb(s, k) {             // karta PDF ~0,2 MB; reszta — średnia z paczki serii
    if (k === 'karta') return (s.files.karta || 0) * 0.2;
    const other = sumFiles(s) - (s.files.karta || 0);
    return other ? ((s.mb || 0) - (s.files.karta || 0) * 0.2) * (s.files[k] || 0) / other : 0;
  }
  function sumFiles(s) { return Object.keys(s.files || {}).reduce(function (a, k) { return a + s.files[k]; }, 0); }

  /* ---------- model produktu ---------- */
  function serieOf(p) {
    return SP.serie(p.fam) || { fam: p.fam, type: SP.catLabel(p.cat), files: {}, scenes: [], feats: [], gw: '', lead: '', n: 0 };
  }
  function typeShort(p) { return serieOf(p).type.split(' · ')[0]; }
  function variant(p) {
    const d = SP.dims(p);
    if (d) return d.replace(/-/g, '–');
    return p.c || p.shape || lcFirst(typeShort(p));
  }
  function titleOf(p) {
    if (p.fam === 'Panele do brodzików') return 'Panel do brodzika ' + p.s.replace(/^Panel\s+/, '');
    if (TITLE[p.fam]) return TITLE[p.fam];
    return typeShort(p) + ' ' + p.brand + ' ' + p.s;
  }
  function kickerHTML(p) {
    const t = typeShort(p);
    if (p.fam === 'Panele do brodzików') return esc(p.s);
    if (norm(t).split(' ')[0] === norm(p.s).split(' ')[0]) return esc(p.s.length >= t.length ? p.s : t);
    return esc(p.s) + ' <span>· ' + esc(lcFirst(t)) + '</span>';
  }
  function metaLine(p) { return [p.c, p.shape].filter(Boolean).join(' · ') || p.brand; }
  function fileBase(p) {
    const clean = function (s) { return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l').replace(/Ł/g, 'L'); };
    const ser = clean(p.s).replace(/[^A-Za-z0-9]+/g, ' ').trim().split(' ').map(cap).join('');
    let dim = '';
    if (p.a != null && p.b != null) dim = p.a + 'x' + p.b + (p.cat === 'panel ścienny' && p.h ? 'x' + p.h : '');
    else if (p.a != null) dim = p.a + 'cm';
    else if (p.c) dim = clean(p.c).replace(/\s+/g, '-');
    return p.brand + '_' + ser + (dim ? '_' + dim : '');
  }
  /* karta produktu PDF: prawdziwe pliki z _narzedzia/7_karty_pdf.py (szablon ../karta/index.html) */
  function kartaPdf(p) { return '../assets/karty/Karta-produktu_LM' + p.ref + '.pdf'; }
  function kartaView(p) { return '../karta/index.html?ref=' + encodeURIComponent(p.ref); }
  /* karty gwarancyjne i instrukcje montażu przypisane do indeksu (assets/dokumenty.js) */
  const DOC_BASE = '../assets/dokumenty/';
  function docsFor(p) {
    return ((SP.docMap && SP.docMap[p.ref]) || []).map(function (k) { return SP.docs[k]; }).filter(Boolean);
  }
  function filesFor(p) {
    const s = serieOf(p), f = [], base = fileBase(p), has = s.files || {};
    f.push({ ext: 'PDF', name: 'Karta-produktu_LM' + p.ref + '.pdf', desc: 'Karta produktu PDF, A4 — parametry, nr ref., EAN, rysunek techniczny, gwarancja', mb: 0.2, href: kartaPdf(p), view: kartaView(p), karta: true });
    f.push({ ext: 'JPG', name: base + '_packshot.jpg', desc: 'Packshot JPG, 2500 px', mb: rnd(p.ref + 'a', 0.6, 1.6) });
    f.push({ ext: 'PNG', name: base + '_packshot.png', desc: 'Packshot PNG, przezroczyste tło', mb: rnd(p.ref + 'b', 2.2, 4.8) });
    if (has['aranżacja']) f.push({ ext: 'JPG', name: base + '_aranzacja.jpg', desc: 'Aranżacja JPG, 2500 px', mb: rnd(p.ref + 'c', 1.8, 3.9) });
    if (has['rysunek']) f.push({ ext: 'PDF', name: base + '_rysunek-techniczny.pdf', desc: 'Rysunek techniczny PDF', mb: rnd(p.ref + 'd', 0.2, 3.2) });
    if (p.cat !== 'akcesoria') f.push({ ext: 'DWG', name: base + '_rysunek.dwg', desc: 'Rysunek 2D DWG', mb: rnd(p.ref + 'e', 0.15, 0.6) });
    if (['brodzik', 'wanna', 'panel ścienny', 'odpływ liniowy'].indexOf(p.cat) !== -1) {
      f.push({ ext: '3D', name: 'Baza CAD Decor — ' + CAD.name, desc: 'Model 3D w bazie CAD Decor (aktualizacja ' + CAD.date + ')', mb: 0, cad: true });
    }
    if (has['infografika']) f.push({ ext: 'PNG', name: base + '_cechy.png', desc: 'Infografika: cechy serii', mb: rnd(p.ref + 'f', 0.5, 1.4) });
    if (has['opis']) f.push({ ext: 'PDF', name: base + '_opis.pdf', desc: 'Opis produktu', mb: rnd(p.ref + 'g', 0.05, 0.2) });
    docsFor(p).forEach(function (d) {              // prawdziwe pliki: assets/dokumenty (8_zasoby_kart.py)
      f.push({ ext: 'PDF', name: d.f, desc: d.t + ' · ' + d.str + ' ' + plural(d.str, 'strona', 'strony', 'stron'), mb: d.mb, href: DOC_BASE + d.f, doc: d.typ });
    });
    return f;
  }
  function extList(p) {
    const seen = {}, out = [];
    filesFor(p).forEach(function (f) { if (!seen[f.ext]) { seen[f.ext] = 1; out.push(f.ext); } });
    return ['JPG', 'PNG', 'PDF', 'DWG', '3D'].filter(function (e) { return out.indexOf(e) !== -1; });
  }
  function zestawFor(p) {
    const r = [];
    if (p.fam === 'Balans' || p.fam === 'Integral') r.push({ fam: 'Maskownica Balans/Integral', why: 'Maskownica odpływu' });
    if (['Grawello', 'Dante', 'Go Baby', 'Dafne'].indexOf(p.fam) !== -1) r.push({ fam: 'Panele do brodzików', why: 'Panel do brodzika', q: p.fam });
    if (p.fam === 'Ipsilon') r.push({ fam: 'Nogi Ipsilon', why: 'Zestaw nóg' });
    if (p.fam === 'Torres') {
      r.push({ fam: 'Nośnik', why: 'Podparcie wanny' });
      r.push({ fam: 'Obudowa uniwersalna', why: 'Zabudowa wanny' });
    }
    if (['Balans', 'Frigo', 'Integral'].indexOf(p.fam) !== -1) r.push({ fam: 'Wall Comfort', why: 'Strefa prysznica' });
    return r.filter(function (x) { return SP.serie(x.fam); });
  }

  /* ---------- komponenty ---------- */
  function dot(hx, cls) { return hx ? '<span class="dot' + (cls ? ' ' + cls : '') + '" style="--c:' + esc(hx) + '"></span>' : ''; }
  function pimg(key, alt) {
    const i = SP.img[key];
    if (!i) return '';
    return '<img' + (i.tb ? '' : ' class="is-mult"') + ' src="' + esc(SP.src(key)) + '" alt="' + esc(alt || '') + '" width="' + i.w +
      '" height="' + i.h + '" decoding="async">';
  }
  function refChip(p, big) {
    return '<button type="button" class="ref' + (big ? ' ref-lg' : '') + '" data-act="copy-ref" data-ref="' + esc(p.ref) +
      '" title="Kopiuj nr ref. LM" aria-label="Kopiuj nr ref. LM ' + esc(p.ref) + '"><span class="ref-k">LM</span><span class="ref-n">' +
      esc(p.ref) + '</span>' + ic('copy', big ? 16 : 13) + '</button>';
  }
  function refStatic(p) { return '<span class="ref"><span class="ref-k">LM</span><span class="ref-n">' + esc(p.ref) + '</span></span>'; }
  function extBadge(ext) { return '<span class="f-ext x-' + esc(String(ext).toLowerCase()) + '">' + esc(ext) + '</span>'; }
  function ftsHTML(p) {
    return '<span class="fts" aria-label="Typy plików">' + extList(p).map(function (e) {
      return '<span class="ft' + (e === '3D' ? ' ft-3d' : '') + '">' + e + '</span>';
    }).join('') + '</span>';
  }
  /* flaga marki na zdjęciu w katalogu: oryginalne logo Sensea (z etykiety) lub Schedpol (logotyp korporacyjny 2016) */
  const BRAND_LOGO = { 'Sensea': '../assets/znaki/sensea.png', 'Schedpol': '../assets/znaki/schedpol.svg' };
  function brandFlag(p) {
    const src = BRAND_LOGO[p.brand];
    return src ? '<span class="flag flag-' + esc(p.brand.toLowerCase()) + '"><img src="' + src + '" alt="' + esc(p.brand) + '"></span>' : '';
  }
  function cardHTML(p, i) {
    const href = H('produkt', { ref: p.ref }), inT = inTeczka('p:' + p.ref);
    return `<article class="card" style="--i:${Math.min(i, 14)}">
      <a class="card-media" href="${href}" tabindex="-1" aria-hidden="true">
        ${pimg(p.im, '')}
        ${p.new ? '<span class="tag">Nowość</span>' : ''}
        ${brandFlag(p)}
      </a>
      <button type="button" class="card-add${inT ? ' is-in' : ''}" data-act="add-product" data-ref="${esc(p.ref)}" aria-label="Dodaj pliki produktu ${esc(p.ref)} do teczki" title="Dodaj pliki do teczki">${ic(inT ? 'check' : 'plus', 16, 1.8)}</button>
      <div class="card-body">
        <p class="card-kicker">${kickerHTML(p)}</p>
        <h3 class="card-title"><a href="${href}">${esc(variant(p))}</a></h3>
        <p class="card-meta">${dot(p.hx)}${esc(metaLine(p))}</p>
        <div class="card-foot">${refChip(p)}${ftsHTML(p)}</div>
      </div>
    </article>`;
  }
  function rowHTML(p) {
    const href = H('produkt', { ref: p.ref });
    return `<tr data-href="${href}">
      <td>${refChip(p)}</td>
      <td><a class="t-prod" href="${href}"><span class="t-thumb">${pimg(p.im, '')}</span><span><b>${esc(p.s)}</b><small>${esc(typeShort(p))} · ${esc(p.brand)}</small></span></a></td>
      <td>${p.shape ? esc(p.shape) : '<span class="muted">—</span>'}</td>
      <td class="mono">${SP.dims(p) ? esc(variant(p)) : '<span class="muted">—</span>'}</td>
      <td>${p.c ? '<span class="t-col">' + dot(p.hx) + esc(p.c) + '</span>' : '<span class="muted">—</span>'}</td>
      <td class="mono">${p.g ? esc(p.g) : '<span class="muted">—</span>'}</td>
      <td>${ftsHTML(p)}</td>
      <td><div class="t-act">
        <a class="icon-btn" href="${esc(kartaPdf(p))}" download aria-label="Pobierz kartę produktu PDF ${esc(p.ref)}" title="Karta produktu PDF">${ic('file', 16)}</a>
        <button type="button" class="icon-btn" data-act="add-product" data-ref="${esc(p.ref)}" aria-label="Dodaj pliki produktu ${esc(p.ref)} do teczki" title="Dodaj pliki do teczki">${ic(inTeczka('p:' + p.ref) ? 'check' : 'plus', 16)}</button>
        <a class="icon-btn" href="${href}" aria-label="Otwórz kartę produktu ${esc(p.ref)}" title="Karta produktu">${ic('arrow-right', 16)}</a>
      </div></td>
    </tr>`;
  }

  /* ---------- tosty i schowek ---------- */
  function toast(msg, detail, icon) {
    const box = $('#toasts'), t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = ic(icon || 'check', 16, 1.8) + '<span>' + esc(msg) + (detail ? ' <span class="mono">' + esc(detail) + '</span>' : '') + '</span>';
    box.appendChild(t);
    while (box.children.length > 3) box.removeChild(box.firstChild);
    setTimeout(function () {
      t.classList.add('out');
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 420);
    }, 2800);
  }
  function legacyCopy(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
    } catch (e) { /* schowek niedostępny — makieta pokazuje samo potwierdzenie */ }
  }
  function copyRef(ref, btn) {
    let viaApi = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(ref).catch(function () { legacyCopy(ref); });
        viaApi = true;
      }
    } catch (e) { /* przejście do metody zapasowej */ }
    if (!viaApi) legacyCopy(ref);
    toast('Skopiowano nr ref.', ref, 'copy');
    if (btn && btn.classList.contains('ref')) {
      btn.classList.add('is-copied');
      setTimeout(function () { btn.classList.remove('is-copied'); }, 1400);
    }
  }

  /* ---------- teczka ---------- */
  const TZ_KEY = 'sp-a-teczka';
  let teczka = (function () {
    try {
      const v = JSON.parse(localStorage.getItem(TZ_KEY) || '[]');
      return Array.isArray(v) ? v.filter(function (x) { return x && x.id && x.title; }) : [];
    } catch (e) { return []; }
  })();
  function tzSave() { try { localStorage.setItem(TZ_KEY, JSON.stringify(teczka)); } catch (e) { /* brak dostępu do pamięci */ } }
  function inTeczka(id) { return teczka.some(function (x) { return x.id === id; }); }
  function tzTotals() { return teczka.reduce(function (a, x) { return { n: a.n + (x.n || 0), mb: a.mb + (x.mb || 0) }; }, { n: 0, mb: 0 }); }
  function tzAdd(item) {
    const i = teczka.findIndex(function (x) { return x.id === item.id; });
    if (i >= 0) { teczka[i] = item; toast('Zaktualizowano w teczce', item.title); }
    else { teczka.unshift(item); toast('Dodano do teczki', item.title + ' · ' + pliki(item.n)); }
    tzSave(); tzPaint(true);
  }
  function tzRemove(id) { teczka = teczka.filter(function (x) { return x.id !== id; }); tzSave(); tzPaint(); }
  function addProduct(ref, files) {
    const p = SP.byRef(ref);
    if (!p) return;
    const fs = files || filesFor(p);
    if (!fs.length) { toast('Zaznacz co najmniej jeden plik', '', 'info'); return; }
    tzAdd({
      id: 'p:' + ref, title: p.s + ' ' + variant(p), sub: 'LM ' + ref, n: fs.length,
      mb: fs.reduce(function (a, f) { return a + (f.mb || 0); }, 0), im: p.im
    });
  }
  function addSeries(fam) {
    const s = SP.serie(fam);
    if (!s) return;
    tzAdd({ id: 's:' + fam, title: 'Paczka serii ' + fam, sub: indeksy(s.n), n: sumFiles(s), mb: s.mb || 0, im: s.pack });
  }
  function addType(fam, type) {
    const s = SP.serie(fam), t = FT.filter(function (x) { return x.k === type; })[0];
    if (!s || !t || !s.files[type]) return;
    tzAdd({ id: 't:' + fam + ':' + type, title: fam + ' — ' + t.l.toLowerCase(), sub: 'paczka typu', n: s.files[type], mb: typeMb(s, type), im: s.pack });
  }
  function tzListHTML() {
    if (!teczka.length) {
      return '<div class="tz-empty"><div class="empty-ic">' + ic('folder', 24) + '</div><b>Teczka jest pusta</b>' +
        '<span>Dodaj pliki z katalogu, karty produktu albo paczkę całej serii.</span></div>';
    }
    return teczka.map(function (x) {
      return `<div class="tz-item">
        <span class="tz-ic">${x.im && SP.img[x.im] ? pimg(x.im, '') : ic(x.icon || 'zip', 20)}</span>
        <span class="tz-main"><span class="tz-t">${esc(x.title)}</span><span class="tz-s">${x.sub ? esc(x.sub) + ' · ' : ''}${pliki(x.n)} · ${mbLabel(x.mb)}</span></span>
        <button class="icon-btn" type="button" data-act="tz-remove" data-id="${esc(x.id)}" aria-label="Usuń z teczki: ${esc(x.title)}">${ic('x', 16)}</button>
      </div>`;
    }).join('');
  }
  function tzFootHTML() {
    const t = tzTotals(), dis = teczka.length ? '' : ' disabled';
    return `<div class="tz-total"><span>${pliki(t.n)} w ${teczka.length} ${plural(teczka.length, 'pozycji', 'pozycjach', 'pozycjach')}</span><b>${mbLabel(t.mb)}</b></div>
      <button class="btn btn-primary btn-block" type="button" data-act="tz-zip"${dis}>Pobierz ZIP <span class="btn-ic">${ic('download', 16)}</span></button>
      <div class="tz-row2">
        <button class="btn btn-block" type="button" data-act="tz-mail"${dis}>${ic('mail', 16)} Wyślij link e-mailem</button>
        <button class="btn" type="button" data-act="tz-clear"${dis}>Wyczyść</button>
      </div>`;
  }
  function tzPaint(bump) {
    const t = tzTotals(), c = $('#teczkaCount');
    c.textContent = t.n;
    c.classList.toggle('is-zero', !t.n);
    if (bump) { c.classList.remove('bump'); void c.offsetWidth; c.classList.add('bump'); }
    $('#teczkaSum').textContent = teczka.length ? pliki(t.n) + ' · ' + mbLabel(t.mb) : 'Brak plików';
    $('#teczkaBody').innerHTML = tzListHTML();
    $('#teczkaFoot').innerHTML = tzFootHTML();
    const inl = $('#tzInline');
    if (inl) {
      $('#tzInSum').textContent = teczka.length ? pliki(t.n) + ' · ' + mbLabel(t.mb) : 'Brak plików';
      $('#tzInList').innerHTML = tzListHTML();
      $('#tzInFoot').innerHTML = tzFootHTML();
      paintPlikiTable();
    }
    $$('[data-act="add-product"]').forEach(function (b) {
      const on = inTeczka('p:' + b.getAttribute('data-ref'));
      if (b.classList.contains('card-add')) { b.classList.toggle('is-in', on); b.innerHTML = ic(on ? 'check' : 'plus', 16, 1.8); }
      else if (b.classList.contains('icon-btn')) b.innerHTML = ic(on ? 'check' : 'plus', 16);
    });
  }

  /* ---------- wyszukiwarka z podpowiedziami ---------- */
  function sgProduct(p) {
    return `<a class="sg-item" href="${H('produkt', { ref: p.ref })}">
      <span class="sg-thumb">${pimg(p.im, '')}</span>
      <span class="sg-main"><span class="sg-t">${esc(p.s)}<span class="mono">${esc(variant(p))}</span></span>
      <span class="sg-s">${dot(p.hx)}${esc([p.c, p.shape, p.brand].filter(Boolean).join(' · '))}</span></span>
      ${refStatic(p)}
    </a>`;
  }
  function sgSerie(s) {
    return `<a class="sg-item" href="${H('katalog', { seria: s.fam })}">
      <span class="sg-thumb">${pimg(s.pack, '')}</span>
      <span class="sg-main"><span class="sg-t">Seria ${esc(s.fam)}</span><span class="sg-s">${indeksy(s.n)} · ${esc(s.type)}</span></span>
      ${ic('arrow-right', 16)}
    </a>`;
  }
  function suggHTML(q) {
    q = String(q || '').trim();
    if (!q) {
      return '<div class="sg-h">Często szukane</div>' + HINTS.map(function (h) {
        return `<a class="sg-item" href="${H('katalog', { q: h })}"><span class="sg-thumb">${ic('search', 18)}</span><span class="sg-main"><span class="sg-t mono">${esc(h)}</span></span>${ic('arrow-right', 16)}</a>`;
      }).join('') + '<div class="sg-h">Kategorie</div>' + SP.cats.slice(0, 4).map(function (c) {
        const n = SP.products.filter(function (p) { return p.cat === c.id; }).length;
        return `<a class="sg-item" href="${H('katalog', { cat: c.id })}"><span class="sg-thumb">${pimg(CAT_REP[c.id], '')}</span><span class="sg-main"><span class="sg-t">${esc(c.label)}</span><span class="sg-s">${indeksy(n)}</span></span>${ic('arrow-right', 16)}</a>`;
      }).join('');
    }
    const res = SP.search(q), nq = norm(q);
    const fams = SP.series.filter(function (s) { return norm(s.fam).indexOf(nq) !== -1; }).slice(0, 3);
    if (!res.length && !fams.length) {
      return '<div class="sg-empty"><b>Brak wyników dla „' + esc(q) + '”</b>Numer ref. LM ma 8 cyfr. Możesz też wpisać serię i wymiar, np. Balans 80×100.</div>';
    }
    let h = '';
    if (res.length) h += '<div class="sg-h">Produkty</div>' + res.slice(0, 6).map(sgProduct).join('');
    if (fams.length) h += '<div class="sg-h">Serie</div>' + fams.map(sgSerie).join('');
    h += '<div class="sg-foot"><span><kbd>Enter</kbd> pokaż wszystkie wyniki</span><span class="mono">' + res.length + ' ' + plural(res.length, 'wynik', 'wyniki', 'wyników') + '</span></div>';
    return h;
  }
  function mountSearch(input, list, opts) {
    opts = opts || {};
    let active = -1;
    const items = function () { return $$('.sg-item', list); };
    const paint = function () { list.innerHTML = suggHTML(input.value); active = -1; };
    const setActive = function (i) {
      const it = items();
      if (!it.length) return;
      active = i < 0 ? it.length - 1 : (i >= it.length ? 0 : i);
      it.forEach(function (el, k) { el.classList.toggle('is-active', k === active); });
      it[active].scrollIntoView({ block: 'nearest' });
    };
    const submit = function () {
      const q = input.value.trim(), res = q ? SP.search(q) : [];
      if (opts.onClose) opts.onClose();
      if (/^\d{8}$/.test(q) && res.length === 1) SPProto.go('produkt', { ref: res[0].ref });
      else SPProto.go('katalog', q ? { q: q } : {});
    };
    input.addEventListener('input', function () { paint(); if (opts.onOpen) opts.onOpen(); });
    input.addEventListener('focus', function () { paint(); if (opts.onOpen) opts.onOpen(); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
      else if (e.key === 'Enter') {
        e.preventDefault();
        const it = items();
        if (active >= 0 && it[active]) it[active].click(); else submit();
      } else if (e.key === 'Escape') { e.stopPropagation(); if (opts.onClose) opts.onClose(); input.blur(); }
    });
    return { paint: paint, submit: submit };
  }

  /* ==========================================================================
     Ekran: Start
     ========================================================================== */
  let packFam = 'Balans';
  let bigSearch = null;

  function packHTML(fam) {
    const s = SP.serie(fam) || SP.series[0];
    const n = sumFiles(s);
    const types = FT.filter(function (t) { return s.files[t.k]; }).sort(function (a, b) { return s.files[b.k] - s.files[a.k]; });
    const max = types.length ? s.files[types[0].k] : 1;
    return `<div class="pack-top">
        <span class="pack-thumb">${pimg(s.pack, '')}</span>
        <div><p class="pack-title">${esc(s.fam)}</p><p class="pack-meta">${pliki(n)} · ${mbLabel(s.mb)}</p></div>
      </div>
      <p class="pack-lead">${esc(s.type)} · ${indeksy(s.n)}</p>
      <div class="bars">${types.map(function (t) {
        return `<div class="bar"><em>${esc(t.l)}</em><i style="--w:${(s.files[t.k] / max).toFixed(3)}"></i><b>${s.files[t.k]}</b></div>`;
      }).join('')}</div>
      <div class="pack-foot">
        <button class="btn btn-primary btn-block" type="button" data-act="add-series" data-fam="${esc(s.fam)}">Dodaj serię do teczki <span class="btn-ic">${ic('plus', 16)}</span></button>
        <a class="link" href="${H('katalog', { seria: s.fam })}">Zobacz ${indeksy(s.n)} w katalogu ${ic('arrow-right', 14)}</a>
      </div>`;
  }

  function renderStart(params) {
    const total = SP.products.length;
    const nFiles = SP.series.reduce(function (a, s) { return a + sumFiles(s); }, 0);
    const mb = SP.series.reduce(function (a, s) { return a + (s.mb || 0); }, 0);
    const dp = SP.byRef(DEFAULT_REF) || SP.products[0];
    const dFiles = filesFor(dp);
    const pick = [];
    ['JPG', 'PNG', 'PDF', 'DWG', '3D'].forEach(function (x) {
      const f = dFiles.filter(function (y) { return y.ext === x; })[0];
      if (f) pick.push(f);
    });
    const dMb = dFiles.reduce(function (a, f) { return a + (f.mb || 0); }, 0);
    const news = SP.series.filter(function (s) { return s.new; });

    app.innerHTML = `
    <div class="wrap">
      <section class="hero" aria-labelledby="heroT">
        <div class="hero-copy">
          <span class="eyebrow rv">Strefa projektanta · Leroy Merlin</span>
          <h1 class="hero-title rv" id="heroT" style="--d:60ms">Znajdź produkt.<span>Pobierz pliki.</span></h1>
          <p class="hero-lead rv" style="--d:120ms">${total} indeksów z oferty Schedpol i Sensea dostępnej w Leroy Merlin — karty produktów PDF, packshoty, aranżacje, rysunki techniczne i modele 3D w jednym miejscu.</p>
          <div class="bigsearch rv" id="bigBox" style="--d:180ms" role="search">
            ${ic('search', 22)}
            <input id="bigSearch" type="search" placeholder="Nr ref. LM, seria, wymiar, kolor…" autocomplete="off" spellcheck="false" aria-label="Szukaj w bibliotece" aria-controls="bigList">
            <kbd>/</kbd>
            <button class="btn btn-primary" type="button" data-act="big-submit">Szukaj <span class="btn-ic">${ic('arrow-right', 16)}</span></button>
            <div class="sugg" id="bigList"></div>
          </div>
          <div class="hints rv" style="--d:240ms"><span>Spróbuj:</span>${HINTS.map(function (h) {
            return '<button class="hint" type="button" data-act="hint" data-q="' + esc(h) + '">' + esc(h) + '</button>';
          }).join('')}</div>
        </div>

        <aside class="bezel demo rv" style="--d:220ms" aria-label="Przykład: komplet plików do jednego indeksu">
          <div class="core">
            <div class="demo-cap"><span class="kicker">Komplet plików do indeksu</span><span class="st st-ok">${ic('check', 12, 2)} Zweryfikowano ${VERIFIED}</span></div>
            <div class="demo-head">
              <a class="demo-thumb" href="${H('produkt', { ref: dp.ref })}" aria-label="Karta produktu ${esc(dp.ref)}">${pimg(dp.im, '')}</a>
              <div>
                <p class="demo-title">${esc(dp.s)}</p>
                <p class="demo-sub"><span class="mono">${esc(variant(dp))}</span>${dp.c ? ' · ' + dot(dp.hx) + esc(dp.c) : ''}</p>
              </div>
              ${refChip(dp)}
            </div>
            <ul class="demo-files">${pick.map(function (f) {
              return '<li>' + extBadge(f.ext) + '<span class="f-name mono">' + esc(f.name) + '</span><span class="f-size mono">' + (f.mb ? mbLabel(f.mb) : 'w bazie') + '</span></li>';
            }).join('')}</ul>
            <div class="demo-foot">
              <span class="mono">${pliki(dFiles.length)} · ${mbLabel(dMb)}</span>
              <button class="btn btn-sm btn-dark" type="button" data-act="add-product" data-ref="${esc(dp.ref)}">${ic('plus', 15, 1.8)} Dodaj do teczki</button>
            </div>
          </div>
        </aside>
      </section>

      <section class="stats rv" aria-label="Biblioteka w liczbach">
        <div class="stat"><b>${total}</b><span>${plural(total, 'indeks', 'indeksy', 'indeksów')} w ofercie Leroy Merlin</span></div>
        <div class="stat"><b>${SP.series.length}</b><span>${plural(SP.series.length, 'rodzina', 'rodziny', 'rodzin')} produktów · Schedpol i Sensea</span></div>
        <div class="stat"><b>${nFiles.toLocaleString('pl-PL')}</b><span>${plural(nFiles, 'plik', 'pliki', 'plików')} w bibliotece</span></div>
        <div class="stat"><b>${nf(mb / 1000, 1)} GB</b><span>łączny rozmiar materiałów</span></div>
      </section>

      <section class="bento" aria-label="Skróty">
        <div class="panel b-cats rv">
          <div class="panel-h"><h2>Kategorie</h2><a class="link" href="${H('katalog')}">Cały katalog ${ic('arrow-right', 14)}</a></div>
          <div class="cats">${SP.cats.map(function (c, i) {
            const n = SP.products.filter(function (p) { return p.cat === c.id; }).length;
            const k = CAT_REP[c.id], im = SP.img[k];
            return `<a class="cat${i === 0 ? ' cat--lg' : ''}" href="${H('katalog', { cat: c.id })}">
              <span class="cat-go">${ic('arrow-up-right', 14)}</span>
              ${im ? '<img class="cat-img' + (im.tb ? '' : ' is-mult') + '" src="' + esc(SP.src(k)) + '" alt="" decoding="async">' : ''}
              <span class="cat-l">${esc(c.label)}</span><span class="cat-n">${indeksy(n)}</span>
            </a>`;
          }).join('')}</div>
        </div>

        <div class="bezel b-pack rv" style="--d:80ms">
          <div class="core">
            <div class="panel-h" style="margin-bottom:0"><h2>Paczka serii</h2><span class="kicker">ZIP</span></div>
            <label class="select pack-sel"><span class="sr">Wybierz serię</span>
              <select id="packSel" aria-label="Wybierz serię">${SP.series.map(function (s) {
                return '<option value="' + esc(s.fam) + '"' + (s.fam === packFam ? ' selected' : '') + '>' + esc(s.fam) + '</option>';
              }).join('')}</select>${ic('chevron-down', 16)}
            </label>
            <div id="packBox" style="display:flex;flex-direction:column;flex:1">${packHTML(packFam)}</div>
          </div>
        </div>

        <div class="panel b-cad rv" id="sek-cad" style="display:flex;flex-direction:column">
          <div class="cad-top">
            <span class="cad-ic">${ic('cube', 24)}</span>
            <div>
              <h2>Baza CAD Decor</h2>
              <div class="cad-chips"><span class="chip">${esc(CAD.name)}</span><span class="chip mono">aktualizacja ${CAD.date}</span><span class="chip mono">${mbLabel(CAD.mb)}</span></div>
            </div>
          </div>
          <ol class="steps">
            <li>Pobierz bazę „${esc(CAD.name)}” — stąd albo przez aktualizator baz w programie.</li>
            <li>Zainstaluj bazę w CAD Decor lub CAD Decor PRO.</li>
            <li>Wstaw model do projektu i potwierdź nr ref. LM na karcie produktu w portalu.</li>
          </ol>
          <div class="cad-foot" style="margin-top:auto">
            <button class="btn btn-dark" type="button" data-act="add-cad">${ic('download', 16)} Pobierz bazę</button>
            <button class="btn" type="button" data-act="demo" data-msg="Makieta: pobieranie pliku" data-detail="Instrukcja-aktualizacji-bazy.pdf">${ic('file', 16)} Instrukcja aktualizacji</button>
          </div>
        </div>

        <div class="panel b-new rv" style="--d:80ms">
          <div class="panel-h"><h2>Nowości 2026</h2></div>
          <div class="newlist">${news.map(function (s) {
            const nn = SP.products.filter(function (p) { return p.fam === s.fam && p.new; }).length;
            const label = s.fam === 'Balans' ? 'Balans — kaszmirowy kamień' : s.fam;
            const pk = s.fam === 'Balans' ? 'p-balans-cas' : s.pack;
            return `<a class="newrow" href="${H('katalog', s.fam === 'Balans' ? { seria: 'Balans', kolor: 'kaszmirowy kamień' } : { seria: s.fam })}">
              <span class="newrow-thumb">${pimg(pk, '')}</span>
              <span><b>${esc(label)}</b><small>${esc(s.type.split(' · ')[0])} · ${indeksy(nn)}</small></span>
              ${ic('arrow-right', 15)}
            </a>`;
          }).join('')}</div>
        </div>

        <div class="panel b-contact rv" id="sek-kontakt">
          <div class="contact">
            <div class="contact-intro">
              <span class="kicker">Kontakt</span>
              <h2 style="margin-top:8px">Brakuje pliku albo wymiaru? Zadzwoń lub napisz.</h2>
              <p>Biuro Obsługi Klienta Schedpol odpowiada na pytania o montaż, dobór produktu i materiały do projektu.</p>
              <span class="chip">${ic('clock', 14)} ${esc(SP.contacts.hours)}</span>
            </div>
            ${SP.contacts.bok.map(function (b, i) {
              return `<div class="bok${i === 0 ? ' is-mine' : ''}">
                ${i === 0 ? '<span class="tag">Twój region</span>' : ''}
                <h3>${esc(b.n)}</h3>
                <a class="mono" href="tel:+48${esc(b.tel.replace(/\s/g, ''))}">${ic('phone', 15)} ${esc(b.tel)}</a>
                <a href="mailto:${esc(b.mail)}">${ic('mail', 15)} ${esc(b.mail)}</a>
              </div>`;
            }).join('')}
          </div>
        </div>
      </section>
    </div>`;

    const box = $('#bigBox'), input = $('#bigSearch');
    bigSearch = mountSearch(input, $('#bigList'), {
      onOpen: function () { box.classList.add('is-open'); },
      onClose: function () { box.classList.remove('is-open'); }
    });
    box.addEventListener('focusout', function (e) {
      if (!box.contains(e.relatedTarget)) setTimeout(function () { if (!box.contains(document.activeElement)) box.classList.remove('is-open'); }, 140);
    });
    $('#packSel').addEventListener('change', function (e) { packFam = e.target.value; $('#packBox').innerHTML = packHTML(packFam); });
    if (params && params.sek) scrollToSek(params.sek);
  }
  function scrollToSek(sek) {
    requestAnimationFrame(function () {
      const el = document.getElementById('sek-' + sek);
      if (!el) return;
      el.classList.add('in');
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }

  /* ==========================================================================
     Ekran: Katalog
     ========================================================================== */
  const PARAM = { cat: 'cat', fam: 'seria', shape: 'ksztalt', color: 'kolor', brand: 'marka', gama: 'gama' };
  const C = { q: '', f: { cat: [], fam: [], shape: [], color: [], brand: [], gama: [] }, sort: 'seria', view: 'grid', limit: 24, open: {} };
  const COLORS = (function () {
    const m = {};
    SP.products.forEach(function (p) { if (p.c) { m[p.c] = m[p.c] || { v: p.c, l: p.c, hx: p.hx, n: 0 }; m[p.c].n++; } });
    return Object.keys(m).map(function (k) { return m[k]; }).sort(function (a, b) { return b.n - a.n; });
  })();
  const GAMY = ['A', 'B', 'C', 'L', 'X', 'brak'];   // wg eksportu referencji LM z 26.03.2026 (assets/lm.js)
  const FACETS = [
    { id: 'cat', label: 'Kategoria', get: function (p) { return p.cat; }, opts: SP.cats.map(function (c) { return { v: c.id, l: c.label }; }) },
    { id: 'fam', label: 'Seria', get: function (p) { return p.fam; }, opts: SP.series.map(function (s) { return { v: s.fam, l: s.fam }; }), collapse: 8 },
    { id: 'shape', label: 'Kształt', get: function (p) { return p.shape; }, opts: ['kwadratowy', 'prostokątny', 'półokrągły', 'pięciokątny'].map(function (v) { return { v: v, l: cap(v) }; }) },
    { id: 'color', label: 'Kolor', get: function (p) { return p.c; }, opts: COLORS, collapse: 7 },
    { id: 'brand', label: 'Marka', get: function (p) { return p.brand; }, opts: [{ v: 'Schedpol', l: 'Schedpol' }, { v: 'Sensea', l: 'Sensea' }] },
    { id: 'gama', label: 'Gama LM', get: function (p) { return p.g || 'brak'; }, opts: GAMY.map(function (g) { return { v: g, l: g === 'brak' ? 'nie podano' : g, mono: g !== 'brak' }; }),
      hint: 'Oznaczenia gam wg przeglądu oferty LM 2025.09.' }
  ];
  function facetById(id) { return FACETS.filter(function (F) { return F.id === id; })[0]; }
  function optLabel(F, v) { const o = F.opts.filter(function (x) { return x.v === v; })[0]; return o ? o.l : v; }

  function catFromParams(params) {
    C.q = params.q || '';
    Object.keys(PARAM).forEach(function (k) {
      C.f[k] = params[PARAM[k]] ? String(params[PARAM[k]]).split('|').filter(Boolean) : [];
    });
    C.sort = params.sort || 'seria';
    C.view = params.widok === 'tabela' ? 'table' : 'grid';
    C.limit = 24;
  }
  function catParams() {
    const o = {};
    if (C.q) o.q = C.q;
    Object.keys(PARAM).forEach(function (k) { if (C.f[k].length) o[PARAM[k]] = C.f[k].join('|'); });
    if (C.sort !== 'seria') o.sort = C.sort;
    if (C.view === 'table') o.widok = 'tabela';
    return o;
  }
  function syncUrl() { try { history.replaceState(null, '', SPProto.href('katalog', catParams())); } catch (e) { /* file:// bez historii */ } }
  function pass(p, skip) {
    for (let i = 0; i < FACETS.length; i++) {
      const F = FACETS[i];
      if (F.id === skip) continue;
      const sel = C.f[F.id];
      if (sel.length && sel.indexOf(F.get(p)) === -1) return false;
    }
    return true;
  }
  function area(p) {
    const a = typeof p.a === 'number' ? p.a : (parseFloat(p.a) || 0);
    const b = typeof p.b === 'number' ? p.b : 0;
    return a * (b || 1);
  }
  function sortList(list) {
    const idx = {};
    SP.series.forEach(function (s, i) { idx[s.fam] = i; });
    const l = list.slice();
    if (C.sort === 'wymiar') {
      l.sort(function (x, y) { return area(x) - area(y) || String(x.s).localeCompare(String(y.s), 'pl'); });
    } else if (C.sort === 'nowe') {
      l.sort(function (x, y) { return (y.new ? 1 : 0) - (x.new ? 1 : 0) || idx[x.fam] - idx[y.fam] || area(x) - area(y); });
    } else {
      l.sort(function (x, y) {
        return String(x.fam).localeCompare(String(y.fam), 'pl') || String(x.s).localeCompare(String(y.s), 'pl') ||
          String(x.c).localeCompare(String(y.c), 'pl') || area(x) - area(y);
      });
    }
    return l;
  }
  function facetsHTML(base) {
    let h = '<div class="facets-head"><span>Filtry</span><button class="icon-btn" type="button" data-act="close-all" aria-label="Zamknij filtry">' + ic('x', 18) + '</button></div>';
    FACETS.forEach(function (F) {
      const cnt = {};
      base.forEach(function (p) { if (pass(p, F.id)) { const v = F.get(p); cnt[v] = (cnt[v] || 0) + 1; } });
      const sel = C.f[F.id], open = !!C.open[F.id];
      let shown = 0, hidden = 0, body = '';
      F.opts.forEach(function (o, i) {
        const on = sel.indexOf(o.v) !== -1, n = cnt[o.v] || 0;
        if (F.collapse && !open && i >= F.collapse && !on) { hidden++; return; }
        shown++;
        body += '<label class="fopt' + (n === 0 && !on ? ' is-zero' : '') + '"><input type="checkbox" data-facet="' + F.id + '" value="' + esc(o.v) + '"' + (on ? ' checked' : '') + '>' +
          '<span class="fbox">' + ic('check', 12, 2.2) + '</span><span class="fl' + (o.mono ? ' mono' : '') + '">' + (o.hx ? dot(o.hx) : '') + esc(o.l) + '</span><span class="fc">' + n + '</span></label>';
      });
      h += '<div class="fg" role="group" aria-label="' + esc(F.label) + '"><div class="fg-h">' + esc(F.label) + (sel.length ? '<span>' + sel.length + '</span>' : '') + '</div>' + body;
      if (F.collapse && F.opts.length > F.collapse) {
        h += '<button class="fmore" type="button" data-act="facet-more" data-facet="' + F.id + '" aria-expanded="' + open + '">' +
          (open ? 'Pokaż mniej' : 'Pokaż wszystkie (' + F.opts.length + ')') + ic('chevron-down', 14) + '</button>';
      }
      if (F.hint) h += '<p class="fhint">' + esc(F.hint) + '</p>';
      h += '</div>';
    });
    return h;
  }
  function toolbarHTML(n) {
    let chips = '';
    if (C.q) chips += '<span class="chip"><span class="chip-k">Szukaj:</span> ' + esc(C.q) + '<button class="chip-x" type="button" data-act="rm-q" aria-label="Usuń wyszukiwaną frazę">' + ic('x', 12, 2) + '</button></span>';
    FACETS.forEach(function (F) {
      C.f[F.id].forEach(function (v) {
        chips += '<span class="chip"><span class="chip-k">' + esc(F.label) + ':</span> ' + esc(optLabel(F, v)) +
          '<button class="chip-x" type="button" data-act="rm-filter" data-facet="' + F.id + '" data-value="' + esc(v) + '" aria-label="Usuń filtr: ' + esc(optLabel(F, v)) + '">' + ic('x', 12, 2) + '</button></span>';
      });
    });
    if (chips) chips += '<button class="chip-clear" type="button" data-act="clear-filters">Wyczyść wszystko</button>';
    const all = n === SP.products.length && !chips;
    return `<div class="tb-count" aria-live="polite"><b>${n}</b> ${all ? plural(n, 'indeks', 'indeksy', 'indeksów') : plural(n, 'wynik', 'wyniki', 'wyników') + ' z ' + SP.products.length}</div>
      <div class="tb-chips">${chips}</div>
      <div class="tb-tools">
        <button class="btn btn-sm only-m" type="button" data-act="open-facets">${ic('filter', 16)} Filtry</button>
        <label class="select"><span class="sr">Sortowanie</span>
          <select id="sortSel" aria-label="Sortowanie">
            <option value="seria"${C.sort === 'seria' ? ' selected' : ''}>Seria A–Z</option>
            <option value="wymiar"${C.sort === 'wymiar' ? ' selected' : ''}>Wymiar rosnąco</option>
            <option value="nowe"${C.sort === 'nowe' ? ' selected' : ''}>Nowości</option>
          </select>${ic('chevron-down', 16)}
        </label>
        <div class="seg" role="group" aria-label="Widok wyników">
          <button type="button" data-act="view" data-view="grid" aria-pressed="${C.view === 'grid'}" aria-label="Widok kafli" title="Kafle">${ic('grid', 16)}</button>
          <button type="button" data-act="view" data-view="table" aria-pressed="${C.view === 'table'}" aria-label="Widok tabeli" title="Tabela">${ic('list', 16)}</button>
        </div>
      </div>`;
  }
  function resultsHTML(list) {
    if (!list.length) {
      return `<div class="empty"><div class="empty-ic">${ic('search', 24)}</div><h3>Brak produktów dla tych kryteriów</h3>
        <p>Usuń część filtrów albo zmień frazę. Numer ref. LM ma 8 cyfr — wpisz go w całości, np. 89189406.</p>
        <button class="btn btn-dark" type="button" data-act="clear-filters">Wyczyść filtry</button></div>`;
    }
    const part = list.slice(0, C.limit);
    let h;
    if (C.view === 'table') {
      h = '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Ref LM</th><th>Seria</th><th>Kształt</th><th>Wymiar</th><th>Kolor</th><th>Gama</th><th>Pliki</th><th><span class="sr">Akcje</span></th></tr></thead><tbody>' +
        part.map(rowHTML).join('') + '</tbody></table></div>';
    } else {
      h = '<div class="grid">' + part.map(cardHTML).join('') + '</div>';
    }
    h += '<div class="more">' + (list.length > part.length ? '<button class="btn" type="button" data-act="more">Pokaż kolejne ' + Math.min(24, list.length - part.length) + '</button>' : '') +
      '<span class="more-info">Wyświetlono ' + part.length + ' z ' + list.length + '</span></div>';
    return h;
  }
  function paintCatalog(focusKey) {
    const base = C.q ? SP.search(C.q) : SP.products;
    const list = sortList(base.filter(function (p) { return pass(p); }));
    const fa = $('#facets');
    if (!fa) return;
    const st = fa.scrollTop;
    fa.innerHTML = facetsHTML(base);
    fa.scrollTop = st;
    $('#tb').innerHTML = toolbarHTML(list.length);
    $('#res').innerHTML = resultsHTML(list);
    if (focusKey) {
      const el = $$('input[data-facet]', fa).filter(function (i) { return i.getAttribute('data-facet') + '|' + i.value === focusKey; })[0];
      if (el) el.focus({ preventScroll: true });
    }
  }
  function renderKatalog(params) {
    catFromParams(params || {});
    app.innerHTML = `
    <div class="wrap">
      <header class="page-head">
        <div>
          <span class="eyebrow">Katalog · oferta w Leroy Merlin</span>
          <h1 class="page-title" style="margin-top:18px">Katalog produktów</h1>
          <p class="page-sub">${SP.products.length} indeksów w ${SP.series.length} rodzinach. Każda pozycja ma numer ref. LM, wymiary i komplet plików do projektu.</p>
        </div>
        <label class="cat-search">${ic('search', 18)}<span class="sr">Filtruj katalog</span>
          <input id="catQ" type="search" placeholder="Filtruj: nr ref., seria, wymiar, kolor…" value="${esc(C.q)}" autocomplete="off" spellcheck="false"><kbd>/</kbd>
        </label>
      </header>
      <div class="cat-layout">
        <aside class="facets" id="facets" aria-label="Filtry katalogu"></aside>
        <section aria-label="Wyniki">
          <div class="tb" id="tb"></div>
          <div id="res"></div>
        </section>
      </div>
    </div>`;
    paintCatalog();

    let timer = null;
    $('#catQ').addEventListener('input', function (e) {
      clearTimeout(timer);
      const v = e.target.value;
      timer = setTimeout(function () { C.q = v.trim(); C.limit = 24; paintCatalog(); syncUrl(); }, 140);
    });
    $('#facets').addEventListener('change', function (e) {
      const inp = e.target.closest('input[data-facet]');
      if (!inp) return;
      const id = inp.getAttribute('data-facet'), arr = C.f[id], i = arr.indexOf(inp.value);
      if (inp.checked && i === -1) arr.push(inp.value);
      if (!inp.checked && i !== -1) arr.splice(i, 1);
      C.limit = 24;
      paintCatalog(id + '|' + inp.value);
      syncUrl();
    });
    $('#tb').addEventListener('change', function (e) {
      if (e.target.id === 'sortSel') { C.sort = e.target.value; paintCatalog(); syncUrl(); }
    });
  }

  /* ==========================================================================
     Ekran: Karta produktu
     ========================================================================== */
  let PD = { p: null, files: [], gal: [] };

  const EXTRA_SCENES = { 'Balans': ['balans-bs-b', 'balans-zoom-bs'] };
  const SCENE_COL = { 'balans-cut': 'w', 'balans-zoom-ws': 'w', 'balans-zoom-bs': 'b', 'najazd-a': '', 'najazd-b': '' };
  function sceneCol(key) {
    if (Object.prototype.hasOwnProperty.call(SCENE_COL, key)) return SCENE_COL[key];
    if (/-ws|-sw/.test(key)) return 'w';
    if (/-bs|black/.test(key)) return 'b';
    if (/-cas/.test(key)) return 'c';
    if (/-gs/.test(key)) return 'g';
    if (/-w$/.test(key)) return 'w';
    if (/-b$/.test(key)) return 'b';
    return '';
  }
  function prodCol(p) {
    const c = p.c || '';
    if (/czarn/.test(c)) return 'b';
    if (/kaszmir/.test(c)) return 'c';
    if (/szar|cement/.test(c)) return 'g';
    if (/bia/.test(c)) return 'w';
    return 'x';
  }
  function galleryFor(p) {
    const s = serieOf(p), pc = prodCol(p), docs = [];
    const ex = (SP.extra && SP.extra[p.ref]) || [];          // zdjęcia dodatkowe z paczki e-commerce (packshoty.js)
    const rys = SP.rys && SP.rys[p.ref];                     // rysunek techniczny tego indeksu (rysunki.js)
    if (rys) {
      const rk = 'rys:' + rys.f;
      SP.img[rk] = SP.img[rk] || { f: 'rys/' + rys.f, w: rys.w, h: rys.h, tb: false };
      docs.push({ k: rk, kind: 'doc', cap: 'Rysunek techniczny · wymiary w mm' });
    } else if (p.fam === 'Balans') {
      docs.push({ k: p.shape === 'prostokątny' ? 'draw-balans-rect' : 'draw-balans-sq', kind: 'doc', cap: 'Rysunek techniczny · wymiary w mm' });
    }
    if (p.fam === 'Balans') docs.push({ k: 'info-balans', kind: 'doc', cap: 'Infografika · cechy serii' });
    /* info-frigo / info-ipsilon celowo pominięte: grafiki zawierają „Ponad 45 lat doświadczenia” i goły badge gwarancji — do korekty przed publikacją */
    const exPack = ex.filter(function (x) { return x.kind === 'pack'; }).map(function (x) { return { k: x.k, kind: 'pack', cap: x.cap }; });
    const exPhoto = ex.filter(function (x) { return x.kind !== 'pack'; }).map(function (x) { return { k: x.k, kind: 'scene', cap: x.cap }; });
    const dup = ex.length ? { 'balans-zoom-ws': 1, 'balans-zoom-bs': 1, 'balans-cut': 1 } : {};
    const all = (s.scenes || []).concat(EXTRA_SCENES[p.fam] || []).filter(function (k) { return SP.img[k] && !dup[k]; });
    let own = all.filter(function (k) { const sc = sceneCol(k); return sc === '' || sc === pc; });
    own.sort(function (a, b) { return (sceneCol(b) === pc ? 1 : 0) - (sceneCol(a) === pc ? 1 : 0); });
    let cap = 'Wizualizacja poglądowa';
    if (!own.length && all.length) { own = all; cap = 'Wizualizacja poglądowa · inny wariant kolorystyczny'; }
    const scenes = own.slice(0, Math.max(2, 9 - docs.length - ex.length)).map(function (k) { return { k: k, kind: 'scene', cap: cap }; });
    return [{ k: p.im, kind: 'pack', cap: '' }].concat(exPack, scenes, exPhoto, docs).filter(function (x) { return SP.img[x.k]; });
  }
  function stageInner(item, alt) {
    const i = SP.img[item.k];
    return '<img' + (item.kind === 'pack' && !i.tb ? ' class="is-mult"' : '') + ' src="' + esc(SP.src(item.k)) + '" alt="' + esc(alt) + '" width="' + i.w + '" height="' + i.h + '">' +
      (item.cap ? '<span class="gal-cap">' + esc(item.cap) + '</span>' : '');
  }
  function galAlt(item, p) {
    return item.kind === 'pack' ? titleOf(p) + ', ' + variant(p) : (item.kind === 'scene' ? 'Aranżacja z produktem ' + p.s + ' — wizualizacja poglądowa' : item.cap);
  }
  function setStage(idx) {
    const item = PD.gal[idx], st = $('#galStage');
    if (!item || !st) return;
    st.className = 'core gal-stage is-' + item.kind;
    st.innerHTML = stageInner(item, galAlt(item, PD.p));
    $$('.gal-thumb').forEach(function (b, i) { b.classList.toggle('is-on', i === idx); b.setAttribute('aria-pressed', i === idx); });
  }
  function filesSummary() {
    const on = $$('.files-tbl input[data-file]').filter(function (i) { return i.checked; });
    const mb = on.reduce(function (a, i) { return a + (PD.files[+i.getAttribute('data-file')].mb || 0); }, 0);
    const sum = $('#fSum'), all = $('#fAll');
    if (sum) sum.textContent = pliki(on.length) + ' · ' + mbLabel(mb);
    if (all) { all.checked = on.length === PD.files.length; all.indeterminate = on.length > 0 && on.length < PD.files.length; }
    $$('.files-tbl tbody tr').forEach(function (tr) { const inp = $('input[data-file]', tr); tr.classList.toggle('is-off', !inp.checked); });
  }

  function renderProdukt(params) {
    const p = SP.byRef((params && params.ref) || DEFAULT_REF) || SP.byRef(DEFAULT_REF) || SP.products[0];
    const s = serieOf(p), files = filesFor(p), gal = galleryFor(p);
    PD = { p: p, files: files, gal: gal };
    const stone = p.cat === 'brodzik' && /kamień/.test(p.c || '');
    const tech = p.tn ? p.tn + (p.tn === 'Stabilsafe' ? '®' : '') + (p.tech ? ' · ' + p.tech : '') : (p.tech || '');
    const attrs = [
      ['Marka', esc(p.brand)],
      ['Seria', '<a class="link" style="font-size:inherit;color:inherit" href="' + H('katalog', { seria: p.fam }) + '">' + esc(p.s) + ' ' + ic('arrow-right', 13) + '</a>'],
      p.shape ? ['Kształt', esc(cap(p.shape))] : null,
      SP.dims(p) ? ['Wymiar', '<span class="mono">' + esc(variant(p)) + '</span>'] : null,
      p.c ? ['Kolor', dot(p.hx, 'lg') + esc(cap(p.c)) + (p.ce || p.ral ? ' <small>' + esc([p.ce, p.ral].filter(Boolean).join(' · ')) + '</small>' : '')] : null,
      tech ? ['Technologia', esc(tech)] : null,
      ['Gama LM', p.g ? '<span class="mono">' + esc(p.g) + '</span>' : '<small>brak w eksporcie LM</small>'],
      p.ean ? ['EAN', '<span class="mono">' + esc(p.ean) + '</span>'] : null,
      stone ? ['Antypoślizgowość', 'klasa A — DIN EN 16165:2023 (załącznik A)'] : null
    ].filter(Boolean);
    const sibs = SP.products.filter(function (x) { return x.fam === p.fam && x.s === p.s && x.c === p.c && x.ref !== p.ref; })
      .sort(function (a, b) { return area(a) - area(b); });
    const zest = zestawFor(p);
    const pdBits = [];
    if (SP.dims(p)) pdBits.push('<span class="mono">' + esc(variant(p)) + '</span>');
    if (p.c) pdBits.push('<span>' + dot(p.hx, 'lg') + esc(p.c) + '</span>');
    if (!pdBits.length && p.shape) pdBits.push('<span>' + esc(p.shape) + '</span>');
    const pdVar = pdBits.join('<i class="sep" aria-hidden="true"></i>');
    const mbAll = files.reduce(function (a, f) { return a + (f.mb || 0); }, 0);

    app.innerHTML = `
    <div class="wrap pd">
      <nav class="crumbs" aria-label="Okruszki">
        <a href="${H('katalog')}">Katalog</a>${ic('chevron-right', 14)}
        <a href="${H('katalog', { cat: p.cat })}">${esc(SP.catLabel(p.cat))}</a>${ic('chevron-right', 14)}
        <a href="${H('katalog', { seria: p.fam })}">${esc(p.fam)}</a>${ic('chevron-right', 14)}
        <span class="mono" aria-current="page">LM ${esc(p.ref)}</span>
      </nav>

      <div class="pd-top">
        <section class="gal" aria-label="Galeria produktu">
          <div class="bezel"><div class="core gal-stage is-pack" id="galStage">${stageInner(gal[0], galAlt(gal[0], p))}</div></div>
          ${gal.length > 1 ? '<div class="gal-thumbs">' + gal.map(function (g, i) {
            return '<button type="button" class="gal-thumb is-' + g.kind + (i === 0 ? ' is-on' : '') + '" data-act="gal" data-idx="' + i + '" aria-pressed="' + (i === 0) + '" aria-label="' +
              esc(g.kind === 'pack' ? 'Packshot' : g.cap) + ' ' + (i + 1) + ' z ' + gal.length + '"><img' + (g.kind === 'pack' && !SP.img[g.k].tb ? ' class="is-mult"' : '') + ' src="' + esc(SP.src(g.k)) + '" alt=""></button>';
          }).join('') + '</div>' : ''}
        </section>

        <section class="pd-info" aria-labelledby="pdT">
          <p class="kicker">${esc(SP.catLabel(p.cat))} · ${esc(p.brand)}${p.new ? ' · <span style="color:var(--brand)">Nowość 2026</span>' : ''}</p>
          <h1 class="pd-title" id="pdT">${esc(titleOf(p))}</h1>
          ${pdVar ? '<p class="pd-var">' + pdVar + '</p>' : ''}
          <div class="pd-ref">${refChip(p, true)}<span>Numer referencyjny Leroy Merlin</span></div>
          <dl class="attrs">${attrs.map(function (a) { return '<div><dt>' + a[0] + '</dt><dd>' + a[1] + '</dd></div>'; }).join('')}</dl>
          <div class="pd-cta">
            <button class="btn btn-primary" type="button" data-act="add-product-sel">Dodaj pliki do teczki <span class="btn-ic">${ic('arrow-right', 16)}</span></button>
            <a class="btn" href="${esc(kartaPdf(p))}" download>${ic('file', 16)} Karta produktu PDF</a>
          </div>
          <p class="pd-karta"><a class="link" href="${esc(kartaView(p))}" target="_blank" rel="noopener">${ic('eye', 15)} Podgląd karty A4 przed pobraniem</a></p>
          <p class="pd-note">${ic('info', 16)} Cena i dostępność: w systemie sklepu Leroy Merlin.</p>
        </section>
      </div>

      <section class="pd-sec" aria-labelledby="fT">
        <div class="sec-h">
          <div><h2 id="fT">Pliki do tego indeksu</h2><p>Zaznacz, czego potrzebujesz do projektu. Nazwy plików mają jeden schemat: marka, seria, wymiar, typ.</p></div>
          <div class="files-tools">
            <label class="check" style="position:relative"><input type="checkbox" id="fAll" checked><span class="fbox">${ic('check', 12, 2.2)}</span>Zaznacz wszystkie</label>
            <span class="mono" id="fSum">${pliki(files.length)} · ${mbLabel(mbAll)}</span>
            <button class="btn btn-sm btn-dark" type="button" data-act="add-product-sel">${ic('plus', 15, 1.8)} Dodaj zaznaczone</button>
          </div>
        </div>
        <div class="tbl-wrap"><table class="tbl files-tbl">
          <thead><tr><th><span class="sr">Zaznacz</span></th><th>Plik</th><th style="text-align:right">Rozmiar</th><th>Status</th><th><span class="sr">Pobierz</span></th></tr></thead>
          <tbody>${files.map(function (f, i) {
            return `<tr>
              <td><label class="f-check"><input type="checkbox" data-file="${i}" checked aria-label="Zaznacz plik: ${esc(f.desc)}"><span class="fbox">${ic('check', 12, 2.2)}</span></label></td>
              <td><div class="f-file">${extBadge(f.ext)}<div><b>${esc(f.name)}</b><small>${esc(f.desc)}</small></div></div></td>
              <td class="num">${f.mb ? mbLabel(f.mb) : '<span class="muted">—</span>'}</td>
              <td>${f.cad ? '<span class="st st-cad">' + ic('cube', 12, 1.8) + ' Baza ' + CAD.date + '</span>' : '<span class="st st-ok">' + ic('check', 12, 2) + ' Zweryfikowano ' + VERIFIED + '</span>'}</td>
              <td><div class="t-act">${f.href
                ? '<a class="icon-btn" href="' + esc(f.view) + '" target="_blank" rel="noopener" aria-label="Podgląd: ' + esc(f.name) + '" title="Podgląd karty">' + ic('eye', 16) + '</a><a class="icon-btn" href="' + esc(f.href) + '" download aria-label="Pobierz: ' + esc(f.name) + '" title="Pobierz PDF">' + ic('download', 16) + '</a>'
                : '<button class="icon-btn" type="button" data-act="demo" data-msg="Makieta: pobieranie pliku" data-detail="' + esc(f.name) + '" aria-label="Pobierz: ' + esc(f.name) + '">' + ic('download', 16) + '</button>'}</div></td>
            </tr>`;
          }).join('')}</tbody>
        </table></div>
      </section>

      <div class="pd-two">
        <section class="panel" aria-labelledby="cT">
          <div class="panel-h"><h2 id="cT">Cechy serii ${esc(p.fam)}</h2><span class="kicker">${esc(s.type.split(' · ')[0])}</span></div>
          ${s.feats && s.feats.length ? '<ol class="feats">' + s.feats.map(function (f, i) { return '<li><span>0' + (i + 1) + '</span>' + esc(f) + '</li>'; }).join('') + '</ol>' : '<p class="feats-lead">' + esc(s.lead) + '</p>'}
        </section>
        <section class="panel gw" aria-labelledby="gT">
          <h2 class="gw-h" id="gT">${ic('shield', 20)} Gwarancja</h2>
          <p>${esc(s.gw)}</p>
          ${docsFor(p).map(function (d) {
            return '<a class="link" href="' + esc(DOC_BASE + d.f) + '" target="_blank" rel="noopener">' + ic('file', 15) + ' ' + esc(d.t) + ' <small>(PDF, ' + esc(nf(d.mb, 1)) + ' MB)</small></a>';
          }).join('')}
        </section>
      </div>

      ${sibs.length ? `<section class="pd-sec" aria-labelledby="sT">
        <div class="sec-h"><div><h2 id="sT">Inne rozmiary w tej serii i kolorze</h2><p>${esc(p.s)}${p.c ? ' · ' + esc(p.c) : ''} — ${indeksy(sibs.length)}</p></div></div>
        <div class="tbl-wrap"><table class="tbl">
          <thead><tr><th>Wymiar</th><th>Kształt</th><th>Nr ref. LM</th><th>Gama LM</th><th><span class="sr">Otwórz</span></th></tr></thead>
          <tbody>${sibs.map(function (x) {
            const href = H('produkt', { ref: x.ref });
            return `<tr data-href="${href}">
              <td class="mono"><a href="${href}">${esc(variant(x))}</a></td>
              <td>${x.shape ? esc(x.shape) : '<span class="muted">—</span>'}</td>
              <td>${refChip(x)}</td>
              <td class="mono">${x.g ? esc(x.g) : '<span class="muted">—</span>'}</td>
              <td><div class="t-act"><a class="icon-btn" href="${href}" aria-label="Otwórz kartę produktu ${esc(x.ref)}">${ic('arrow-right', 16)}</a></div></td>
            </tr>`;
          }).join('')}</tbody>
        </table></div>
      </section>` : ''}

      ${zest.length ? `<section class="pd-sec" aria-labelledby="zT">
        <div class="sec-h"><div><h2 id="zT">Elementy zestawu</h2><p>Produkty z oferty w Leroy Merlin, które uzupełniają tę serię w projekcie.</p></div></div>
        <div class="zestaw">${zest.map(function (z) {
          const zs = SP.serie(z.fam);
          const zp = z.q ? SP.products.filter(function (x) { return x.fam === z.fam && norm(x.s).indexOf(norm(z.q)) !== -1; })[0] : null;
          return `<a class="zcard" href="${H('katalog', z.q ? { seria: z.fam, q: z.q } : { seria: z.fam })}">
            <span class="zcard-thumb">${pimg(zp ? zp.im : zs.pack, '')}</span>
            <span class="zcard-main"><span class="kicker">${esc(z.why)}</span><b>${esc(zp ? zp.s : zs.fam)}</b><p>${esc(zs.lead)}</p><span class="mono">${indeksy(zs.n)}</span></span>
          </a>`;
        }).join('')}</div>
      </section>` : ''}
    </div>`;

    const tbl = $('.files-tbl');
    tbl.addEventListener('change', function (e) { if (e.target.matches('input[data-file]')) filesSummary(); });
    $('#fAll').addEventListener('change', function (e) {
      $$('.files-tbl input[data-file]').forEach(function (i) { i.checked = e.target.checked; });
      filesSummary();
    });
  }

  /* ==========================================================================
     Ekran: Centrum plików
     ========================================================================== */
  const P = { tab: 'all' };
  const TABS = [{ k: 'all', l: 'Wszystkie' }].concat(FT.filter(function (t) { return FT_MAIN.indexOf(t.k) !== -1 || t.k === 'instrukcja' || t.k === 'karta'; }));

  function plikiTableHTML() {
    const tab = P.tab, all = tab === 'all';
    const rows = SP.series.filter(function (s) { return all || s.files[tab]; });
    const seriaCell = function (s) {
      return '<a class="t-prod" href="' + H('katalog', { seria: s.fam }) + '"><span class="t-thumb">' + pimg(s.pack, '') + '</span><span><b>' + esc(s.fam) + '</b><small>' + esc(s.type.split(' · ')[0]) + ' · ' + indeksy(s.n) + '</small></span></a>';
    };
    const num = function (v) { return '<td class="num">' + (v ? '<b>' + v + '</b>' : '<span class="zero">—</span>') + '</td>'; };
    if (all) {
      const tot = { other: 0, sum: 0, mb: 0 };
      FT_MAIN.forEach(function (k) { tot[k] = 0; });
      const body = rows.map(function (s) {
        const sum = sumFiles(s);
        const other = sum - FT_MAIN.reduce(function (a, k) { return a + (s.files[k] || 0); }, 0);
        FT_MAIN.forEach(function (k) { tot[k] += s.files[k] || 0; });
        tot.other += other; tot.sum += sum; tot.mb += s.mb || 0;
        const inT = inTeczka('s:' + s.fam);
        return '<tr><td>' + seriaCell(s) + '</td>' + FT_MAIN.map(function (k) { return num(s.files[k]); }).join('') + num(other) +
          '<td class="num"><b>' + sum + '</b></td><td class="num">' + mbLabel(s.mb) + '</td><td><div class="t-act">' +
          (inT ? '<span class="icon-btn is-done" title="W teczce" aria-label="Paczka serii ' + esc(s.fam) + ' jest w teczce">' + ic('check', 16, 2) + '</span>' : '<button class="icon-btn is-add" type="button" data-act="add-series" data-fam="' + esc(s.fam) + '" title="Dodaj paczkę serii do teczki" aria-label="Dodaj paczkę serii ' + esc(s.fam) + ' do teczki">' + ic('plus', 16, 1.8) + '</button>') +
          '</div></td></tr>';
      }).join('');
      return '<div class="tbl-wrap"><table class="tbl fl-tbl"><thead><tr><th>Seria</th>' +
        FT_MAIN.map(function (k) { return '<th style="text-align:right">' + esc(FT.filter(function (t) { return t.k === k; })[0].l) + '</th>'; }).join('') +
        '<th style="text-align:right">Pozostałe</th><th style="text-align:right">Razem</th><th style="text-align:right">Rozmiar</th><th><span class="sr">Akcja</span></th></tr></thead><tbody>' + body +
        '<tr><td><b>Razem · ' + rows.length + ' ' + plural(rows.length, 'rodzina', 'rodziny', 'rodzin') + '</b></td>' + FT_MAIN.map(function (k) { return num(tot[k]); }).join('') + num(tot.other) +
        '<td class="num"><b>' + tot.sum.toLocaleString('pl-PL') + '</b></td><td class="num"><b>' + mbLabel(tot.mb) + '</b></td><td></td></tr></tbody></table></div>';
    }
    const T = FT.filter(function (t) { return t.k === tab; })[0];
    let tn = 0, tmb = 0;
    const body = rows.map(function (s) {
      const n = s.files[tab], mb = typeMb(s, tab), inT = inTeczka('t:' + s.fam + ':' + tab);
      tn += n; tmb += mb;
      return '<tr><td>' + seriaCell(s) + '</td>' + num(n) + '<td class="num">ok. ' + mbLabel(mb) + '</td><td><span class="st st-ok">' + ic('check', 12, 2) + ' Zweryfikowano ' + VERIFIED + '</span></td><td><div class="t-act">' +
        (inT ? '<span class="st st-ok">' + ic('check', 12, 2) + ' W teczce</span>' : '<button class="btn btn-sm" type="button" data-act="add-type" data-fam="' + esc(s.fam) + '" data-type="' + esc(tab) + '">' + ic('plus', 14, 1.8) + ' Do teczki</button>') +
        '</div></td></tr>';
    }).join('');
    return '<div class="tbl-wrap"><table class="tbl fl-tbl"><thead><tr><th>Seria</th><th style="text-align:right">' + esc(T.l) + '</th><th style="text-align:right">Rozmiar</th><th>Status</th><th><span class="sr">Akcja</span></th></tr></thead><tbody>' +
      body + '<tr><td><b>Razem · ' + rows.length + ' ' + plural(rows.length, 'rodzina', 'rodziny', 'rodzin') + '</b></td>' + num(tn) + '<td class="num"><b>ok. ' + mbLabel(tmb) + '</b></td><td></td><td></td></tr></tbody></table></div>';
  }
  function tabsHTML() {
    return TABS.map(function (t) {
      const n = t.k === 'all' ? SP.series.reduce(function (a, s) { return a + sumFiles(s); }, 0) : SP.series.reduce(function (a, s) { return a + (s.files[t.k] || 0); }, 0);
      return '<button class="tab' + (P.tab === t.k ? ' is-on' : '') + '" type="button" role="tab" aria-selected="' + (P.tab === t.k) + '" data-act="ftab" data-tab="' + esc(t.k) + '">' + esc(t.l) + '<small>' + n.toLocaleString('pl-PL') + '</small></button>';
    }).join('');
  }
  function paintPlikiTable() {
    const box = $('#flTable'), tabs = $('#flTabs');
    if (!box || !tabs) return;
    tabs.innerHTML = tabsHTML();
    box.innerHTML = plikiTableHTML();
  }
  function renderPliki(params) {
    P.tab = TABS.some(function (t) { return t.k === (params && params.typ); }) ? params.typ : 'all';
    const nFiles = SP.series.reduce(function (a, s) { return a + sumFiles(s); }, 0);
    const mb = SP.series.reduce(function (a, s) { return a + (s.mb || 0); }, 0);
    app.innerHTML = `
    <div class="wrap">
      <header class="page-head">
        <div>
          <span class="eyebrow">Centrum plików</span>
          <h1 class="page-title" style="margin-top:18px">Paczki plików dla całych serii</h1>
          <p class="page-sub">${nFiles.toLocaleString('pl-PL')} ${plural(nFiles, 'plik', 'pliki', 'plików')} · ${mbLabel(mb)} · ${SP.series.length} ${plural(SP.series.length, 'rodzina', 'rodziny', 'rodzin')} produktów. Publikujemy wyłącznie pliki po weryfikacji treści.</p>
        </div>
        <button class="btn" type="button" data-act="add-cad">${ic('cube', 16)} Baza CAD Decor · ${CAD.date}</button>
      </header>
      <div class="fl-layout">
        <section aria-label="Paczki serii">
          <div class="tabs" id="flTabs" role="tablist" aria-label="Typ plików"></div>
          <div id="flTable"></div>
          <div class="notes">
            <div class="note"><h3>${ic('shield', 18)} Statusy plików</h3><p>Publikujemy wyłącznie pliki po weryfikacji treści. Każdy plik ma status i datę weryfikacji.</p>
              <div class="sts"><span class="st st-ok">${ic('check', 12, 2)} Zweryfikowano ${VERIFIED}</span><span class="st st-cad">${ic('cube', 12, 1.8)} Baza ${CAD.date}</span></div></div>
            <div class="note"><h3>${ic('layers', 18)} Wersje</h3><p>Po aktualizacji pliku poprzednia wersja znika z biblioteki. Paczki ZIP i linki z teczki zawierają aktualne wersje plików.</p></div>
            <div class="note"><h3>${ic('file', 18)} Nazwy plików</h3><p>Jeden schemat nazw dla wszystkich materiałów:</p><p><code>Schedpol_&lt;Seria&gt;_&lt;wymiar&gt;_&lt;typ&gt;.&lt;ext&gt;</code></p></div>
          </div>
        </section>
        <aside class="bezel fl-side" id="tzInline" aria-label="Teczka">
          <div class="core">
            <div class="panel-h" style="margin-bottom:0"><h2>Teczka</h2><span class="kicker">ZIP</span></div>
            <p class="mono" id="tzInSum" style="margin-top:2px;font-size:12.5px;color:var(--ink-2)"></p>
            <div class="tz-list" id="tzInList"></div>
            <div class="drawer-foot" id="tzInFoot" style="padding:16px 0 0;margin-top:12px"></div>
          </div>
        </aside>
      </div>
    </div>`;
    tzPaint();
  }

  /* ==========================================================================
     Nakładki, nawigacja, zdarzenia globalne
     ========================================================================== */
  let lastFocus = null, cmdSearch = null, firstRender = true, current = '';

  function scrim(on) { $('#scrim').classList.toggle('is-on', !!on); }
  function openTeczka() {
    closeAll();
    lastFocus = document.activeElement;
    const d = $('#teczka');
    d.classList.add('is-open'); d.setAttribute('aria-hidden', 'false'); scrim(true);
    setTimeout(function () { const b = $('.icon-btn', d); if (b) b.focus(); }, 80);
  }
  function openFacets() {
    closeAll();
    lastFocus = document.activeElement;
    const f = $('#facets');
    if (!f) return;
    f.classList.add('is-open'); scrim(true);
  }
  function openSearch() {
    closeAll();
    lastFocus = document.activeElement;
    const c = $('#cmd'), inp = $('#cmdInput');
    c.hidden = false; inp.value = '';
    cmdSearch.paint();
    setTimeout(function () { inp.focus(); }, 30);
  }
  function closeMenu() {
    $('#navLinks').classList.remove('is-open');
    const b = $('.nav-burger');
    b.classList.remove('is-open'); b.setAttribute('aria-expanded', 'false');
  }
  function closeAll(restore) {
    const d = $('#teczka'), f = $('#facets'), c = $('#cmd');
    const wasOpen = d.classList.contains('is-open') || (f && f.classList.contains('is-open')) || !c.hidden;
    d.classList.remove('is-open'); d.setAttribute('aria-hidden', 'true');
    if (f) f.classList.remove('is-open');
    c.hidden = true;
    closeMenu(); scrim(false);
    if (restore && wasOpen && lastFocus && document.contains(lastFocus)) lastFocus.focus({ preventScroll: true });
  }
  function setNav(screen, params) {
    let key = screen === 'produkt' ? 'katalog' : screen;
    if (screen === 'start' && params && params.sek) key = params.sek;
    $$('#navLinks a').forEach(function (a) {
      const on = a.getAttribute('data-nav') === key;
      a.classList.toggle('is-on', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
  }
  let io = null;
  function observeReveals() {
    const els = $$('.rv:not(.in)');
    if (!('IntersectionObserver' in window)) { els.forEach(function (el) { el.classList.add('in'); }); return; }
    if (!io) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
      }, { rootMargin: '0px 0px -6% 0px', threshold: 0.04 });
    }
    els.forEach(function (el) { io.observe(el); });
    // Zabezpieczenie dla podglądów i wydruku: po chwili odsłoń wszystko, czego obserwator nie złapał.
    setTimeout(function () { $$('.rv:not(.in)').forEach(function (el) { el.classList.add('in'); }); }, 3200);
  }

  function render(route) {
    const screen = ['start', 'katalog', 'produkt', 'pliki'].indexOf(route.screen) !== -1 ? route.screen : 'start';
    const params = route.params || {};
    closeAll();
    if (screen === 'start' && current === 'start' && params.sek && $('#sek-' + params.sek)) {
      scrollToSek(params.sek);                       // ta sama strona — tylko przewiń do sekcji
    } else if (screen === 'katalog') renderKatalog(params);
    else if (screen === 'produkt') renderProdukt(params);
    else if (screen === 'pliki') renderPliki(params);
    else renderStart(params);
    current = screen;
    app.setAttribute('data-screen', screen);
    setNav(screen, params);
    tzPaint();
    observeReveals();
    document.title = ({ start: 'Start', katalog: 'Katalog', produkt: 'Karta produktu', pliki: 'Centrum plików' })[screen] + ' — Strefa projektanta Schedpol (koncepcja A)';
    if (!firstRender) app.focus({ preventScroll: true });
    firstRender = false;
  }

  document.addEventListener('click', function (e) {
    const sg = e.target.closest('.sg-item');
    if (sg) { closeAll(); return; }
    const navA = e.target.closest('#navLinks a, .foot-links a');
    if (navA) {
      closeMenu();
      const m = /[?&]sek=(\w+)/.exec(navA.getAttribute('href') || '');
      if (m && current === 'start' && $('#sek-' + m[1])) { e.preventDefault(); scrollToSek(m[1]); setNav('start', { sek: m[1] }); }
      return;
    }
    const t = e.target.closest('[data-act]');
    if (!t) {
      const tr = e.target.closest('tr[data-href]');
      if (tr && !e.target.closest('a, button, input, label')) location.hash = tr.getAttribute('data-href');
      return;
    }
    const act = t.getAttribute('data-act');
    if (act === 'open-search') openSearch();
    else if (act === 'open-teczka') openTeczka();
    else if (act === 'open-facets') openFacets();
    else if (act === 'close-all') closeAll(true);
    else if (act === 'toggle-menu') {
      const open = !$('#navLinks').classList.contains('is-open');
      $('#navLinks').classList.toggle('is-open', open);
      t.classList.toggle('is-open', open); t.setAttribute('aria-expanded', String(open));
    }
    else if (act === 'hint') {
      const inp = $('#bigSearch');
      if (inp) { inp.value = t.getAttribute('data-q'); inp.focus(); if (bigSearch) bigSearch.paint(); $('#bigBox').classList.add('is-open'); }
    }
    else if (act === 'big-submit') { if (bigSearch) bigSearch.submit(); }
    else if (act === 'copy-ref') copyRef(t.getAttribute('data-ref'), t);
    else if (act === 'add-product') addProduct(t.getAttribute('data-ref'));
    else if (act === 'add-product-sel') {
      if (!PD.p) return;
      const sel = $$('.files-tbl input[data-file]').filter(function (i) { return i.checked; }).map(function (i) { return PD.files[+i.getAttribute('data-file')]; });
      addProduct(PD.p.ref, sel);
    }
    else if (act === 'add-series') addSeries(t.getAttribute('data-fam'));
    else if (act === 'add-type') addType(t.getAttribute('data-fam'), t.getAttribute('data-type'));
    else if (act === 'add-cad') tzAdd({ id: 'cad', title: 'Baza CAD Decor — ' + CAD.name, sub: 'aktualizacja ' + CAD.date, n: 1, mb: CAD.mb, icon: 'cube' });
    else if (act === 'tz-remove') tzRemove(t.getAttribute('data-id'));
    else if (act === 'tz-clear') { teczka = []; tzSave(); tzPaint(); toast('Teczka wyczyszczona', '', 'folder'); }
    else if (act === 'tz-zip') { const tt = tzTotals(); toast('Makieta: paczka ZIP gotowa do pobrania', pliki(tt.n) + ' · ' + mbLabel(tt.mb), 'download'); }
    else if (act === 'tz-mail') toast('Makieta: link do teczki wysłany', 'anna.nowak@…', 'mail');
    else if (act === 'demo') toast(t.getAttribute('data-msg') || 'Makieta', t.getAttribute('data-detail') || '', 'download');
    else if (act === 'gal') setStage(+t.getAttribute('data-idx'));
    else if (act === 'more') { C.limit += 24; paintCatalog(); }
    else if (act === 'view') { C.view = t.getAttribute('data-view'); paintCatalog(); syncUrl(); }
    else if (act === 'facet-more') { const id = t.getAttribute('data-facet'); C.open[id] = !C.open[id]; paintCatalog(); }
    else if (act === 'rm-q') { C.q = ''; const q = $('#catQ'); if (q) q.value = ''; C.limit = 24; paintCatalog(); syncUrl(); }
    else if (act === 'rm-filter') {
      const arr = C.f[t.getAttribute('data-facet')], i = arr.indexOf(t.getAttribute('data-value'));
      if (i !== -1) arr.splice(i, 1);
      C.limit = 24; paintCatalog(); syncUrl();
    }
    else if (act === 'clear-filters') {
      Object.keys(C.f).forEach(function (k) { C.f[k] = []; });
      C.q = ''; const q2 = $('#catQ'); if (q2) q2.value = '';
      C.limit = 24; paintCatalog(); syncUrl();
    }
    else if (act === 'ftab') {
      P.tab = t.getAttribute('data-tab'); paintPlikiTable();
      try { history.replaceState(null, '', SPProto.href('pliki', P.tab === 'all' ? {} : { typ: P.tab })); } catch (err) { /* bez historii */ }
    }
  });

  document.addEventListener('keydown', function (e) {
    const typing = /^(input|textarea|select)$/i.test(e.target.tagName || '');
    if (e.key === 'Escape') { closeAll(true); return; }
    if (e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const big = $('#bigSearch'), cq = $('#catQ');
      if (big && big.getBoundingClientRect().bottom > 80) big.focus();
      else if (cq && cq.getBoundingClientRect().bottom > 80) cq.focus();
      else openSearch();
    }
  });

  // Paleta wyszukiwania
  cmdSearch = mountSearch($('#cmdInput'), $('#cmdList'), { onClose: function () { closeAll(true); } });
  $('#cmd').addEventListener('click', function (e) { if (e.target === e.currentTarget) closeAll(true); });

  // Cień wyspy nawigacji po przewinięciu
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { $('#nav').classList.toggle('is-scrolled', !en[0].isIntersecting); }).observe($('#topSentinel'));
  }

  SPI.hydrate(document);
  SPProto.init({
    concept: 'A', name: 'Biblioteka',
    screens: [
      { id: 'start', label: 'Start' },
      { id: 'katalog', label: 'Katalog' },
      { id: 'produkt', label: 'Karta produktu' },
      { id: 'pliki', label: 'Pliki' }
    ],
    render: render
  });
})();
