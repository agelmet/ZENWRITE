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
})();
