/**
 * Company Reports Dashboard — Hermes dashboard plugin frontend.
 * Loaded as an iframe entry by the Hermes dashboard.
 * Fetches report data from the plugin API and renders with
 * metric cards, badges, callouts, tables, and TOC sidebar.
 */
(function () {
  'use strict';

  const BASE = '/api/plugins/derez-company';

  // --- Inject styles ---
  const style = document.createElement('style');
  style.textContent = `
.company-dash{font-family:var(--hermes-font-family,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif);color:var(--hermes-text-primary,#1a1a2e);background:var(--hermes-bg-primary,#fff);height:100%;display:flex;flex-direction:column;overflow:hidden}
.company-dash__toolbar{display:flex;align-items:center;gap:.5rem;padding:.5rem 1rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}
.company-dash__search{flex:1;padding:.4rem .6rem;border:1px solid var(--hermes-border,#ccc);border-radius:6px;font-size:.875rem;background:var(--hermes-bg-secondary,#f5f5f5);color:inherit}
.company-dash__search:focus{outline:none;border-color:var(--hermes-accent,#4f46e5)}
.company-dash__refresh{padding:.4rem .75rem;border:1px solid var(--hermes-border,#ccc);border-radius:6px;background:var(--hermes-bg-secondary,#f5f5f5);cursor:pointer;font-size:.875rem;color:inherit}
.company-dash__refresh:disabled{opacity:.5}
.company-dash__tabs{display:flex;border-bottom:1px solid var(--hermes-border,#e0e0e0);padding:0 1rem;overflow-x:auto}
.company-dash__tab{padding:.5rem 1rem;cursor:pointer;font-size:.875rem;border-bottom:2px solid transparent;color:var(--hermes-text-secondary,#666);white-space:nowrap;transition:color .15s,border-color .15s}
.company-dash__tab:hover{color:var(--hermes-text-primary,#1a1a2e)}
.company-dash__tab--active{color:var(--hermes-accent,#4f46e5);border-bottom-color:var(--hermes-accent,#4f46e5);font-weight:600}
.company-dash__body{flex:1;display:flex;overflow:hidden}
.company-dash__toc{width:200px;flex-shrink:0;padding:1rem;border-right:1px solid var(--hermes-border,#e0e0e0);overflow-y:auto;display:none;font-size:.8125rem}
@media(min-width:1024px){.company-dash__toc{display:block}}
.company-dash__toc-title{font-size:.6875rem;text-transform:uppercase;letter-spacing:.05em;color:var(--hermes-text-secondary,#666);margin:0 0 .5rem 0}
.company-dash__toc-item{display:block;padding:.2rem 0;padding-left:.5rem;border-left:2px solid transparent;color:var(--hermes-text-secondary,#666);text-decoration:none;cursor:pointer;transition:color .15s,border-color .15s}
.company-dash__toc-item:hover{color:var(--hermes-text-primary,#1a1a2e);border-left-color:var(--hermes-accent,#4f46e5)}
.company-dash__toc-item--h3{padding-left:1.25rem}
.company-dash__toc-item--h4{padding-left:2rem}
.company-dash__content{flex:1;padding:1.5rem;overflow-y:auto}
.company-dash__metrics{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem}
.company-dash__metric-card{flex:1;min-width:160px;padding:1rem;border:1px solid var(--hermes-border,#e0e0e0);border-radius:8px;background:var(--hermes-bg-secondary,#f9fafb)}
.company-dash__metric-label{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--hermes-text-secondary,#666)}
.company-dash__metric-value{font-size:1.5rem;font-weight:700;margin-top:.25rem}
.company-dash__section-heading{margin:1.5rem 0 .75rem 0;font-weight:600}
.company-dash__section-heading--h2{font-size:1.25rem}
.company-dash__section-heading--h3{font-size:1.1rem}
.company-dash__badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.75rem;font-weight:600;text-transform:uppercase;margin:.1rem}
.company-dash__badge--green{background:#dcfce7;color:#166534}
.company-dash__badge--red{background:#fee2e2;color:#991b1b}
.company-dash__badge--yellow{background:#fef3c7;color:#92400e}
.company-dash__badge--blue{background:#e0e7ff;color:#3730a3}
.company-dash__callout{padding:.75rem 1rem;border-radius:6px;margin:.75rem 0;border-left:4px solid;font-size:.875rem}
.company-dash__callout--note{background:#f0f9ff;border-left-color:#0ea5e9}
.company-dash__callout--warning,.company-dash__callout--caution{background:#fffbeb;border-left-color:#f59e0b}
.company-dash__callout--important,.company-dash__callout--danger{background:#fef2f2;border-left-color:#ef4444}
.company-dash__callout--todo,.company-dash__callout--info,.company-dash__callout--tip{background:#f0fdf4;border-left-color:#22c55e}
.company-dash__table{width:100%;border-collapse:collapse;margin:.75rem 0;font-size:.875rem}
.company-dash__table th{text-align:left;padding:.5rem .75rem;border-bottom:2px solid var(--hermes-border,#e0e0e0);font-weight:600}
.company-dash__table td{padding:.4rem .75rem;border-bottom:1px solid var(--hermes-border,#e0e0e0)}
.company-dash__empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666);text-align:center}
.company-dash__empty-icon{font-size:3rem;margin-bottom:1rem;opacity:.4}
.company-dash__loading{display:flex;align-items:center;justify-content:center;padding:4rem;color:var(--hermes-text-secondary,#666)}
.company-dash__error{padding:1.5rem;margin:1rem;border:1px solid #fca5a5;border-radius:8px;background:#fef2f2;color:#991b1b}
.company-dash__spinner{width:24px;height:24px;border:3px solid var(--hermes-border,#e0e0e0);border-top-color:var(--hermes-accent,#4f46e5);border-radius:50%;animation:spin .6s linear infinite;margin-right:.75rem}
@keyframes spin{to{transform:rotate(360deg)}}
.company-dash__text p{margin:.5rem 0;line-height:1.6}
.company-dash__list{margin:.5rem 0;padding-left:1.5rem}
.company-dash__list li{margin:.2rem 0}`;
  document.head.appendChild(style);

  // --- State ---
  let tabs = [];
  let activeTabId = null;
  let reportContent = null;
  let headings = [];
  let loading = true;
  let scanning = false;
  let error = null;

  // --- Helpers ---
  function escapeHtml(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  }

  function badgeVariant(value) {
    var v = (value || '').toLowerCase().replace(/\s+/g, '-');
    var greens = ['active','warm','hot','won','success','complete','approved','done'];
    var reds = ['blocked','delayed','failed','lost','critical','danger','cancelled','rejected','blacklisted'];
    var yellows = ['warning','pending','cold','on-hold','in-progress'];
    if (greens.indexOf(v) !== -1) return 'green';
    if (reds.indexOf(v) !== -1) return 'red';
    if (yellows.indexOf(v) !== -1) return 'yellow';
    return 'blue';
  }

  // --- API ---
  async function fetchTabs() {
    try {
      var res = await fetch(BASE + '/tabs');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      tabs = await res.json();
      loading = false;
      if (tabs.length > 0 && !activeTabId) {
        activeTabId = tabs[0].id;
        fetchReport(activeTabId);
      }
      render();
    } catch (err) {
      loading = false;
      error = err.message;
      render();
    }
  }

  async function fetchReport(tabId) {
    if (!tabId) return;
    try {
      var res = await fetch(BASE + '/report/' + encodeURIComponent(tabId));
      if (!res.ok) {
        var detail = await res.json().catch(function(){return {};});;
        throw new Error(detail.detail || 'HTTP ' + res.status);
      }
      var data = await res.json();
      reportContent = data.content || {};
      fetchTOC(tabId);
      error = null;
    } catch (err) {
      error = err.message;
      reportContent = null;
    }
    render();
  }

  async function fetchTOC(tabId) {
    try {
      var res = await fetch(BASE + '/toc/' + encodeURIComponent(tabId));
      if (res.ok) {
        var data = await res.json();
        headings = data.headings || [];
      }
    } catch (e) { headings = []; }
  }

  async function rescan() {
    scanning = true;
    render();
    try {
      await fetch(BASE + '/scan', { method: 'POST' });
      await fetchTabs();
      if (activeTabId) await fetchReport(activeTabId);
    } catch (e) { /* ignore */ }
    scanning = false;
    render();
  }

  function switchTab(tabId) {
    activeTabId = tabId;
    reportContent = null;
    headings = [];
    fetchReport(tabId);
    render();
  }

  // --- Render ---
  function render() {
    root.innerHTML = '';

    if (loading) {
      root.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading reports...</div>';
      return;
    }

    if (error && tabs.length === 0) {
      root.innerHTML = '<div class="company-dash__error"><strong>Error:</strong> ' + escapeHtml(error) + '</div>';
      return;
    }

    // Toolbar
    var toolbar = document.createElement('div');
    toolbar.className = 'company-dash__toolbar';
    toolbar.innerHTML = '<input class="company-dash__search" type="text" placeholder="Search reports..." id="derez-search" />' +
      '<button class="company-dash__refresh" id="derez-refresh">' + (scanning ? 'Scanning...' : '\u21bb Refresh') + '</button>';
    root.appendChild(toolbar);

    toolbar.querySelector('#derez-search').addEventListener('input', function(e) {
      var q = e.target.value.toLowerCase();
      if (!q) return;
      var match = tabs.filter(function(t) { return t.name.toLowerCase().indexOf(q) !== -1; });
      if (match.length > 0 && match[0].id !== activeTabId) switchTab(match[0].id);
    });
    toolbar.querySelector('#derez-refresh').addEventListener('click', rescan);

    // Empty state
    if (tabs.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'company-dash__empty';
      empty.innerHTML = '<div class="company-dash__empty-icon">\u{1F4C4}</div>' +
        '<div class="company-dash__empty-title">No company reports found</div>' +
        '<div class="company-dash__empty-desc">Add markdown files to:<br/><code>company/reports</code></div>';
      root.appendChild(empty);
      return;
    }

    // Tab bar
    var tabBar = document.createElement('div');
    tabBar.className = 'company-dash__tabs';
    tabs.forEach(function(t) {
      var tab = document.createElement('div');
      tab.className = 'company-dash__tab' + (t.id === activeTabId ? ' company-dash__tab--active' : '');
      tab.textContent = t.name;
      tab.addEventListener('click', function() { switchTab(t.id); });
      tabBar.appendChild(tab);
    });
    root.appendChild(tabBar);

    // Body
    var body = document.createElement('div');
    body.className = 'company-dash__body';

    // TOC sidebar
    if (headings.length > 1) {
      var toc = document.createElement('nav');
      toc.className = 'company-dash__toc';
      toc.innerHTML = '<div class="company-dash__toc-title">On this page</div>';
      headings.forEach(function(h) {
        var a = document.createElement('a');
        a.className = 'company-dash__toc-item';
        if (h.level >= 3) a.className += ' company-dash__toc-item--h' + h.level;
        a.textContent = h.text;
        a.href = '#' + h.anchor;
        a.addEventListener('click', function(e) {
          e.preventDefault();
          var el = document.getElementById(h.anchor);
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        toc.appendChild(a);
      });
      body.appendChild(toc);
    }

    // Content area
    var content = document.createElement('div');
    content.className = 'company-dash__content';

    if (error) {
      content.innerHTML = '<div class="company-dash__error"><strong>Error loading report:</strong> ' + escapeHtml(error) + '</div>';
      body.appendChild(content);
      root.appendChild(body);
      return;
    }

    if (!reportContent) {
      content.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading...</div>';
      body.appendChild(content);
      root.appendChild(body);
      return;
    }

    // Metrics row
    if (reportContent.metrics && reportContent.metrics.length > 0) {
      var metricsRow = document.createElement('div');
      metricsRow.className = 'company-dash__metrics';
      reportContent.metrics.forEach(function(m) {
        metricsRow.innerHTML += '<div class="company-dash__metric-card">' +
          '<div class="company-dash__metric-label">' + escapeHtml(m.label) + '</div>' +
          '<div class="company-dash__metric-value">' + escapeHtml(m.value) + '</div></div>';
      });
      content.appendChild(metricsRow);
    }

    // Sections
    if (reportContent.sections) {
      reportContent.sections.forEach(function(section) {
        // Section heading
        if (section.heading) {
          var h = document.createElement('div');
          h.className = 'company-dash__section-heading company-dash__section-heading--h' + (section.level || 2);
          h.textContent = section.heading;
          var anchor = (section.anchor || section.heading.toLowerCase().replace(/[^a-z0-9\s-]/g,'').replace(/\s+/g,'-'));
          h.id = anchor;
          content.appendChild(h);
        }

        // Elements
        if (section.elements) {
          section.elements.forEach(function(elem) {
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
              elem.items.forEach(function(item) {
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

        // Fallback raw HTML
        if ((!section.elements || section.elements.length === 0) && section.body_html) {
          var htmlDiv = document.createElement('div');
          htmlDiv.className = 'company-dash__text';
          htmlDiv.innerHTML = section.body_html;
          content.appendChild(htmlDiv);
        }
      });
    }

    // Fallback raw HTML if no sections
    if ((!reportContent.sections || reportContent.sections.length === 0) && reportContent.raw_html) {
      content.innerHTML += '<div class="company-dash__text">' + reportContent.raw_html + '</div>';
    }

    body.appendChild(content);
    root.appendChild(body);
  }

  // --- Bootstrap ---
  var root = document.createElement('div');
  root.className = 'company-dash';
  root.innerHTML = '<div class="company-dash__loading"><div class="company-dash__spinner"></div>Loading reports...</div>';
  document.body.appendChild(root);

  fetchTabs();
})();