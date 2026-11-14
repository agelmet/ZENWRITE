/* form of interest (14 Nov 2026): the quote composer now SENDS — POST to advonmedia.com/api/form → Resend → the client's inbox.
   If the relay can't be reached, the same message opens in the visitor's e-mail app (mailto fallback). Nothing is stored here. */
(function () {
  var d = document, f = d.getElementById('qf'), b = d.getElementById('qsend'), lt = d.getElementById('letter');
  if (!f || !b || !lt) return;
  var EL = d.documentElement.lang !== 'en', API = 'https://advonmedia.com/api/form', stamp = '', asked = 0, busy = 0;
  var T = EL ? {
    name: 'Γράψτε το ονοματεπώνυμό σας.', email: 'Γράψτε ένα σωστό e-mail, για να σας στείλουμε την προσφορά.',
    phone: 'Ο αριθμός δεν φαίνεται σωστός — διορθώστε τον ή αφήστε το πεδίο κενό.', ok: 'Χρειάζεται η συγκατάθεσή σας για να σας απαντήσουμε.',
    sending: 'Αποστολή…', fail: 'Δεν ήταν δυνατή η αποστολή από εδώ — ανοίγουμε το μήνυμα στο πρόγραμμα e-mail σας.',
    title: 'Αίτημα προσφοράς', q: ['Υπηρεσία', 'Επίπεδο / ίδρυμα', 'Αντικείμενο ή τμήμα', 'Έκταση', 'Προθεσμία', 'Γλώσσα', 'Σύστημα παραπομπών'],
    words: 'λέξεις', h: 'Το αίτημά σας στάλθηκε', p1: 'Σας ευχαριστούμε! Θα σας απαντήσουμε σύντομα στο ', p2: ' με προσφορά και χρονοδιάγραμμα.'
  } : {
    name: 'Please write your full name.', email: 'Please write a valid e-mail so we can send you the quote.',
    phone: 'This number doesn’t look right — fix it or leave the field empty.', ok: 'We need your consent to reply to you.',
    sending: 'Sending…', fail: 'We couldn’t send it from here — opening the message in your e-mail app.',
    title: 'Quote request', q: ['Service', 'Level / institution', 'Subject or department', 'Length', 'Deadline', 'Language', 'Referencing style'],
    words: 'words', h: 'Your request has been sent', p1: 'Thank you! We will reply soon at ', p2: ' with a quote and a timeline.'
  };
  function getStamp() {
    if (asked) return; asked = 1;
    fetch(API + '?stamp=1', { mode: 'cors' }).then(function (r) { return r.json(); }).then(function (j) { stamp = j.stamp || ''; }).catch(function () {});
  }
  f.addEventListener('focusin', getStamp); f.addEventListener('pointerdown', getStamp);
  var E = f.elements, err = d.getElementById('qerr');
  function mark(el, msg) {
    var box = el.type === 'checkbox' ? el.closest('.qok') : el.closest('.qi');
    if (!box) return;
    box.classList.toggle('bad', !!msg);
    if (el.type === 'checkbox') return;
    var s = box.querySelector('.fe');
    if (msg) { if (!s) { s = d.createElement('small'); s.className = 'fe'; box.appendChild(s); } s.textContent = msg; }
    else if (s) s.remove();
  }
  function phone(v) {
    var p = v.replace(/[^\d+]/g, '');
    if (/^[29]\d{7}$/.test(p)) p = '+357' + p;          // Cyprus number written without the code
    return p;
  }
  function check() {
    var bad = null, nm = E.nm.value.trim(), em = E.em.value.trim(), ph = E.ph.value.trim();
    var r = [[E.nm, nm.length < 2 ? T.name : ''],
             [E.em, /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(em) ? '' : T.email],
             [E.ph, !ph || /^\+?\d{8,15}$/.test(phone(ph)) ? '' : T.phone],
             [E.ok, E.ok.checked ? '' : T.ok]];
    r.forEach(function (x) { mark(x[0], x[1]); if (x[1] && !bad) bad = x; });
    err.hidden = !bad || bad[0] !== E.ok; if (bad && bad[0] === E.ok) err.textContent = T.ok;
    if (bad) { bad[0].focus({ preventScroll: true }); bad[0].scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    return !bad;
  }
  ['nm', 'em', 'ph'].forEach(function (k) { E[k].addEventListener('input', function () { if (E[k].closest('.qi').classList.contains('bad')) mark(E[k], ''); }); });
  E.ok.addEventListener('change', function () { if (E.ok.checked) { mark(E.ok, ''); err.hidden = true; } });
  function val(n) { var x = f.querySelector('input[name=' + n + ']:checked'); return x ? x.value : ''; }
  function answers() {
    var dl = E.dl.value ? new Date(E.dl.value + 'T12:00').toLocaleDateString(EL ? 'el-GR' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
    var v = [val('qt'), E.lv.value, E.fd.value.trim(), '≈ ' + (+E.ln.value).toLocaleString(EL ? 'el-GR' : 'en-GB') + ' ' + T.words, dl, val('ql'), E.st.value];
    return v.map(function (a, i) { return { q: T.q[i], a: a }; }).filter(function (x) { return x.a; });
  }
  function fallback() {
    var body = (d.getElementById('ltb').textContent || '') + '\n\n' + E.nm.value.trim() + '\n' + E.em.value.trim() + (E.ph.value.trim() ? '\n' + E.ph.value.trim() : '');
    location.href = 'mailto:' + lt.dataset.to + '?subject=' + encodeURIComponent(T.title + ' — ' + val('qt')) + '&body=' + encodeURIComponent(body);
  }
  function done() {
    var box = d.createElement('div'); box.className = 'lt-done'; box.setAttribute('role', 'status');
    box.innerHTML = '<svg viewBox="0 0 60 60" aria-hidden="true"><path pathLength="1" d="M30 4a26 26 0 1 1-.1 0"/><path pathLength="1" d="M18 31l8 8 16-17"/></svg><h3></h3><p></p>';
    box.querySelector('h3').textContent = T.h;
    var p = box.querySelector('p'), s = d.createElement('strong'); s.textContent = E.em.value.trim();
    p.append(T.p1, s, T.p2);
    lt.appendChild(box); lt.offsetWidth; lt.classList.add('sent');
    var q = f.closest('.qt'); if (q) q.classList.add('sent');
    Array.prototype.forEach.call(E, function (x) { x.disabled = true; });
    lt.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  f.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (busy || !check()) return;
    if (E._gotcha && E._gotcha.value) { done(); return; }
    busy = 1; var label = b.innerHTML; b.disabled = true; b.textContent = T.sending; err.hidden = true;
    var data = {
      site: 'zenwrite', kind: 'form', lang: EL ? 'el' : 'en', page: location.href, stamp: stamp, _gotcha: E._gotcha ? E._gotcha.value : '',
      title: T.title + (val('qt') ? ' — ' + val('qt') : ''), name: E.nm.value.trim(), email: E.em.value.trim(),
      phone: E.ph.value.trim() ? phone(E.ph.value.trim()) : '', message: E.nt.value.trim(), answers: answers()
    };
    var go = function () {
      fetch(API, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); })
        .then(function (x) {
          busy = 0; b.disabled = false; b.innerHTML = label;
          if (x.j && x.j.ok) return done();
          var e = (x.j && x.j.error) || '';
          if (e === 'invalid_name') return mark(E.nm, T.name);
          if (e === 'invalid_email') return mark(E.em, T.email);
          if (e === 'invalid_phone') return mark(E.ph, T.phone);
          throw new Error(e || 'http ' + x.s);
        })
        .catch(function () { busy = 0; b.disabled = false; b.innerHTML = label; err.textContent = T.fail; err.hidden = false; setTimeout(fallback, 1400); });
    };
    if (stamp) go();
    else { asked = 0; getStamp(); setTimeout(function () { data.stamp = stamp; go(); }, 1200); }
  });
})();
