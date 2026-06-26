/* studiwize — landing interactions (vanilla) */
(function () {
  'use strict';

  /* ── inject app-mark SVG (play + page spine) ──────────── */
  var MARK_SVG = '<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" aria-hidden="true">' +
    '<rect class="mk-spine" x="29" y="24" width="6.5" height="52" rx="3.2"/>' +
    '<polygon class="mk-play" points="47,32 73,50 47,68"/></svg>';
  document.querySelectorAll('.mark').forEach(function (m) {
    if (!m.querySelector('svg')) m.innerHTML = MARK_SVG;
  });

  /* ── nav shadow on scroll ─────────────────────────────── */
  var nav = document.querySelector('.nav');
  var onScroll = function () {
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 8);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── scroll reveal (respects prefers-reduced-motion) ─── */
  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    // skip IntersectionObserver; show everything immediately
    document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
  }

  /* ── audio player demo ────────────────────────────────── */
  var CHAPTERS = [
    { n: '01', name: 'Markets & Trade-offs', len: 38 },
    { n: '02', name: 'Supply & Demand', len: 44 },
    { n: '03', name: 'Elasticity & Its Application', len: 41 },
    { n: '04', name: 'Consumer Choice', len: 52 },
    { n: '05', name: 'Firms & Production', len: 47 },
    { n: '06', name: 'The Costs of Production', len: 49 },
    { n: '07', name: 'Competitive Markets', len: 55 },
    { n: '08', name: 'Monopoly & Market Power', len: 43 },
    { n: '09', name: 'Externalities', len: 39 },
    { n: '10', name: 'Public Goods & Commons', len: 36 }
  ];
  var SPEEDS = [1, 1.25, 1.5, 1.75, 2];

  var state = { idx: 6, t: 726, playing: false, speed: 1 };
  try {
    var saved = JSON.parse(localStorage.getItem('studiwize_player') || 'null');
    if (saved && typeof saved.idx === 'number') {
      state.idx = Math.min(CHAPTERS.length - 1, Math.max(0, saved.idx));
      state.t = Math.max(0, saved.t || 0);
      state.speed = SPEEDS.indexOf(saved.speed) >= 0 ? saved.speed : 1;
    }
  } catch (e) {}

  var $ = function (s) { return document.querySelector(s); };
  var elFill = $('#plFill'), elCur = $('#plCur'), elRem = $('#plRem'),
      elCh = $('#plCh'), elTitle = $('#plTitle'), elPlay = $('#plPlay'),
      elScreen = $('#plScreen'), elSpeed = $('#plSpeed'), elSheet = $('#plSheet'),
      elChList = $('#chList'), elBar = $('#plBar'), elSheetToggle = $('#plSheetToggle');

  var dur = function () { return CHAPTERS[state.idx].len * 60; };
  var fmt = function (s) {
    s = Math.max(0, Math.floor(s));
    var m = Math.floor(s / 60), ss = s % 60;
    return m + ':' + (ss < 10 ? '0' : '') + ss;
  };

  function persist() {
    try {
      localStorage.setItem('studiwize_player', JSON.stringify({ idx: state.idx, t: state.t, speed: state.speed }));
    } catch (e) {}
  }

  function renderMeta() {
    var c = CHAPTERS[state.idx];
    if (elCh) elCh.textContent = 'Chapter ' + c.n;
    if (elTitle) elTitle.textContent = c.name;
    if (elSpeed) elSpeed.textContent = state.speed + '×';
    document.querySelectorAll('.ch-row').forEach(function (r, i) {
      r.classList.toggle('active', i === state.idx);
      r.setAttribute('aria-selected', i === state.idx ? 'true' : 'false');
    });
  }
  function renderTime() {
    var d = dur();
    if (state.t > d) state.t = d;
    var pct = (state.t / d) * 100;
    if (elFill) elFill.style.width = pct.toFixed(2) + '%';
    if (elBar) elBar.setAttribute('aria-valuenow', Math.round(pct));
    if (elCur) elCur.textContent = fmt(state.t);
    if (elRem) elRem.textContent = '-' + fmt(d - state.t);
  }

  var timer = null;
  function setPlaying(p) {
    state.playing = p;
    if (elScreen) elScreen.classList.toggle('playing', p);
    if (elPlay) elPlay.innerHTML = p ? ICON.pause : ICON.play;
    if (elPlay) elPlay.setAttribute('aria-label', p ? 'Pause' : 'Play');
    if (timer) { clearInterval(timer); timer = null; }
    if (p) {
      timer = setInterval(function () {
        state.t += 0.5 * state.speed;
        if (state.t >= dur()) {
          if (state.idx < CHAPTERS.length - 1) { state.idx++; state.t = 0; renderMeta(); }
          else { state.t = dur(); setPlaying(false); }
        }
        renderTime();
        if (Math.floor(state.t) % 3 === 0) persist();
      }, 500);
    }
    persist();
  }

  function selectChapter(i) {
    state.idx = i; state.t = 0;
    renderMeta(); renderTime(); persist();
    if (!state.playing) setPlaying(true);
  }

  var ICON = {
    play: '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.2v13.6c0 .9 1 1.5 1.8 1L20 12.9c.7-.45.7-1.5 0-1.95L9.8 4.2C9 3.7 8 4.3 8 5.2Z"/></svg>',
    pause: '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.3"/><rect x="13.5" y="5" width="4" height="14" rx="1.3"/></svg>'
  };

  // build chapter list
  if (elChList) {
    elChList.innerHTML = CHAPTERS.map(function (c, i) {
      return '<div class="ch-row" role="option" aria-selected="false" tabindex="0" data-i="' + i + '">' +
        '<span class="ch-num">' + c.n + '</span>' +
        '<span class="ch-name">' + c.name + '</span>' +
        '<span class="ch-len">' + c.len + 'm</span></div>';
    }).join('');
    elChList.querySelectorAll('.ch-row').forEach(function (r) {
      r.addEventListener('click', function () { selectChapter(+r.dataset.i); });
      r.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectChapter(+r.dataset.i); }
      });
    });
  }

  if (elPlay) elPlay.addEventListener('click', function () { setPlaying(!state.playing); });

  var back = $('#plBack'), fwd = $('#plFwd');
  if (back) back.addEventListener('click', function () { state.t = Math.max(0, state.t - 15); renderTime(); persist(); });
  if (fwd) fwd.addEventListener('click', function () { state.t = Math.min(dur(), state.t + 30); renderTime(); persist(); });

  if (elSpeed) elSpeed.addEventListener('click', function () {
    var i = SPEEDS.indexOf(state.speed);
    state.speed = SPEEDS[(i + 1) % SPEEDS.length];
    renderMeta(); persist();
  });

  if (elBar) elBar.addEventListener('click', function (e) {
    var r = elBar.getBoundingClientRect();
    state.t = Math.min(dur(), Math.max(0, ((e.clientX - r.left) / r.width) * dur()));
    renderTime(); persist();
  });

  // chapter sheet open/close — toggle `hidden` attr for a11y
  function openSheet() {
    if (elSheet) { elSheet.removeAttribute('hidden'); elSheet.classList.add('open'); }
    if (elSheetToggle) elSheetToggle.setAttribute('aria-expanded', 'true');
  }
  function closeSheet() {
    if (elSheet) { elSheet.setAttribute('hidden', ''); elSheet.classList.remove('open'); }
    if (elSheetToggle) elSheetToggle.setAttribute('aria-expanded', 'false');
  }

  if (elSheetToggle) elSheetToggle.addEventListener('click', openSheet);
  var sheetClose = $('#plSheetClose');
  if (sheetClose) sheetClose.addEventListener('click', closeSheet);

  renderMeta(); renderTime();
  if (elPlay) elPlay.innerHTML = ICON.play;

  /* ── how it works stepper ─────────────────────────────── */
  var steps = Array.prototype.slice.call(document.querySelectorAll('.step'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.how-panel'));
  var hi = 0, hTimer = null, procRAF = null;
  var DWELL = prefersReduced ? 99999 : 3600; // pause auto-advance if motion reduced

  function showStep(i, manual) {
    hi = i;
    steps.forEach(function (s, k) {
      s.classList.toggle('on', k === i);
      s.setAttribute('aria-selected', k === i ? 'true' : 'false');
      s.setAttribute('tabindex', k === i ? '0' : '-1');
      var p = s.querySelector('.step-prog');
      if (p) { p.style.transition = 'none'; p.style.width = '0%'; }
    });
    panels.forEach(function (p, k) {
      p.classList.toggle('show', k === i);
      if (k === i) { p.removeAttribute('hidden'); } else { p.setAttribute('hidden', ''); }
    });
    // animate current step progress bar
    var prog = steps[i] && steps[i].querySelector('.step-prog');
    if (prog && !prefersReduced) {
      requestAnimationFrame(function () {
        prog.style.transition = 'width ' + DWELL + 'ms linear';
        prog.style.width = '100%';
      });
    }
    // panel-specific anim
    runPanel(i);
    if (manual) restartTimer();
  }

  function runPanel(i) {
    if (i === 0) {
      var drop = document.querySelector('#howDrop'), chip = document.querySelector('#howChip');
      if (drop && chip) {
        drop.style.display = ''; chip.style.display = 'none';
        drop.classList.remove('hot');
        if (!prefersReduced) {
          setTimeout(function () { if (hi === 0) drop.classList.add('hot'); }, 900);
          setTimeout(function () { if (hi === 0) { drop.style.display = 'none'; chip.style.display = 'flex'; } }, 1700);
        } else {
          chip.style.display = 'flex'; drop.style.display = 'none';
        }
      }
    } else if (i === 1) {
      var bar = document.querySelector('#howProc');
      if (bar) {
        bar.style.width = '0%';
        if (!prefersReduced) {
          var start = performance.now();
          cancelAnimationFrame(procRAF);
          var tick = function (now) {
            if (hi !== 1) return;
            var p = Math.min(1, (now - start) / (DWELL - 400));
            bar.style.width = (p * 100).toFixed(1) + '%';
            if (p < 1) procRAF = requestAnimationFrame(tick);
          };
          procRAF = requestAnimationFrame(tick);
        } else {
          bar.style.width = '70%';
        }
      }
    }
  }

  function restartTimer() {
    if (prefersReduced) return;
    if (hTimer) clearInterval(hTimer);
    hTimer = setInterval(function () { showStep((hi + 1) % steps.length, false); }, DWELL);
  }

  steps.forEach(function (s, k) {
    s.addEventListener('click', function () { showStep(k, true); });
    s.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showStep(k, true); }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); showStep((k + 1) % steps.length, true); }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); showStep((k - 1 + steps.length) % steps.length, true); }
    });
  });

  // start stepper when in view
  var howSection = document.querySelector('#how');
  if (howSection && steps.length) {
    var startedHow = false;
    var howIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && !startedHow) {
          startedHow = true; showStep(0, false); restartTimer();
        } else if (!e.isIntersecting && startedHow) {
          if (hTimer) { clearInterval(hTimer); hTimer = null; }
        } else if (e.isIntersecting && startedHow && !hTimer) {
          restartTimer();
        }
      });
    }, { threshold: 0.3 });
    howIO.observe(howSection);
  }

  /* ── waitlist form — Formspree AJAX ──────────────────── */
  var form = document.querySelector('#waitForm'),
      input = document.querySelector('#waitEmail'),
      note = document.querySelector('#waitNote'),
      success = document.querySelector('#waitSuccess'),
      successEmail = document.querySelector('#wsEmail');

  function isEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }

  function showSuccess(email) {
    if (successEmail) successEmail.textContent = email;
    if (form) form.style.display = 'none';
    if (note) note.style.display = 'none';
    if (success) success.classList.add('show');
  }

  function showFormError(msg) {
    if (note) {
      note.textContent = msg;
      note.classList.add('error');
    }
    if (input) { input.classList.add('err'); input.focus(); }
  }

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = (input ? input.value : '').trim();

      // client-side validation (keeps UX in our control; form action is the no-JS fallback)
      if (!v) { showFormError('Enter your email to join the list.'); return; }
      if (!isEmail(v)) { showFormError("That email doesn't look right — check it?"); return; }

      if (input) input.classList.remove('err');
      if (note) note.classList.remove('error');

      // disable button while submitting
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = 'Joining…'; }

      fetch(form.action, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: new FormData(form)
      })
        .then(function (r) {
          if (r.ok) {
            showSuccess(v);
          } else {
            return r.json().then(function (data) {
              var msg = (data && data.errors && data.errors[0] && data.errors[0].message) ||
                        'Something went wrong — please try again.';
              throw new Error(msg);
            });
          }
        })
        .catch(function (err) {
          if (btn) { btn.disabled = false; btn.textContent = 'Join the waitlist'; }
          showFormError(err.message || 'Something went wrong — please try again.');
        });
    });

    if (input) {
      input.addEventListener('input', function () {
        if (input.classList.contains('err')) {
          input.classList.remove('err');
          if (note) { note.classList.remove('error'); note.textContent = note.dataset.default || ''; }
        }
      });
    }
  }

  /* ── smooth anchor offset for sticky nav ──────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id.length < 2) return;
      var t = document.querySelector(id);
      if (!t) return;
      e.preventDefault();
      var y = t.getBoundingClientRect().top + window.scrollY - 76;
      window.scrollTo({ top: y, behavior: prefersReduced ? 'auto' : 'smooth' });
    });
  });
})();
