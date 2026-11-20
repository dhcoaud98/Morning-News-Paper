/* 아침 브리핑 — 정적 웹앱
 * 데이터: issues/index.json (발행 목록) + issues/YYYY/MM/YYYY-MM-DD.json (각 호)
 * 화면: (기본) 메인 · #today 최신 호 · #issue-YYYY-MM-DD 특정 호
 */
(function () {
  'use strict';

  var SECTIONS = [
    { key: 'hr', no: '01', name: 'HR', short: 'HR', sub: '인사 · 조직 · 채용', repo: 'HR' },
    { key: 'ax', no: '02', name: 'AX · AI · 기업교육', short: 'AX', sub: 'AI 전환 · 기업교육', repo: 'AI-AX' },
    { key: 'econ', no: '03', name: '경제', short: '경제', sub: '경제 공부 · 시장', repo: 'economy' }
  ];
  var SEC = {};
  SECTIONS.forEach(function (s) { SEC[s.key] = s; });
  var WEEK = ['일', '월', '화', '수', '목', '금', '토'];

  var app = document.getElementById('app');
  var state = { index: null, cache: {}, month: null, query: '', sec: 'all' };

  /* ---------- 유틸 ---------- */
  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  // 마크다운 인라인(굵게·기울임·링크)만 안전하게 변환
  var LINK = /\[((?:[^\[\]]|\[[^\]]*\])+)\]\(([^\s)]+(?:\([^\s)]*\)[^\s)]*)*)\)/g;
  function md(s) {
    var out = esc(s);
    out = out.replace(LINK, function (_, t, u) {
      var url = u.replace(/&amp;/g, '&');
      if (!/^https?:\/\//i.test(url)) return t;
      return '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + t + '</a>';
    });
    out = out.replace(/\*\*([^*]+?)\*\*/g, '<b>$1</b>');
    out = out.replace(/(^|[^*])\*([^*\s][^*]*?)\*(?!\*)/g, '$1<i>$2</i>');
    return out;
  }
  function plain(s) { return String(s || '').replace(/\*\*/g, '').replace(LINK, '$1'); }
  function issuePath(d) { return 'issues/' + d.slice(0, 4) + '/' + d.slice(5, 7) + '/' + d + '.json'; }
  function pd(d) { var p = d.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2]); }
  function korDate(d) { var t = pd(d); return t.getFullYear() + '년 ' + (t.getMonth() + 1) + '월 ' + t.getDate() + '일 ' + WEEK[t.getDay()] + '요일'; }
  function shortDate(d) { var t = pd(d); return String(t.getMonth() + 1).padStart(2, '0') + '.' + String(t.getDate()).padStart(2, '0') + ' ' + WEEK[t.getDay()]; }
  function getJSON(p) {
    return fetch(p, { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(p + ' (' + r.status + ')');
      return r.json();
    });
  }
  function loadIndex() {
    if (state.index) return Promise.resolve(state.index);
    return getJSON('issues/index.json').then(function (j) {
      j.issues.sort(function (a, b) { return a.date < b.date ? 1 : -1; });
      state.index = j; return j;
    });
  }
  function loadIssue(d) {
    if (state.cache[d]) return Promise.resolve(state.cache[d]);
    return getJSON(issuePath(d)).then(function (j) { state.cache[d] = j; return j; });
  }
  function badges(keys) {
    return '<span class="badges">' + SECTIONS.map(function (s) {
      return keys.indexOf(s.key) !== -1 ? '<span class="sb">' + esc(s.short) + '</span>' : '';
    }).join('') + '</span>';
  }

  /* ---------- 공통 머리 ---------- */
  function masthead(small) {
    var idx = state.index;
    return '<header class="masthead' + (small ? ' small' : '') + '">' +
      '<div class="kicker">HR · AX · ECONOMY</div>' +
      '<h1><a href="#home">' + esc(idx.title || '아침 브리핑') + '</a></h1>' +
      '<p>' + esc(idx.tagline || '') + '</p></header><div class="double-rule"></div>';
  }
  function topbar(left, right) {
    return '<div class="topbar"><div class="left">' + left + '</div><div class="right">' + right + '</div></div>';
  }

  /* ---------- 신문 한 호 ---------- */
  function sources(list) {
    if (!list || !list.length) return '';
    return '<div class="srcs">출처 · ' + list.map(function (s) {
      return '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.title) + '</a>';
    }).join('<span class="dot"> · </span>') + '</div>';
  }
  function notes(list) {
    if (!list || !list.length) return '';
    return '<ul class="notes">' + list.map(function (n) {
      return '<li>' + (n.label ? '<b>' + esc(n.label) + '</b> ' : '') + md(n.text) + '</li>';
    }).join('') + '</ul>';
  }
  function meaning(m) {
    if (!m) return '';
    return '<div class="why"><b>' + esc(m.label === '나에게 의미' ? '→ 나에게 의미' : m.label) + '</b> ' + md(m.text) + '</div>';
  }
  function article(a, cls) {
    return '<article class="art ' + (cls || '') + '">' +
      '<h3>' + md(a.title) + '</h3>' +
      (a.when ? '<div class="when">' + esc(a.when) + '</div>' : '') +
      a.body.map(function (p) { return '<p>' + md(p) + '</p>'; }).join('') +
      meaning(a.meaning) + notes(a.notes) + sources(a.sources) + '</article>';
  }

  function pickLead(issue) {
    for (var i = 0; i < SECTIONS.length; i++) {
      var s = issue.sections[SECTIONS[i].key];
      if (s && s.categories.length && s.categories[0].articles.length) {
        return { sec: SECTIONS[i], cat: s.categories[0], art: s.categories[0].articles[0] };
      }
    }
    return null;
  }

  // 1면 톱 아래: 다른 섹션의 첫 기사 미리보기
  function more(issue, lead) {
    var items = SECTIONS.filter(function (s) { return s.key !== lead.sec.key && issue.sections[s.key]; }).map(function (s) {
      var x = issue.sections[s.key];
      var c = x.categories[0];
      if (!c || !c.articles.length) return '';
      var a = c.articles[0];
      var p = plain(a.body[0] || '');
      if (p.length > 120) p = p.slice(0, 118) + '…';
      return '<a class="mi" href="#issue-' + issue.date + '" data-jump="sec-' + s.key + '"><span class="label">' + esc(s.name) + ' · ' + esc(c.name) + '</span>' +
        '<span class="mt">' + esc(plain(a.title)) + '</span><span class="mp">' + esc(p) + '</span></a>';
    }).join('');
    return items ? '<div class="more-tops"><div class="side-h">다른 섹션 톱</div><div class="mis">' + items + '</div></div>' : '';
  }

  function ticker(issue) {
    var e = issue.sections.econ;
    if (!e || !e.numbers || !e.numbers.length) return '';
    return '<div class="ticker" aria-label="숫자 한눈에">' + e.numbers.map(function (n) {
      return '<div class="item" title="' + esc(n.basis) + '"><b>' + esc(n.name) + '</b><span class="mono">' + esc(n.value) + '</span></div>';
    }).join('') + '</div>';
  }

  function front(issue) {
    var keys = SECTIONS.filter(function (s) { return issue.sections[s.key]; });
    var lead = pickLead(issue);

    var nav = '<a href="#home">메인</a><a href="#issue-' + issue.date + '" class="on">1면</a>' +
      keys.map(function (s) { return '<a href="#issue-' + issue.date + '" data-jump="sec-' + s.key + '">' + esc(s.name) + '</a>'; }).join('');

    var leadHtml = '';
    if (lead) {
      var a = lead.art;
      leadHtml = '<article class="lead">' +
        '<div class="label">오늘의 톱 · ' + esc(lead.sec.name) + ' · ' + esc(lead.cat.name) + '</div>' +
        '<h2>' + md(a.title) + '</h2>' +
        (a.when ? '<p class="deck">' + esc(a.when) + '</p>' : '') +
        '<div class="body-cols">' + a.body.map(function (p) { return '<p>' + md(p) + '</p>'; }).join('') + '</div>' +
        meaning(a.meaning) + notes(a.notes) + sources(a.sources) + more(issue, lead) + '</article>';
    }

    var ones = keys.map(function (s) {
      var x = issue.sections[s.key];
      return x.oneLine ? '<li><b>' + esc(s.short) + '</b> — ' + md(x.oneLine) + '</li>' : '';
    }).join('');
    var econ = issue.sections.econ;
    var nums = econ && econ.numbers && econ.numbers.length
      ? '<div><div class="side-h">숫자 한눈에</div><table class="nums">' + econ.numbers.map(function (n) {
        return '<tr><th scope="row">' + esc(n.name) + '</th><td class="mono">' + esc(n.value) + '</td></tr><tr class="basis"><td colspan="2">' + md(n.basis) + '</td></tr>';
      }).join('') + '</table>' + (econ.nextCheck ? '<p class="next"><b>다음 주 체크</b> ' + md(econ.nextCheck) + '</p>' : '') + '</div>'
      : '';
    var picks = [];
    keys.forEach(function (s) { (issue.sections[s.key].picks || []).forEach(function (p) { picks.push({ s: s, p: p }); }); });
    var picksHtml = picks.length ? '<div class="must"><div class="side-h">이번 주 볼 만한 것</div>' + picks.map(function (x) {
      var t = '<span class="sb">' + esc(x.s.short) + '</span> ' + esc(plain(x.p.title));
      return x.p.url ? '<a href="' + esc(x.p.url) + '" target="_blank" rel="noopener">' + t + '</a>' : '<div class="pk">' + t + '</div>';
    }).join('') + '</div>' : '';

    var side = '<aside class="side">' +
      (ones ? '<div class="box"><h3>오늘의 한 줄</h3><ol>' + ones + '</ol></div>' : '') +
      nums + picksHtml + '</aside>';

    var secs = keys.map(function (s) { return sectionBlock(issue, s, lead); }).join('');

    var list = state.index.issues;
    var i = list.findIndex(function (x) { return x.date === issue.date; });
    var older = list[i + 1], newer = list[i - 1];
    var foot = '<footer class="foot"><span>각 섹션은 HR · AI-AX · economy 레포의 일일 브리핑(Claude 자동 작성)을 모은 것입니다. 중요한 내용은 출처 원문에서 확인하세요.</span><span class="pn">' +
      (older ? '<a href="#issue-' + older.date + '">← ' + esc(shortDate(older.date)) + '</a>' : '') +
      '<a href="#home">전체 신문</a>' +
      (newer ? '<a href="#issue-' + newer.date + '">' + esc(shortDate(newer.date)) + ' →</a>' : '') +
      '</span></footer>';

    return topbar(
      '<span>' + esc(korDate(issue.date)) + '</span><span>제 ' + esc(issue.issueNo) + '호</span>' + badges(keys.map(function (s) { return s.key; })),
      (older ? '<a href="#issue-' + older.date + '">← 이전 호</a>' : '') + (newer ? '<a href="#issue-' + newer.date + '">다음 호 →</a>' : '') + '<a href="#home">전체 신문 보기</a>'
    ) + masthead(true) +
      '<nav class="nav" aria-label="섹션">' + nav + '</nav>' + ticker(issue) +
      '<section class="front">' + leadHtml + side + '</section>' + secs + foot;
  }

  function sectionBlock(issue, s, lead) {
    var x = issue.sections[s.key];
    var h = '<section class="secblock" id="sec-' + s.key + '">' +
      '<div class="sec-h"><span class="no">' + s.no + '</span><span class="name">' + esc(s.name) + '</span>' +
      '<span class="sub">' + esc(s.sub) + '</span>' +
      (x.sourceUrl ? '<a class="orig" href="' + esc(x.sourceUrl) + '" target="_blank" rel="noopener">원본 브리핑 ↗</a>' : '') + '</div>' +
      (x.oneLine ? '<p class="standfirst">' + md(x.oneLine) + '</p>' : '');

    if (x.terms && x.terms.length) {
      h += '<div class="cat"><div class="cat-h">오늘의 용어</div><div class="terms">' + x.terms.map(function (t) {
        return '<div class="term"><h3>' + esc(t.name) + '</h3><dl>' + t.items.map(function (it) {
          return '<dt>' + esc(it.label) + '</dt><dd>' + md(it.text) + '</dd>';
        }).join('') + '</dl></div>';
      }).join('') + '</div></div>';
    }

    x.categories.forEach(function (c) {
      var arts = c.articles.filter(function (a) { return !(lead && lead.art === a); });
      var movedLead = arts.length < c.articles.length;
      if (!arts.length && !movedLead) return;
      h += '<div class="cat"><div class="cat-h">' + esc(c.name) +
        (movedLead ? '<a class="tolead" href="#issue-' + issue.date + '" data-jump="top">톱기사는 1면에 ↑</a>' : '') + '</div>' +
        '<div class="arts">' + arts.map(function (a) { return article(a); }).join('') + '</div></div>';
    });

    if (x.question) {
      h += '<div class="cat"><div class="cat-h">오늘 생각해볼 질문</div><div class="quiz"><p class="q">' + md(x.question.q) + '</p>' +
        (x.question.a && x.question.a.length ? '<details><summary>정답 보기</summary>' + x.question.a.map(function (p) { return '<p>' + md(p) + '</p>'; }).join('') + '</details>' : '') +
        '</div></div>';
    }
    if (s.key === 'econ' && x.picks && x.picks.length) {
      h += '<div class="cat"><div class="cat-h">오늘의 읽을거리</div><ul class="reads">' + x.picks.map(function (p) { return '<li>' + md(p.text) + '</li>'; }).join('') + '</ul></div>';
    }
    return h + '</section>';
  }

  /* ---------- 메인 ---------- */
  function matches(e) {
    var q = state.query.trim().toLowerCase(), sec = state.sec;
    if (sec !== 'all' && e.sections.indexOf(sec) === -1) return { ok: false, hits: [] };
    if (!q) return { ok: true, hits: [] };
    var pool = [];
    (sec === 'all' ? e.sections : [sec]).forEach(function (k) {
      pool = pool.concat((e.titles[k] || []).map(plain));
      if (e.oneLines[k]) pool.push(plain(e.oneLines[k]));
    });
    var hits = pool.filter(function (t) { return t.toLowerCase().indexOf(q) !== -1; });
    return { ok: hits.length > 0, hits: hits };
  }

  function home() {
    var list = state.index.issues, latest = list[0];
    var byDate = {};
    list.forEach(function (e) { byDate[e.date] = e; });
    if (!state.month) state.month = latest.date.slice(0, 7);
    var months = Array.from(new Set(list.map(function (e) { return e.date.slice(0, 7); }))).sort();
    var mi = months.indexOf(state.month), prevM = months[mi - 1], nextM = months[mi + 1];
    var y = +state.month.slice(0, 4), mo = +state.month.slice(5, 7);

    var hero = '<section class="hero">' +
      '<div class="hero-date"><div class="muted">최신호 · 제 ' + esc(latest.issueNo) + '호</div>' +
      '<div class="big">' + (pd(latest.date).getMonth() + 1) + '.' + pd(latest.date).getDate() + '</div>' +
      '<div class="serif">' + esc(korDate(latest.date)) + '</div>' + badges(latest.sections) +
      '<a class="cta" href="#issue-' + latest.date + '">오늘 신문 펼치기 →</a></div>' +
      '<div class="hero-body"><div class="label">오늘의 톱</div><h2><a href="#issue-' + latest.date + '">' + md(latest.lead) + '</a></h2>' +
      '<ul class="ones">' + SECTIONS.filter(function (s) { return latest.oneLines[s.key]; }).map(function (s) {
        return '<li><span class="sb">' + esc(s.short) + '</span><span>' + md(latest.oneLines[s.key]) + '</span></li>';
      }).join('') + '</ul></div></section>';

    var first = new Date(y, mo - 1, 1).getDay(), days = new Date(y, mo, 0).getDate();
    var cells = WEEK.map(function (w) { return '<div class="wd">' + w + '</div>'; }).join('');
    for (var b = 0; b < first; b++) cells += '<div class="cell"></div>';
    for (var d = 1; d <= days; d++) {
      var key = y + '-' + String(mo).padStart(2, '0') + '-' + String(d).padStart(2, '0');
      var e = byDate[key];
      if (e) {
        var m = matches(e);
        cells += '<div class="cell"><a class="card' + (key === latest.date ? ' today' : '') + (m.ok ? '' : ' dim') + '" href="#issue-' + key + '">' +
          '<div class="top"><span class="d">' + d + '</span><span class="tag">' + (key === latest.date ? '최신' : '제' + e.issueNo + '호') + '</span></div>' +
          '<div class="hl">' + esc(plain(e.lead)) + '</div>' + badges(e.sections) + '</a></div>';
      } else {
        cells += '<div class="cell empty"><span class="d">' + d + '</span></div>';
      }
    }
    var tail = (7 - ((first + days) % 7)) % 7;
    for (var t = 0; t < tail; t++) cells += '<div class="cell"></div>';

    var rows = list.map(function (e) {
      var m = matches(e);
      if (!m.ok) return '';
      return '<a class="row" href="#issue-' + e.date + '"><span class="dt">' + esc(shortDate(e.date)) + '<small>제' + e.issueNo + '호</small></span>' +
        '<span class="rt"><span class="tt">' + esc(plain(e.lead)) + '</span>' +
        (m.hits.length ? '<span class="hit">' + m.hits.slice(0, 3).map(esc).join(' · ') + '</span>' : '') + '</span>' + badges(e.sections) + '</a>';
    }).join('');

    var pills = [{ key: 'all', name: '전체' }].concat(SECTIONS).map(function (s) {
      return '<button type="button" class="pill' + (state.sec === s.key ? ' on' : '') + '" data-sec="' + s.key + '" aria-pressed="' + (state.sec === s.key) + '">' + esc(s.key === 'ax' ? 'AX · 교육' : s.name) + '</button>';
    }).join('');

    return topbar('<span>' + esc(korDate(latest.date)) + '</span><span>지금까지 ' + list.length + '개 호 발행</span>',
      '<span class="muted">마지막 갱신 ' + esc(state.index.updated || '') + '</span>') +
      masthead(false) + hero +
      '<div class="arch-head"><div><div class="muted" style="font-size:13px;margin-bottom:6px">' + y + '년</div><div class="month">' +
      '<button type="button" class="icon-btn" aria-label="이전 달" data-month="' + (prevM || '') + '"' + (prevM ? '' : ' disabled') + '>' + chev('l') + '</button>' +
      '<h2>' + mo + '월</h2>' +
      '<button type="button" class="icon-btn" aria-label="다음 달" data-month="' + (nextM || '') + '"' + (nextM ? '' : ' disabled') + '>' + chev('r') + '</button>' +
      '</div></div><div class="filters"><label for="q">기사 검색</label>' +
      '<input id="q" type="search" placeholder="예: 정년, 에이전트, 환율" value="' + esc(state.query) + '">' + pills + '</div></div>' +
      '<div class="cal">' + cells + '</div>' +
      '<div class="recent"><h3>' + (state.query || state.sec !== 'all' ? '검색 결과' : '지난 신문 전체') + '</h3>' +
      (rows || '<div class="empty-msg">조건에 맞는 신문이 없습니다.</div>') + '</div>' +
      '<footer class="foot"><span>HR · AI-AX · economy 레포의 브리핑을 매일 아침 한 장으로 엮습니다. 그날 없는 분야는 빼고 발행합니다.</span><a href="#today">최신호 →</a></footer>';
  }
  function chev(dir) {
    return '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="' + (dir === 'l' ? 'M10 3L5 8l5 5' : 'M6 3l5 5-5 5') + '"/></svg>';
  }

  /* ---------- 라우팅 ---------- */
  function render(html) { app.innerHTML = '<div class="wrap">' + html + '</div>'; }

  function route() {
    var h = (location.hash || '').replace(/^#/, '');
    loadIndex().then(function (idx) {
      if (!idx.issues.length) { render('<div class="loading">아직 발행된 신문이 없습니다.</div>'); return; }
      var m = /^issue-(\d{4}-\d{2}-\d{2})$/.exec(h);
      if (h === 'today' || m) {
        var date = m ? m[1] : idx.issues[0].date;
        return loadIssue(date).then(function (issue) {
          render(front(issue));
          document.title = (idx.title || '아침 브리핑') + ' — ' + korDate(issue.date);
          window.scrollTo(0, 0);
        });
      }
      render(home()); bindHome();
      document.title = idx.title || '아침 브리핑';
      window.scrollTo(0, 0);
    }).catch(function (err) {
      render('<div class="error">신문을 불러오지 못했습니다.<br><span class="mono" style="font-size:13px">' + esc(err.message) + '</span></div>');
    });
  }

  function rerenderHome(keepFocus) {
    var pos = keepFocus ? document.getElementById('q').selectionStart : 0;
    var y = window.scrollY;
    render(home()); bindHome();
    window.scrollTo(0, y);
    if (keepFocus) { var q = document.getElementById('q'); q.focus(); q.setSelectionRange(pos, pos); }
  }
  function bindHome() {
    var q = document.getElementById('q');
    if (q) q.addEventListener('input', function () { state.query = q.value; rerenderHome(true); });
    app.querySelectorAll('[data-sec]').forEach(function (b) {
      b.addEventListener('click', function () { state.sec = b.getAttribute('data-sec'); rerenderHome(false); });
    });
    app.querySelectorAll('[data-month]').forEach(function (b) {
      b.addEventListener('click', function () { var v = b.getAttribute('data-month'); if (v) { state.month = v; rerenderHome(false); } });
    });
  }

  // 섹션 바로가기: 해시를 바꾸지 않고 스크롤
  app.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-jump]');
    if (!a) return;
    e.preventDefault();
    var id = a.getAttribute('data-jump');
    if (id === 'top') { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  window.addEventListener('hashchange', route);
  route();
})();
