/**
 * Company Reports Dashboard — Hermes dashboard plugin frontend.
 *
 * Registered as a React component via the Hermes plugin SDK.
 * Discovers report HTML/MD files and renders their HTML content
 * directly into the dashboard panel.
 */
(function () {
  'use strict';

  var React = window.__HERMES_PLUGIN_SDK__.React;
  var hooks = window.__HERMES_PLUGIN_SDK__.hooks;

  var BASE = '/api/plugins/derez-company';

  // ── Minimal styles (theme-dependent, no search bar) ──
  var STYLE_TEXT =
    '.company-dash{font-family:var(--hermes-font-family,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif);color:var(--hermes-text-primary,#1a1a2e);background:var(--hermes-bg-primary,#fff);height:100%;display:flex;flex-direction:column;overflow:hidden}' +
    '.company-dash__toolbar{display:flex;align-items:center;gap:.5rem;padding:.5rem 1rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}' +
    '.company-dash__refresh{padding:.4rem .75rem;border:1px solid var(--hermes-border,#ccc);border-radius:6px;background:var(--hermes-bg-secondary,#f5f5f5);cursor:pointer;font-size:.875rem;color:inherit;margin-left:auto}' +
    '.company-dash__refresh:disabled{opacity:.5}' +
    '.company-dash__tabs{display:flex;border-bottom:1px solid var(--hermes-border,#e0e0e0);padding:0 1rem;overflow-x:auto}' +
    '.company-dash__tab{padding:.5rem 1rem;cursor:pointer;font-size:.875rem;border-bottom:2px solid transparent;color:var(--hermes-text-secondary,#666);white-space:nowrap;transition:color .15s,border-color .15s}' +
    '.company-dash__tab:hover{color:var(--hermes-text-primary,#1a1a2e)}' +
    '.company-dash__tab--active{color:var(--hermes-accent,#4f46e5);border-bottom-color:var(--hermes-accent,#4f46e5);font-weight:600}' +
    '.company-dash__body{flex:1;display:flex;overflow:hidden}' +
    '.company-dash__content{flex:1;padding:1.5rem;overflow-y:auto}' +
    '.company-dash__empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666);text-align:center}' +
    '.company-dash__empty-icon{font-size:3rem;margin-bottom:1rem;opacity:.4}' +
    '.company-dash__loading{display:flex;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666)}' +
    '.company-dash__error{padding:1.5rem;margin:1rem;border:1px solid #fca5a5;border-radius:8px;background:#fef2f2;color:#991b1b}' +
    '.company-dash__spinner{width:24px;height:24px;border:3px solid var(--hermes-border,#e0e0e0);border-top-color:var(--hermes-accent,#4f46e5);border-radius:50%;animation:spin .6s linear infinite;margin-right:.75rem}' +
    '@keyframes spin{to{transform:rotate(360deg)}}' +
    /* HTML report content gets wrapped in this class */
    '.company-dash__report h1{font-size:1.5rem;font-weight:700;margin:0 0 .75rem 0;color:var(--hermes-text-primary,#1a1a2e)}' +
    '.company-dash__report h2{font-size:1.2rem;font-weight:600;margin:1.25rem 0 .5rem 0;padding-bottom:.25rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}' +
    '.company-dash__report h3{font-size:1.05rem;font-weight:600;margin:1rem 0 .25rem 0}' +
    '.company-dash__report p{margin:.4rem 0;line-height:1.6}' +
    '.company-dash__report table{width:100%;border-collapse:collapse;margin:.75rem 0;font-size:.875rem}' +
    '.company-dash__report th{text-align:left;padding:.5rem .75rem;border-bottom:2px solid var(--hermes-border,#e0e0e0);font-weight:600}' +
    '.company-dash__report td{padding:.4rem .75rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}' +
    '.company-dash__report ul,.company-dash__report ol{margin:.4rem 0;padding-left:1.5rem}' +
    '.company-dash__report li{margin:.2rem 0}' +
    '.company-dash__report code{font-size:.85em;padding:.1em .35em;border-radius:4px;background:var(--hermes-bg-secondary,#f5f5f5)}' +
    '.company-dash__report pre{overflow-x:auto;padding:.75rem;border-radius:6px;background:var(--hermes-bg-secondary,#f5f5f5);font-size:.85rem}' +
    '.company-dash__report blockquote{padding:.5rem 1rem;margin:.75rem 0;border-left:4px solid var(--hermes-accent,#4f46e5);background:var(--hermes-bg-secondary,#f9fafb);border-radius:4px}' +
    '.company-dash__report a{color:var(--hermes-accent,#4f46e5);text-decoration:underline}' +
    '.company-dash__report hr{border:none;border-top:1px solid var(--hermes-border,#e0e0e0);margin:1.25rem 0}';

  // Inject styles once at module level
  (function () {
    var s = document.createElement('style');
    s.textContent = STYLE_TEXT;
    document.head.appendChild(s);
  })();

  // ── Helpers ──
  function escapeAttr(str) {
    if (!str) return '';
    return String(str).replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── React Component ──────────────────────────────────
  function CompanyDashboard() {
    var rootRef = hooks.useRef(null);
    var tabsRef = hooks.useRef([]);
    var htmlContentRef = hooks.useRef('');
    var headingsRef = hooks.useRef([]);

    var loadingRef = hooks.useRef(true);
    var scanningRef = hooks.useRef(false);
    var errorRef = hooks.useRef(null);
    var activeTabIdRef = hooks.useRef(null);

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
            var firstId = list[0].id;
            activeTabIdRef.current = firstId;
            fetchReport(firstId);
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
      if (!tabId) return;
      fetch(BASE + '/report/' + encodeURIComponent(tabId))
        .then(function (res) {
          if (!res.ok) return res.json().then(function (d) { throw new Error((d && d.detail) || 'HTTP ' + res.status); });
          return res.json();
        })
        .then(function (data) {
          activeTabIdRef.current = tabId;
          // Prefer HTML content, fall back to rendered markdown
          htmlContentRef.current = (data.content && data.content.html) || (data.content && data.content.raw_html) || '';
          headingsRef.current = (data.content && data.content.headings) || [];
          errorRef.current = null;
          bump();
        })
        .catch(function (err) {
          errorRef.current = err.message;
          htmlContentRef.current = '';
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
      htmlContentRef.current = '';
      headingsRef.current = [];
      errorRef.current = null;
      activeTabIdRef.current = tabId;
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
        el.innerHTML = '<div class="company-dash__error"><strong>Error:</strong> ' + escapeAttr(errorRef.current) + '</div>';
        return;
      }

      // Toolbar — only refresh button
      var toolbar = document.createElement('div');
      toolbar.className = 'company-dash__toolbar';
      var title = document.createElement('span');
      title.style.cssText = 'font-size:.875rem;font-weight:600;color:var(--hermes-text-primary,#1a1a2e)';
      title.textContent = 'Company Reports';
      toolbar.appendChild(title);
      var refreshBtn = document.createElement('button');
      refreshBtn.className = 'company-dash__refresh';
      refreshBtn.textContent = scanningRef.current ? 'Scanning...' : '\u21bb Refresh';
      refreshBtn.disabled = scanningRef.current;
      refreshBtn.addEventListener('click', rescan);
      toolbar.appendChild(refreshBtn);
      el.appendChild(toolbar);

      // Empty state
      if (tabsRef.current.length === 0) {
        var empty = document.createElement('div');
        empty.className = 'company-dash__empty';
        empty.innerHTML = '<div class="company-dash__empty-icon">\u{1F4C4}</div>' +
          '<div class="company-dash__empty-title">No company reports found</div>' +
          '<div class="company-dash__empty-desc">Add HTML files to:<br/><code>~/company/reports/</code></div>';
        el.appendChild(empty);
        return;
      }

      // Tab bar
      var tabs = tabsRef.current;
      var activeId = activeTabIdRef.current || (tabs.length > 0 ? tabs[0].id : null);
      var tabBar = document.createElement('div');
      tabBar.className = 'company-dash__tabs';
      tabs.forEach(function (t) {
        var tab = document.createElement('div');
        tab.className = 'company-dash__tab' + (t.id === activeId ? ' company-dash__tab--active' : '');
        tab.textContent = t.name;
        tab.addEventListener('click', function () { switchTab(t.id); });
        tabBar.appendChild(tab);
      });
      el.appendChild(tabBar);

      // Content area
      var body = document.createElement('div');
      body.className = 'company-dash__body';
      var content = document.createElement('div');
      content.className = 'company-dash__content';

      if (errorRef.current) {
        content.innerHTML = '<div class="company-dash__error"><strong>Error loading report:</strong> ' + escapeAttr(errorRef.current) + '</div>';
        body.appendChild(content);
        el.appendChild(body);
        return;
      }

      var html = htmlContentRef.current;
      if (!html) {
        content.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading...</div>';
        body.appendChild(content);
        el.appendChild(body);
        return;
      }

      // Render the HTML content directly
      var reportDiv = document.createElement('div');
      reportDiv.className = 'company-dash__report';
      reportDiv.innerHTML = html;
      content.appendChild(reportDiv);
      body.appendChild(content);
      el.appendChild(body);
    }

    // ── Effects ──
    hooks.useEffect(function () {
      if (rootRef.current) render(rootRef.current);
    }, [tick]);

    hooks.useEffect(function () {
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