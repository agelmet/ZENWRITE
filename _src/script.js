(function () {
  var d = document, H = d.documentElement, W = window;
  var RM = matchMedia('(prefers-reduced-motion:reduce)').matches;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };

  /* intro: the book opens, once per session */
  if (H.classList.contains('zi')) {
    var endIntro = function () { H.classList.remove('zi'); var i = $('.intro'); if (i) i.remove(); };
    setTimeout(endIntro, d.hidden ? 0 : 2250);
  }

  /* headings: one move per section */
  function words(h, fn) {
    var k = 0;
    (function walk(n) {
      [].slice.call(n.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var f = d.createDocumentFragment();
          c.textContent.split(/(\s+)/).forEach(function (w) {
            if (!w) return;
            if (/^\s+$/.test(w)) { f.appendChild(d.createTextNode(' ')); return; }
            f.appendChild(fn(w, k++));
          });
          c.replaceWith(f);
        } else if (c.nodeType === 1 && c.tagName !== 'BR') walk(c);
      });
    })(h);
  }
  $$('[data-fx]').forEach(function (h) {
    var fx = h.dataset.fx;
    if (RM || fx === 'brush') return;
    h.setAttribute('aria-label', h.textContent.replace(/\s+/g, ' ').trim());
    var li = 0;
    words(h, function (w, k) {
      var o = d.createElement('span');
      o.setAttribute('aria-hidden', 'true');
      if (fx === 'mask') { o.className = 'wd'; var i = d.createElement('span'); i.textContent = w; i.style.setProperty('--k', k); o.appendChild(i); }
      else if (fx === 'light') { o.className = 'lt'; o.textContent = w; o.style.setProperty('--k', k); }
      else { o.className = 'lw'; Array.from(w).forEach(function (ch) { var s = d.createElement('span'); s.className = 'lc'; s.textContent = ch; s.style.setProperty('--k', li++); o.appendChild(s); }); }
      return o;
    });
  });

  /* reveals */
  var targets = $$('[data-rv],[data-fx],.kicker,.ct,.pr-c,.draw');
  if (RM || !('IntersectionObserver' in W)) targets.forEach(function (e) { e.classList.add('in', 'fx-in'); });
  else {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in', 'fx-in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .04 });
    targets.forEach(function (e) { io.observe(e); });
    setTimeout(function () { if (d.hidden) targets.forEach(function (e) { e.classList.add('in', 'fx-in'); }); }, 2500);
  }

  /* pause ambient motion off screen */
  if ('IntersectionObserver' in W) {
    var po = new IntersectionObserver(function (es) { es.forEach(function (en) { en.target.classList.toggle('off', !en.isIntersecting); }); });
    $$('.hero,.sh,.tick,.tl,.ct,section').forEach(function (s) { po.observe(s); });
  }

  /* header: menus */
  var hd = $('#hd'), mgli = $('.has-mg'), nvb = $('.nv-b');
  if (nvb) nvb.addEventListener('click', function () { var o = mgli.classList.toggle('open'); nvb.setAttribute('aria-expanded', o); });
  d.addEventListener('click', function (ev) { if (mgli && !mgli.contains(ev.target)) { mgli.classList.remove('open'); nvb.setAttribute('aria-expanded', 'false'); } });
  var dr = $('#drawer'), bg = $('.burger');
  function drawer(o) { dr.hidden = !o; bg.setAttribute('aria-expanded', o); d.body.style.overflow = o ? 'hidden' : ''; if (o) $('.dr-x').focus(); }
  if (bg) bg.addEventListener('click', function () { drawer(true); });
  if (dr) { $('.dr-x').addEventListener('click', function () { drawer(false); }); $$('a', dr).forEach(function (a) { a.addEventListener('click', function () { drawer(false); }); }); }
  d.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { if (dr && !dr.hidden) drawer(false); if (mgli) mgli.classList.remove('open'); } });

  /* FAQ: one open at a time */
  $$('.faq-l').forEach(function (l) {
    var ds = $$('details', l);
    ds.forEach(function (x) { x.addEventListener('toggle', function () { if (x.open) ds.forEach(function (y) { if (y !== x) y.open = false; }); }); });
  });

  /* hero: pointer depth */
  var hero = $('.hero-v');
  if (hero && !RM && matchMedia('(hover:hover) and (pointer:fine)').matches) {
    var tx = 0, ty = 0, cx = 0, cy = 0, run = false, hs = $('.hero');
    var tick = function () { cx += (tx - cx) * .08; cy += (ty - cy) * .08; hero.style.setProperty('--mx', cx.toFixed(3)); hero.style.setProperty('--my', cy.toFixed(3)); if (Math.abs(tx - cx) + Math.abs(ty - cy) > .002) requestAnimationFrame(tick); else run = false; };
    hs.addEventListener('pointermove', function (ev) { tx = ev.clientX / innerWidth - .5; ty = ev.clientY / innerHeight - .5; if (!run) { run = true; requestAnimationFrame(tick); } });
  }

  /* spotlight on cards */
  if (matchMedia('(hover:hover)').matches) $$('.in-c').forEach(function (c) {
    c.addEventListener('pointermove', function (ev) { var r = c.getBoundingClientRect(); c.style.setProperty('--x', (ev.clientX - r.left) + 'px'); c.style.setProperty('--y', (ev.clientY - r.top) + 'px'); });
  });

  /* philosophy: words come into ink with the scroll */
  var pq = $('[data-scrub]'), pw = [];
  if (pq && !RM) {
    var em = ['ΜΑΖΙ', 'WITH'];
        words(pq, function (w) { var s = d.createElement('span'); s.className = 'w' + (/^(μαζί|σας,|with|you,)$/i.test(w) ? ' v' : ''); s.textContent = w; pw.push(s); return s; });
  }

  /* journey: brush path through the stations */
  var jr = $('.jr'), jw = $('.jr-w'), jp = $('.jr-p'), jb = $('.jr-bg'), walk = $('.jr-walk'), stations = $$('.jr-s'), jpts = [], jlen = 0, jsamp = [];
  function jBuild() {
    if (!jw) return;
    var wr = jw.getBoundingClientRect(), pts = stations.map(function (s) { var r = $('.jr-d', s).getBoundingClientRect(); return [r.left - wr.left + r.width / 2, r.top - wr.top + r.height / 2]; });
    var dd = 'M' + pts[0][0] + ' ' + (pts[0][1] - 60);
    dd += ' L' + pts[0][0] + ' ' + pts[0][1];
    for (var i = 1; i < pts.length; i++) {
      var a = pts[i - 1], b = pts[i], my = (a[1] + b[1]) / 2;
      dd += ' C' + a[0] + ' ' + my + ' ' + b[0] + ' ' + my + ' ' + b[0] + ' ' + b[1];
    }
    var last = pts[pts.length - 1]; dd += ' L' + last[0] + ' ' + (last[1] + 60);
    jp.setAttribute('d', dd); jb.setAttribute('d', dd);
    jlen = jp.getTotalLength(); jp.style.strokeDasharray = jlen; jp.style.strokeDashoffset = jlen;
    jsamp = []; for (var k = 0; k <= 200; k++) { var p = jp.getPointAtLength(jlen * k / 200); jsamp.push([p.x, p.y]); }
    jpts = pts;
  }

  /* one scroll handler */
  var prog = $('.prog i'), tt = $('.totop'), tk = $('.tick-i'), lastY = scrollY, ticking = false, sk = 0;
  function onScroll() {
    ticking = false;
    var y = scrollY, h = d.documentElement.scrollHeight - innerHeight, p = h > 0 ? y / h : 0;
    if (prog) prog.style.setProperty('--p', p.toFixed(4));
    if (tt) tt.style.setProperty('--p', p.toFixed(4));
    hd.classList.toggle('solid', y > 30);
    H.classList.toggle('scrolled', y > innerHeight * .6);
    if (hero && y < innerHeight * 1.2) hero.style.setProperty('--sy', (y / innerHeight).toFixed(3));
    if (tk && !RM) { var v = Math.max(-8, Math.min(8, (y - lastY) * .25)); sk += (v - sk) * .3; tk.style.setProperty('--sk', sk.toFixed(2) + 'deg'); if (Math.abs(sk) > .05) req(); }
    lastY = y;
    if (pw.length) {
      var r = pq.getBoundingClientRect(), t = (innerHeight * .82 - r.top) / (r.height + innerHeight * .35);
      var n = Math.round(Math.max(0, Math.min(1, t)) * pw.length);
      for (var i = 0; i < pw.length; i++) pw[i].classList.toggle('lit', i < n);
    }
    if (jlen && !RM) {
      var wr = jw.getBoundingClientRect(), q = Math.max(0, Math.min(1, (innerHeight * .6 - wr.top) / wr.height));
      jp.style.strokeDashoffset = (jlen * (1 - q)).toFixed(1);
      var s = jsamp[Math.round(q * 200)];
      walk.style.setProperty('--wx', s[0] + 'px'); walk.style.setProperty('--wy', s[1] + 'px');
      jr.classList.toggle('go', q > 0 && q < 1);
      stations.forEach(function (st, i) { st.classList.toggle('on', jpts[i] && s[1] >= jpts[i][1] - 4); });
    }
  }
  function req() { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }
  addEventListener('scroll', req, { passive: true });
  addEventListener('resize', function () { jBuild(); req(); });
  if (jw) {
    if (RM) stations.forEach(function (s) { s.classList.add('on'); });
    (d.fonts && d.fonts.ready ? d.fonts.ready : Promise.resolve()).then(function () { jBuild(); req(); });
  }
  onScroll();

  /* quote composer */
  var qf = $('#qf'), lt = $('#letter');
  if (qf && lt) {
    var L = JSON.parse(lt.dataset.l), body = $('#ltb'), seal = $('.lt-seal'), send = $('#qsend'), out = $('#qo'), lang = H.lang;
    var nf = function (n) { return n.toLocaleString(lang === 'el' ? 'el-GR' : 'en-GB'); };
    var params = new URLSearchParams(location.search), pre = params.get('t');
    if (pre) { var r0 = $('input[data-k="' + pre + '"]', qf); if (r0) r0.checked = true; }
    var typer = null, shown = '';
    function text() {
      var f = qf.elements, ty = (qf.querySelector('input[name=qt]:checked') || {}).value || '';
      var ln = +f.ln.value, pg = Math.round(ln / 300);
      out.textContent = nf(ln) + ' ' + L.q_words + ' · ≈ ' + nf(pg) + ' ' + L.q_pages;
      var lines = [L.q_hello, '', L.q_intro + ': ' + ty + '.', ''];
      lines.push('— ' + L.q_level + ': ' + f.lv.value);
      if (f.fd.value.trim()) lines.push('— ' + L.q_field + ': ' + f.fd.value.trim());
      lines.push('— ' + L.q_len + ': ≈ ' + nf(ln) + ' ' + L.q_words);
      if (f.dl.value) { var dt = new Date(f.dl.value + 'T12:00'); lines.push('— ' + L.q_dead + ': ' + dt.toLocaleDateString(lang === 'el' ? 'el-GR' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric' })); }
      lines.push('— ' + L.q_langl + ': ' + (qf.querySelector('input[name=ql]:checked') || {}).value);
      lines.push('— ' + L.q_style + ': ' + f.st.value);
      if (f.nt.value.trim()) lines.push('', f.nt.value.trim());
      lines.push('', L.q_bye, f.nm.value.trim() || '');
      return lines.join('\n');
    }
    function render(anim) {
      var t = text();
      send.href = 'mailto:' + lt.dataset.to + '?subject=' + encodeURIComponent(lt.dataset.sub + ' — ' + ((qf.querySelector('input[name=qt]:checked') || {}).value || '')) + '&body=' + encodeURIComponent(t);
      seal.classList.add('on');
      clearInterval(typer);
      if (!anim || RM) { body.textContent = t; shown = t; return; }
      var start = 0; while (start < shown.length && shown[start] === t[start]) start++;
      var i = start;
      typer = setInterval(function () {
        i = Math.min(t.length, i + 3);
        body.textContent = t.slice(0, i);
        var c = d.createElement('span'); c.className = 'car'; body.appendChild(c);
        if (i >= t.length) { clearInterval(typer); shown = t; }
      }, 16);
    }
    qf.addEventListener('input', function () { render(true); });
    qf.addEventListener('change', function () { render(true); });
    qf.addEventListener('submit', function (ev) { ev.preventDefault(); });
    render(false);
    var cp = $('#qcopy');
    cp.addEventListener('click', function () {
      var done = function () { cp.textContent = L.q_copied; setTimeout(function () { cp.textContent = L.q_copy; }, 1800); };
      if (navigator.clipboard) navigator.clipboard.writeText(text()).then(done, done); else done();
    });
  }

  /* hero: a live regression the visitor can push around */
  var ch = $('#chart');
  if (ch) (function () {
    var P = JSON.parse(ch.dataset.pts), svg = $('.ch-svg', ch), line = $('#rgLine'), band = $('#rgBand'), nw = $('#rgNew'), note = $('#rgNote'), cross = $('.rg-x', nw);
    var X0 = 112, X1 = 732, Y0 = 604, Y1 = 136, el = H.lang === 'el';
    var MX = function (x) { return X0 + (X1 - X0) * x / 10; }, MY = function (y) { return Y0 - (Y0 - Y1) * y / 10; };
    var F = function (v, n) { var s = v.toFixed(n); return el ? s.replace('.', ',') : s; };
    var cl = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
    var cur = { x: 8.4, y: 2.4 }, tgt = { x: 8.4, y: 2.4 }, act = 0, actT = 0, W = 6, live = false, auto = !matchMedia('(hover:hover) and (pointer:fine)').matches;
    var WOB = [0, 1.2, -.9, .8, -1.1, .7, -.6, 0];
    function phi(z) { var t = 1 / (1 + .2316419 * Math.abs(z)), d = .3989423 * Math.exp(-z * z / 2), p = d * t * (.3193815 + t * (-.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return z > 0 ? 1 - p : p; }
    function fit() {
      var n = 0, sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0;
      function add(x, y, w) { n += w; sx += w * x; sy += w * y; sxx += w * x * x; syy += w * y * y; sxy += w * x * y; }
      P.forEach(function (p) { add(p[0], p[1], 1); });
      if (act > .01) add(cur.x, cur.y, W * act);
      var mx = sx / n, my = sy / n, Sxx = sxx - n * mx * mx, Syy = syy - n * my * my, Sxy = sxy - n * mx * my;
      var b = Sxy / Sxx, a = my - b * mx, r = Sxy / Math.sqrt(Sxx * Syy), N = P.length + (act > .5 ? 1 : 0);
      var s = Math.sqrt(Math.max(1e-6, (Syy - b * Sxy) / (n - 2)));
      return { a: a, b: b, r: r, mx: mx, Sxx: Sxx, s: s, n: n, N: N };
    }
    function render() {
      var f = fit(), xa = .3, xb = 9.7;
      if (Math.abs(f.b) > 1e-6) { var x0 = (0 - f.a) / f.b, x10 = (10 - f.a) / f.b; xa = Math.max(xa, Math.min(x0, x10)); xb = Math.min(xb, Math.max(x0, x10)); }
      var d = '';
      for (var i = 0; i < 8; i++) { var x = xa + (xb - xa) * i / 7; d += (i ? 'L' : 'M') + MX(x).toFixed(1) + ' ' + (MY(f.a + f.b * x) + WOB[i]).toFixed(1); }
      line.setAttribute('d', d);
      var up = '', lo = [];
      for (var k = 0; k <= 16; k++) {
        var xx = .3 + 9.4 * k / 16, yh = f.a + f.b * xx, se = 1.96 * f.s * Math.sqrt(1 / f.n + (xx - f.mx) * (xx - f.mx) / f.Sxx);
        up += (k ? 'L' : 'M') + MX(xx).toFixed(1) + ' ' + MY(cl(yh + se, 0, 10)).toFixed(1);
        lo.push(MX(xx).toFixed(1) + ' ' + MY(cl(yh - se, 0, 10)).toFixed(1));
      }
      band.setAttribute('d', up + 'L' + lo.reverse().join('L') + 'Z');
      var t = f.r * Math.sqrt((f.N - 2) / Math.max(1e-6, 1 - f.r * f.r)), p = 2 * (1 - phi(Math.abs(t)));
      var ps = p < .001 ? '< ' + F(.001, 3) : '= ' + F(p, 3);
      note.textContent = 'r = ' + F(f.r, 2) + ' · p ' + ps;
      note.setAttribute('y', cl(MY(f.a + f.b * 9.7) - 26, 150, 560).toFixed(0));
      $('#cfA').textContent = F(f.a, 2); $('#cfB').textContent = F(f.b, 2); $('#cfR').textContent = F(f.r, 2);
      $('#cfT').textContent = F(t, 2); $('#cfP').textContent = p < .001 ? '< ' + F(.001, 3) : F(p, 3);
      $('#cfR2').textContent = F(f.r * f.r, 2); $('#cfN').textContent = f.N;
      var px = MX(cur.x), py = MY(cur.y);
      nw.setAttribute('transform', 'translate(' + px.toFixed(1) + ' ' + py.toFixed(1) + ')');
      cross.setAttribute('d', 'M0 0H' + (X0 - px).toFixed(1) + 'M0 0V' + (Y0 - py).toFixed(1));
      nw.classList.toggle('on', act > .5);
    }
    var run = false, t0 = performance.now();
    function loop(now) {
      if (auto) { var tt = (now - t0) / 1000; tgt.x = 5.2 + 3.6 * Math.sin(tt * .32); tgt.y = 4.6 + 3.9 * Math.cos(tt * .47); actT = 1; }
      cur.x += (tgt.x - cur.x) * .1; cur.y += (tgt.y - cur.y) * .1; act += (actT - act) * .12;
      render();
      var moving = Math.abs(tgt.x - cur.x) + Math.abs(tgt.y - cur.y) + Math.abs(actT - act) > .004;
      if ((auto || moving) && !d.hidden && !ch.closest('section').classList.contains('off')) requestAnimationFrame(loop); else run = false;
    }
    function kick() { if (!run && live) { run = true; requestAnimationFrame(loop); } }
    setTimeout(function () {
      live = true; line.classList.add('live'); band.classList.add('on'); render();
      if (RM) return;
      if (auto) { kick(); addEventListener('scroll', kick, { passive: true }); }
    }, RM ? 0 : (H.classList.contains('zi') ? 3600 : 3300));
    if (!auto && !RM) {
      var hs = $('.hero');
      hs.addEventListener('pointermove', function (ev) {
        if (!live) return;
        var m = svg.getScreenCTM(); if (!m) return;
        var pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; pt = pt.matrixTransform(m.inverse());
        var x = (pt.x - X0) / (X1 - X0) * 10, y = (Y0 - pt.y) / (Y0 - Y1) * 10;
        if (x > -1 && x < 11 && y > -1 && y < 11) { tgt.x = cl(x, .2, 9.8); tgt.y = cl(y, .2, 9.8); actT = 1; } else actT = 0;
        kick();
      });
      hs.addEventListener('pointerleave', function () { actT = 0; kick(); });
    }
  })();
})();
