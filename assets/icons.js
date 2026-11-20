/* Wspólny zestaw ikon liniowych (24×24, cienka kreska) — makiety portalu Schedpol dla projektantów LM.
   Użycie:  SPI.icon('search')  |  SPI.icon('download', { size: 18, sw: 1.4, cls: 'moja-klasa' })  → string z <svg> */
(function (w) {
  var P = {
    search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    download: '<path d="M12 4v11"/><path d="M7.5 11.5L12 16l4.5-4.5"/><path d="M5 19.5h14"/>',
    file: '<path d="M6.5 3.5H14l4 4v13h-11.5z"/><path d="M14 3.5v4h4"/>',
    cube: '<path d="M12 3.5l7.5 4.25v8.5L12 20.5l-7.5-4.25v-8.5z"/><path d="M4.5 7.75L12 12l7.5-4.25"/><path d="M12 12v8.5"/>',
    ruler: '<path d="M4 15.5L15.5 4 20 8.5 8.5 20z"/><path d="M7.5 12l1.5 1.5M10 9.5l1.5 1.5M12.5 7l1.5 1.5"/>',
    layers: '<path d="M12 4l8 4.5-8 4.5-8-4.5z"/><path d="M4 12.5l8 4.5 8-4.5"/><path d="M4 16l8 4.5 8-4.5"/>',
    bookmark: '<path d="M7 4h10v16l-5-3.5L7 20z"/>',
    heart: '<path d="M12 19.5s-7-4.3-7-9.4a3.9 3.9 0 0 1 7-2.5 3.9 3.9 0 0 1 7 2.5c0 5.1-7 9.4-7 9.4z"/>',
    'arrow-right': '<path d="M5 12h14"/><path d="M13.5 6.5L19 12l-5.5 5.5"/>',
    'arrow-left': '<path d="M19 12H5"/><path d="M10.5 6.5L5 12l5.5 5.5"/>',
    'arrow-up-right': '<path d="M7 17L17 7"/><path d="M9 7h8v8"/>',
    'chevron-down': '<path d="M6 9.5l6 6 6-6"/>',
    'chevron-right': '<path d="M9.5 6l6 6-6 6"/>',
    'chevron-left': '<path d="M14.5 6l-6 6 6 6"/>',
    filter: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
    grid: '<path d="M4.5 4.5h6v6h-6zM13.5 4.5h6v6h-6zM4.5 13.5h6v6h-6zM13.5 13.5h6v6h-6z"/>',
    list: '<path d="M8.5 6.5h11M8.5 12h11M8.5 17.5h11"/><path d="M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01"/>',
    phone: '<path d="M6.5 4.5h3l1.5 4-2 1.5a10 10 0 0 0 5 5l1.5-2 4 1.5v3a1.5 1.5 0 0 1-1.6 1.5A14.5 14.5 0 0 1 5 6.1a1.5 1.5 0 0 1 1.5-1.6z"/>',
    mail: '<path d="M4 6.5h16v11H4z"/><path d="M4.5 7l7.5 6 7.5-6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    play: '<path d="M8 5.5v13l11-6.5z"/>',
    image: '<path d="M4 5.5h16v13H4z"/><path d="M4 15l4.5-4.5 4 4 3-3 4.5 4.5"/><circle cx="15.5" cy="9.5" r="1.3"/>',
    folder: '<path d="M4 7a1 1 0 0 1 1-1h4.5l2 2H19a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z"/>',
    copy: '<path d="M9 9h10v10H9z"/><path d="M5 15V5h10"/>',
    home: '<path d="M4.5 11L12 4.5l7.5 6.5"/><path d="M6.5 9.5v10h11v-10"/>',
    user: '<circle cx="12" cy="8.5" r="3.5"/><path d="M5 19.5c1-3.5 4-5 7-5s6 1.5 7 5"/>',
    bell: '<path d="M6.5 16.5v-5a5.5 5.5 0 0 1 11 0v5l1.5 2h-14z"/><path d="M10 20.5h4"/>',
    clipboard: '<path d="M8 5.5H6v15h12v-15h-2"/><path d="M8 4h8v3H8z"/><path d="M9 11h6M9 14.5h6"/>',
    compass: '<circle cx="12" cy="12" r="8"/><path d="M14.8 9.2l-1.6 4-4 1.6 1.6-4z"/>',
    eye: '<path d="M3.5 12s3-6 8.5-6 8.5 6 8.5 6-3 6-8.5 6-8.5-6-8.5-6z"/><circle cx="12" cy="12" r="2.5"/>',
    book: '<path d="M5 5.5c2.5-1 5-1 7 .5v13c-2-1.5-4.5-1.5-7-.5z"/><path d="M19 5.5c-2.5-1-5-1-7 .5v13c2-1.5 4.5-1.5 7-.5z"/>',
    external: '<path d="M14 5h5v5"/><path d="M19 5l-8 8"/><path d="M17 13.5V19H5V7h5.5"/>',
    print: '<path d="M7 8V4.5h10V8"/><path d="M7 16.5H4.5V9h15v7.5H17"/><path d="M7 13.5h10v6H7z"/>',
    info: '<circle cx="12" cy="12" r="8"/><path d="M12 11v5M12 8h.01"/>',
    'box-check': '<path d="M4 8l8-4 8 4v8l-8 4-8-4z"/><path d="M8.5 12.2l2.4 2.4 4.6-4.8"/>',
    cart: '<path d="M3 4.5h2.2l2.1 9.8a1.5 1.5 0 0 0 1.5 1.2h8.3a1.5 1.5 0 0 0 1.5-1.1l1.6-6.4H6"/><circle cx="9.5" cy="19.5" r="1.3"/><circle cx="17" cy="19.5" r="1.3"/>',
    truck: '<path d="M2.5 6.5h11v9.8"/><path d="M2.5 6.5v9.8h2.2M8.3 16.3h5.2M13.5 9.5h4l3 3.3v3.5h-1.7"/><circle cx="6.5" cy="17" r="1.8"/><circle cx="17" cy="17" r="1.8"/>',
    clock: '<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>',
    drop: '<path d="M12 4s6 6.2 6 10.3a6 6 0 0 1-12 0C6 10.2 12 4 12 4z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    swap: '<path d="M7 7h12l-3-3"/><path d="M17 17H5l3 3"/>',
    pin: '<path d="M12 20.5s6-5.6 6-10.3a6 6 0 0 0-12 0c0 4.7 6 10.3 6 10.3z"/><circle cx="12" cy="10" r="2.2"/>',
    shield: '<path d="M12 3.5l7 2.5v5.5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2.2 2.2L15 10.4"/>',
    send: '<path d="M4.5 11.5l15-7-5.5 15.5-3-6.5z"/><path d="M11 13.5l8.5-9"/>',
    qr: '<path d="M4.5 4.5h6v6h-6zM13.5 4.5h6v6h-6zM4.5 13.5h6v6h-6z"/><path d="M13.5 13.5h2.5v2.5M19.5 13.5v.01M13.5 19.5h.01M17 17h2.5v2.5"/>',
    square: '<path d="M5 5h14v14H5z"/>',
    rect: '<path d="M3.5 7h17v10h-17z"/>',
    quarter: '<path d="M5 5h14a0 0 0 0 1 0 0c0 7.7-6.3 14-14 14z"/>',
    penta: '<path d="M5 5h14v8l-6 6H5z"/>',
    star: '<path d="M12 4.5l2.3 4.9 5.2.7-3.8 3.7.9 5.2-4.6-2.5-4.6 2.5.9-5.2-3.8-3.7 5.2-.7z"/>',
    zip: '<path d="M6.5 3.5H14l4 4v13h-11.5z"/><path d="M14 3.5v4h4"/><path d="M10 10v1.2M10 13v1.2M10 16v1.2"/>',
    video: '<path d="M4 6.5h11.5v11H4z"/><path d="M15.5 10.5l4.5-2.5v8l-4.5-2.5"/>',
    settings: '<circle cx="12" cy="12" r="2.8"/><path d="M12 4v2.2M12 17.8V20M4 12h2.2M17.8 12H20M6.3 6.3l1.6 1.6M16.1 16.1l1.6 1.6M17.7 6.3l-1.6 1.6M7.9 16.1l-1.6 1.6"/>',
    logout: '<path d="M10 5H5.5v14H10"/><path d="M10 12h9"/><path d="M15.5 8.5L19 12l-3.5 3.5"/>',
    help: '<circle cx="12" cy="12" r="8"/><path d="M9.8 9.6a2.3 2.3 0 0 1 4.4.9c0 1.6-2.2 1.9-2.2 3.4M12 16.6h.01"/>'
  };
  w.SPI = {
    names: Object.keys(P),
    icon: function (name, o) {
      o = o || {};
      var s = o.size || 20, sw = o.sw || 1.5;
      return '<svg class="i i-' + name + (o.cls ? ' ' + o.cls : '') + '" width="' + s + '" height="' + s +
        '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + sw +
        '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (P[name] || P.square) + '</svg>';
    },
    /* Zamienia w DOM elementy <i data-i="search" data-size="18"></i> na ikony */
    hydrate: function (root) {
      (root || document).querySelectorAll('[data-i]').forEach(function (el) {
        if (el.dataset.done) return;
        el.innerHTML = w.SPI.icon(el.dataset.i, { size: +el.dataset.size || 20, sw: +el.dataset.sw || 1.5 });
        el.dataset.done = '1';
        el.style.display = el.style.display || 'inline-flex';
      });
    }
  };
})(window);
