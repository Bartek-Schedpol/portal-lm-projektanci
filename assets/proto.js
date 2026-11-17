/* Pasek prezentera + prosty router ekranów dla makiet (wspólny dla koncepcji A/B/C).
   Nie jest częścią projektu portalu — służy wyłącznie do przeglądania makiety.

   Użycie w makiecie:
     SPProto.init({
       concept: 'A', name: 'Biblioteka',
       screens: [{ id: 'start', label: 'Start' }, { id: 'katalog', label: 'Katalog', match: ['katalog', 'produkt'] }],
       render: function (route) { ... }      // route = { screen: 'katalog', params: { seria: 'Balans' } }
     });
     SPProto.go('produkt', { ref: '89189406' });     // nawigacja programowa  →  #/produkt?ref=89189406
     <a href="#/katalog?seria=Balans">…</a>          // albo zwykły link

   Dodatki: klawisze ← / → przełączają ekrany, „H" chowa pasek; parametr ?clean=1 w adresie ukrywa pasek (podglądy). */
(function (w, d) {
  var cfg = null, dock = null;
  var CONCEPTS = [
    { id: 'A', name: 'Biblioteka', href: '../a-biblioteka/index.html' },
    { id: 'B', name: 'Pracownia', href: '../b-pracownia/index.html' },
    { id: 'C', name: 'Showroom', href: '../c-showroom/index.html' }
  ];
  var CSS = '' +
    '.spp{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:2147483000;display:flex;align-items:center;gap:4px;' +
    'padding:5px;border-radius:999px;background:rgba(18,18,20,.92);color:#fff;font:500 12px/1 "Segoe UI",system-ui,sans-serif;' +
    'box-shadow:0 10px 40px rgba(0,0,0,.28),inset 0 0 0 1px rgba(255,255,255,.08);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);' +
    'transition:transform .5s cubic-bezier(.32,.72,0,1),opacity .4s;max-width:calc(100vw - 24px);white-space:nowrap}' +
    '.spp.is-hidden{transform:translate(-50%,calc(100% + 30px));opacity:0;pointer-events:none}' +
    '.spp a,.spp button{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:6px;height:30px;padding:0 12px;border-radius:999px;' +
    'color:rgba(255,255,255,.72);font:inherit;letter-spacing:.01em;transition:background .25s,color .25s}' +
    '.spp a:hover,.spp button:hover{background:rgba(255,255,255,.1);color:#fff}' +
    '.spp .on{background:#fff;color:#111}.spp .on:hover{background:#fff;color:#111}' +
    '.spp .sep{width:1px;height:18px;background:rgba(255,255,255,.16);margin:0 4px;flex:none}' +
    '.spp .lbl{padding:0 10px 0 12px;color:rgba(255,255,255,.5);font-size:11px;text-transform:uppercase;letter-spacing:.12em}' +
    '.spp .cc{width:30px;padding:0;justify-content:center;font-weight:600}' +
    '.spp .scr{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none}.spp .scr::-webkit-scrollbar{display:none}' +
    '.spp-show{all:unset;cursor:pointer;position:fixed;right:14px;bottom:14px;z-index:2147483000;' +
    'width:34px;height:34px;border-radius:50%;background:rgba(18,18,20,.85);color:#fff;display:none;align-items:center;justify-content:center;' +
    'font:600 12px "Segoe UI",system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.25)}' +
    '.spp-show.on{display:flex}' +
    '@media (max-width:720px){.spp .lbl,.spp .back span{display:none}.spp{bottom:10px}}' +
    '@media print{.spp,.spp-show{display:none!important}}';

  function parse() {
    var h = (location.hash || '').replace(/^#\/?/, '');
    var parts = h.split('?');
    var params = {};
    (parts[1] || '').split('&').forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf('=');
      var k = decodeURIComponent(i < 0 ? kv : kv.slice(0, i));
      params[k] = i < 0 ? '' : decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' '));
    });
    return { screen: parts[0] || (cfg && cfg.screens[0].id) || '', params: params };
  }
  function tabFor(screen) {
    var hit = null;
    cfg.screens.forEach(function (s) { if (s.id === screen || (s.match || []).indexOf(screen) !== -1) hit = hit || s.id; });
    return hit;
  }
  function paint(route) {
    if (!dock) return;
    var t = tabFor(route.screen);
    dock.querySelectorAll('[data-scr]').forEach(function (b) { b.classList.toggle('on', b.dataset.scr === t); });
  }
  function onRoute() {
    var r = parse();
    try { cfg.render(r); } catch (e) { console.error('[SPProto] render error', e); }
    paint(r);
    if (!r.params.keep) w.scrollTo(0, 0);
    d.documentElement.setAttribute('data-screen', r.screen);
  }
  function build() {
    if (/[?&]clean=1/.test(location.search)) return;
    var st = d.createElement('style'); st.textContent = CSS; d.head.appendChild(st);
    dock = d.createElement('nav'); dock.className = 'spp'; dock.setAttribute('aria-label', 'Pasek prezentera makiety');
    var solo = !!w.SPP_SOLO;                      // publikacja samej makiety (bez opracowania i koncepcji B/C)
    var h = solo ? '' : '<a class="back" href="../index.html" title="Powrót do opracowania">←<span>Opracowanie</span></a><span class="sep"></span>';
    if (!solo) CONCEPTS.forEach(function (c) {
      h += '<a class="cc' + (c.id === cfg.concept ? ' on' : '') + '" href="' + c.href + '" title="Koncepcja ' + c.id + ' — ' + c.name + '">' + c.id + '</a>';
    });
    h += '<span class="lbl">' + cfg.name + '</span><span class="sep"></span><span class="scr">';
    cfg.screens.forEach(function (s) { h += '<button data-scr="' + s.id + '">' + s.label + '</button>'; });
    h += '</span><span class="sep"></span><button data-hide title="Ukryj pasek (klawisz H)">✕</button>';
    dock.innerHTML = h; d.body.appendChild(dock);
    var show = d.createElement('button'); show.className = 'spp-show'; show.textContent = cfg.concept; show.title = 'Pokaż pasek prezentera';
    d.body.appendChild(show);
    function toggle(v) { dock.classList.toggle('is-hidden', v); show.classList.toggle('on', v); }
    dock.addEventListener('click', function (e) {
      var b = e.target.closest('[data-scr]');
      if (b) { api.go(b.dataset.scr); return; }
      if (e.target.closest('[data-hide]')) toggle(true);
    });
    show.addEventListener('click', function () { toggle(false); });
    d.addEventListener('keydown', function (e) {
      if (/input|textarea|select/i.test((e.target.tagName || '')) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'h' || e.key === 'H') toggle(!dock.classList.contains('is-hidden'));
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        var ids = cfg.screens.map(function (s) { return s.id; });
        var i = ids.indexOf(tabFor(parse().screen));
        var n = e.key === 'ArrowRight' ? Math.min(ids.length - 1, i + 1) : Math.max(0, i - 1);
        if (n !== i) api.go(ids[n]);
      }
    });
  }
  var api = {
    init: function (c) {
      cfg = c;
      build();
      w.addEventListener('hashchange', onRoute);
      onRoute();
    },
    go: function (screen, params) {
      var q = [];
      Object.keys(params || {}).forEach(function (k) {
        if (params[k] !== undefined && params[k] !== null && params[k] !== '') q.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      });
      var target = '#/' + screen + (q.length ? '?' + q.join('&') : '');
      if (location.hash === target) onRoute(); else location.hash = target;
    },
    route: parse,
    href: function (screen, params) {
      var q = [];
      Object.keys(params || {}).forEach(function (k) { q.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k])); });
      return '#/' + screen + (q.length ? '?' + q.join('&') : '');
    }
  };
  w.SPProto = api;
})(window, document);
