/**
 * Company Reports Dashboard — Hermes dashboard plugin frontend.
 *
 * Registered as a React component via the Hermes plugin SDK's
 * window.__HERMES_PLUGINS__.register() so the dashboard can mount it.
 * Uses the SDK's React and hooks, then does DOM-based rendering inside
 * the component's container ref (avoids a full JSX/build-step refactor).
 */
(function () {
  'use strict';

  var React = window.__HERMES_PLUGIN_SDK__.React;
  var hooks = window.__HERMES_PLUGIN_SDK__.hooks;

  var BASE = '/api/plugins/derez-company';

  // ── Styles ────────────────────────────────────────────
  var STYLE_TEXT =
    '.company-dash{font-family:var(--hermes-font-family,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif);color:var(--hermes-text-primary,#1a1a2e);background:var(--hermes-bg-primary,#fff);height:100%;display:flex;flex-direction:column;overflow:hidden}' +
    '.company-dash__toolbar{display:flex;align-items:center;gap:.5rem;padding:.5rem 1rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}' +
    '.company-dash__search{flex:1;padding:.4rem .6rem;border:1px solid var(--hermes-border,#ccc);border-radius:6px;font-size:.875rem;background:var(--hermes-bg-secondary,#f5f5f5);color:inherit}' +
    '.company-dash__search:focus{outline:none;border-color:var(--hermes-accent,#4f46e5)}' +
    '.company-dash__refresh{padding:.4rem .75rem;border:1px solid var(--hermes-border,#ccc);border-radius:6px;background:var(--hermes-bg-secondary,#f5f5f5);cursor:pointer;font-size:.875rem;color:inherit}' +
    '.company-dash__refresh:disabled{opacity:.5}' +
    '.company-dash__tabs{display:flex;border-bottom:1px solid var(--hermes-border,#e0e0e0);padding:0 1rem;overflow-x:auto}' +
    '.company-dash__tab{padding:.5rem 1rem;cursor:pointer;font-size:.875rem;border-bottom:2px solid transparent;color:var(--hermes-text-secondary,#666);white-space:nowrap;transition:color .15s,border-color .15s}' +
    '.company-dash__tab:hover{color:var(--hermes-text-primary,#1a1a2e)}' +
    '.company-dash__tab--active{color:var(--hermes-accent,#4f46e5);border-bottom-color:var(--hermes-accent,#4f46e5);font-weight:600}' +
    '.company-dash__body{flex:1;display:flex;overflow:hidden}' +
    '.company-dash__toc{width:200px;flex-shrink:0;padding:1rem;border-right:1px solid var(--hermes-border,#e0e0e0);overflow-y:auto;display:none;font-size:.8125rem}' +
    '@media(min-width:1024px){.company-dash__toc{display:block}}' +
    '.company-dash__toc-title{font-size:.6875rem;text-transform:uppercase;letter-spacing:.05em;color:var(--hermes-text-secondary,#666);margin:0 0 .5rem 0}' +
    '.company-dash__toc-item{display:block;padding:.2rem 0;padding-left:.5rem;border-left:2px solid transparent;color:var(--hermes-text-secondary,#666);text-decoration:none;cursor:pointer;transition:color .15s,border-color .15s}' +
    '.company-dash__toc-item:hover{color:var(--hermes-text-primary,#1a1a2e);border-left-color:var(--hermes-accent,#4f46e5)}' +
    '.company-dash__toc-item--h3{padding-left:1.25rem}' +
    '.company-dash__toc-item--h4{padding-left:2rem}' +
    '.company-dash__content{flex:1;padding:1.5rem;overflow-y:auto}' +
    '.company-dash__metrics{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem}' +
    '.company-dash__metric-card{flex:1;min-width:160px;padding:1rem;border:1px solid var(--hermes-border,#e0e0e0);border-radius:8px;background:var(--hermes-bg-secondary,#f9fafb)}' +
    '.company-dash__metric-label{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--hermes-text-secondary,#666)}' +
    '.company-dash__metric-value{font-size:1.5rem;font-weight:700;margin-top:.25rem}' +
    '.company-dash__section-heading{margin:1.5rem 0 .75rem 0;font-weight:600}' +
    '.company-dash__section-heading--h2{font-size:1.25rem}' +
    '.company-dash__section-heading--h3{font-size:1.1rem}' +
    '.company-dash__badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.75rem;font-weight:600;text-transform:uppercase;margin:.1rem}' +
    '.company-dash__badge--green{background:#dcfce7;color:#166534}' +
    '.company-dash__badge--red{background:#fee2e2;color:#991b1b}' +
    '.company-dash__badge--yellow{background:#fef3c7;color:#92400e}' +
    '.company-dash__badge--blue{background:#e0e7ff;color:#3730a3}' +
    '.company-dash__callout{padding:.75rem 1rem;border-radius:6px;margin:.75rem 0;border-left:4px solid;font-size:.875rem}' +
    '.company-dash__callout--note{background:#f0f9ff;border-left-color:#0ea5e9}' +
    '.company-dash__callout--warning,.company-dash__callout--caution{background:#fffbeb;border-left-color:#f59e0b}' +
    '.company-dash__callout--important,.company-dash__callout--danger{background:#fef2f2;border-left-color:#ef4444}' +
    '.company-dash__callout--todo,.company-dash__callout--info,.company-dash__callout--tip{background:#f0fdf4;border-left-color:#22c55e}' +
    '.company-dash__table{width:100%;border-collapse:collapse;margin:.75rem 0;font-size:.875rem}' +
    '.company-dash__table th{text-align:left;padding:.5rem .75rem;border-bottom:2px solid var(--hermes-border,#e0e0e0);font-weight:600}' +
    '.company-dash__table td{padding:.4rem .75rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}' +
    '.company-dash__empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666);text-align:center}' +
    '.company-dash__empty-icon{font-size:3rem;margin-bottom:1rem;opacity:.4}' +
    '.company-dash__loading{display:flex;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666)}' +
    '.company-dash__error{padding:1.5rem;margin:1rem;border:1px solid #fca5a5;border-radius:8px;background:#fef2f2;color:#991b1b}' +
    '.company-dash__spinner{width:24px;height:24px;border:3px solid var(--hermes-border,#e0e0e0);border-top-color:var(--hermes-accent,#4f46e5);border-radius:50%;animation:spin .6s linear infinite;margin-right:.75rem}' +
    '@keyframes spin{to{transform:rotate(360deg)}}' +
    '.company-dash__text p{margin:.5rem 0;line-height:1.6}' +
    '.company-dash__list{margin:.5rem 0;padding-left:1.5rem}' +
    '.company-dash__list li{margin:.2rem 0}';

  // Inject styles once at module level
  (function () {
    var s = document.createElement('style');
    s.textContent = STYLE_TEXT;
    document.head.appendChild(s);
  })();

  // ── Helpers ──
  function escapeHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  }

  function badgeVariant(value) {
    var v = (value || '').toLowerCase().replace(/\s+/g, '-');
    var greens = ['active','warm','hot','won','success','complete','approved','done'];
    var reds   = ['blocked','delayed','failed','lost','critical','danger','cancelled','rejected','blacklisted'];
    var yellows = ['warning','pending','cold','on-hold','in-progress'];
    if (greens.indexOf(v) !== -1) return 'green';
    if (reds.indexOf(v) !== -1)   return 'red';
    if (yellows.indexOf(v) !== -1) return 'yellow';
    return 'blue';
  }

  // ── React Component ──────────────────────────────────
  function CompanyDashboard() {
    var rootRef = hooks.useRef(null);
    var tabsRef = hooks.useRef([]);
    var reportRef = hooks.useRef(null);
    var headingsRef = hooks.useRef([]);

    var loadingRef = hooks.useRef(true);
    var scanningRef = hooks.useRef(false);
    var errorRef = hooks.useRef(null);

    // Tick counter — bumped after every state change so the render effect fires
    var tickRef = hooks.useRef(0);
    var [tick, setTick] = hooks.useState(0);

    function bump() {
      tickRef.current++;
      setTick(tickRef.current);
    }

    // ── API ──
    function fetchTabs() {
      fetch(BASE + '/tabs')
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (list) {
          tabsRef.current = list;
          loadingRef.current = false;
          if (list.length > 0) {
            fetchReport(list[0].id);
          }
          bump();
        })
        .catch(function (err) {
          loadingRef.current = false;
          errorRef.current = err.message;
          bump();
        });
    }

    function fetchReport(tabId) {
      fetch(BASE + '/report/' + encodeURIComponent(tabId))
        .then(function (res) {
          if (!res.ok) return res.json().then(function (d) { throw new Error((d && d.detail) || 'HTTP ' + res.status); });
          return res.json();
        })
        .then(function (data) {
          reportRef.current = (data && data.content) || null;
          errorRef.current = null;
          fetchTOC(tabId);
          bump();
        })
        .catch(function (err) {
          errorRef.current = err.message;
          reportRef.current = null;
          bump();
        });
    }

    function fetchTOC(tabId) {
      fetch(BASE + '/toc/' + encodeURIComponent(tabId))
        .then(function (res) {
          if (res.ok) return res.json();
        })
        .then(function (data) {
          headingsRef.current = (data && data.headings) || [];
          bump();
        })
        .catch(function () {
          headingsRef.current = [];
          bump();
        });
    }

    function rescan() {
      scanningRef.current = true;
      bump();
      fetch(BASE + '/scan', { method: 'POST' })
        .then(function () { return fetchTabs(); })
        .catch(function () { /* ignore */ })
        .then(function () {
          scanningRef.current = false;
          bump();
        });
    }

    function switchTab(tabId) {
      reportRef.current = null;
      headingsRef.current = [];
      fetchReport(tabId);
    }

    // ── Render ──
    function render(el) {
      if (!el) return;
      el.innerHTML = '';

      if (loadingRef.current) {
        el.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading reports...</div>';
        return;
      }

      if (errorRef.current && tabsRef.current.length === 0) {
        el.innerHTML = '<div class="company-dash__error"><strong>Error:</strong> ' + escapeHtml(errorRef.current) + '</div>';
        return;
      }

      // Toolbar
      var toolbar = document.createElement('div');
      toolbar.className = 'company-dash__toolbar';
      toolbar.innerHTML = '<input class="company-dash__search" type="text" placeholder="Search reports..." id="derez-search" />' +
        '<button class="company-dash__refresh" id="derez-refresh">' + (scanningRef.current ? 'Scanning...' : '\u21bb Refresh') + '</button>';
      el.appendChild(toolbar);

      toolbar.querySelector('#derez-search').addEventListener('input', function (e) {
        var q = e.target.value.toLowerCase();
        if (!q) return;
        var match = tabsRef.current.filter(function (t) { return t.name.toLowerCase().indexOf(q) !== -1; });
        if (match.length > 0 && match[0].id) switchTab(match[0].id);
      });
      toolbar.querySelector('#derez-refresh').addEventListener('click', rescan);

      // Empty state
      if (tabsRef.current.length === 0) {
        var empty = document.createElement('div');
        empty.className = 'company-dash__empty';
        empty.innerHTML = '<div class="company-dash__empty-icon">\u{1F4C4}</div>' +
          '<div class="company-dash__empty-title">No company reports found</div>' +
          '<div class="company-dash__empty-desc">Add markdown files to:<br/><code>company/reports</code></div>';
        el.appendChild(empty);
        return;
      }

      // Find active tab
      var activeId = null;
      var tabs = tabsRef.current;
      for (var i = 0; i < tabs.length; i++) {
        // Determine which tab is active — use the first one if none set
        var isActive = !activeId && i === 0;
        // In a real scenario the active tab comes from the last fetchReport call
        // We track it via reportRef — if reportRef has content, that tab is active
        // For simplicity, we accept whatever was last fetched
      }

      // Tab bar
      var tabBar = document.createElement('div');
      tabBar.className = 'company-dash__tabs';
      var activeTabId = (reportRef.current && reportRef.current._tabId) || (tabs.length > 0 ? tabs[0].id : null);
      tabs.forEach(function (t) {
        var tab = document.createElement('div');
        tab.className = 'company-dash__tab' + (t.id === activeTabId ? ' company-dash__tab--active' : '');
        tab.textContent = t.name;
        tab.addEventListener('click', function () { switchTab(t.id); });
        tabBar.appendChild(tab);
      });
      el.appendChild(tabBar);

      // Body
      var body = document.createElement('div');
      body.className = 'company-dash__body';

      // TOC sidebar
      var headings = headingsRef.current;
      if (headings.length > 1) {
        var toc = document.createElement('nav');
        toc.className = 'company-dash__toc';
        toc.innerHTML = '<div class="company-dash__toc-title">On this page</div>';
        headings.forEach(function (h) {
          var a = document.createElement('a');
          a.className = 'company-dash__toc-item';
          if (h.level >= 3) a.className += ' company-dash__toc-item--h' + h.level;
          a.textContent = h.text;
          a.href = '#' + h.anchor;
          a.addEventListener('click', function (e) {
            e.preventDefault();
            var target = document.getElementById(h.anchor);
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          });
          toc.appendChild(a);
        });
        body.appendChild(toc);
      }

      // Content area
      var content = document.createElement('div');
      content.className = 'company-dash__content';

      if (errorRef.current) {
        content.innerHTML = '<div class="company-dash__error"><strong>Error loading report:</strong> ' + escapeHtml(errorRef.current) + '</div>';
        body.appendChild(content);
        el.appendChild(body);
        return;
      }

      var rc = reportRef.current;
      if (!rc) {
        content.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading...</div>';
        body.appendChild(content);
        el.appendChild(body);
        return;
      }

      // Metrics row
      if (rc.metrics && rc.metrics.length > 0) {
        var metricsRow = document.createElement('div');
        metricsRow.className = 'company-dash__metrics';
        rc.metrics.forEach(function (m) {
          metricsRow.innerHTML += '<div class="company-dash__metric-card">' +
            '<div class="company-dash__metric-label">' + escapeHtml(m.label) + '</div>' +
            '<div class="company-dash__metric-value">' + escapeHtml(m.value) + '</div></div>';
        });
        content.appendChild(metricsRow);
      }

      // Sections
      if (rc.sections) {
        rc.sections.forEach(function (section) {
          if (section.heading) {
            var h = document.createElement('div');
            h.className = 'company-dash__section-heading company-dash__section-heading--h' + (section.level || 2);
            h.textContent = section.heading;
            var anchor = (section.anchor || section.heading.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-'));
            h.id = anchor;
            content.appendChild(h);
          }
          if (section.elements) {
            section.elements.forEach(function (elem) {
              if (elem.type === 'metric') {
                content.innerHTML += '<div class="company-dash__metric-card"><div class="company-dash__metric-label">' +
                  escapeHtml(elem.label) + '</div><div class="company-dash__metric-value">' + escapeHtml(elem.value) + '</div></div>';
              } else if (elem.type === 'status') {
                content.innerHTML += '<span class="company-dash__badge company-dash__badge--' + badgeVariant(elem.value || elem.text) + '">' +
                  escapeHtml(elem.text) + '</span>';
              } else if (elem.type === 'callout') {
                content.innerHTML += '<div class="company-dash__callout company-dash__callout--' + (elem.variant || 'note') + '">' +
                  escapeHtml(elem.text) + '</div>';
              } else if (elem.type === 'list_items' && elem.items) {
                var ul = document.createElement('ul');
                ul.className = 'company-dash__list';
                elem.items.forEach(function (item) {
                  var li = document.createElement('li');
                  li.innerHTML = item.html || escapeHtml(item.text);
                  ul.appendChild(li);
                });
                content.appendChild(ul);
              } else if (elem.type === 'text') {
                var p = document.createElement('div');
                p.className = 'company-dash__text';
                p.innerHTML = elem.html || escapeHtml(elem.text);
                content.appendChild(p);
              }
            });
          }
          if ((!section.elements || section.elements.length === 0) && section.body_html) {
            var htmlDiv = document.createElement('div');
            htmlDiv.className = 'company-dash__text';
            htmlDiv.innerHTML = section.body_html;
            content.appendChild(htmlDiv);
          }
        });
      }
      if ((!rc.sections || rc.sections.length === 0) && rc.raw_html) {
        content.innerHTML += '<div class="company-dash__text">' + rc.raw_html + '</div>';
      }

      body.appendChild(content);
      el.appendChild(body);
    }

    // ── Effects ──
    hooks.useEffect(function () {
      if (rootRef.current) {
        render(rootRef.current);
      }
    }, [tick]);

    hooks.useEffect(function () {
      // Bootstrap on mount
      if (rootRef.current) {
        render(rootRef.current);
        fetchTabs();
      }
    }, []);

    return React.createElement('div', { ref: rootRef, className: 'company-dash' });
  }

  // ── Register with Hermes plugin SDK ─────────────────
  window.__HERMES_PLUGINS__.register('derez-company', CompanyDashboard);
})();