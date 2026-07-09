<template id="company-dashboard">
  <div class="company-dashboard">
    <!-- Loading state -->
    <div v-if="loading" class="company-dashboard__loading">
      <hermes-spinner />
      <p>Loading reports...</p>
    </div>

    <!-- Error state -->
    <hermes-error-panel
      v-else-if="error"
      :title="errorTitle"
      :message="errorMessage"
    >
      <hermes-button v-if="showRetry" @click="rescan">Retry</hermes-button>
    </hermes-error-panel>

    <!-- Empty state -->
    <hermes-empty-state
      v-else-if="tabs.length === 0"
      icon="file-text"
      title="No company reports found"
      description='Add markdown files to:<br/><code>company/reports</code>'
    >
      <hermes-button @click="rescan">Rescan</hermes-button>
    </hermes-empty-state>

    <!-- Dashboard content -->
    <div v-else class="company-dashboard__content">
      <!-- Toolbar -->
      <div class="company-dashboard__toolbar">
        <hermes-search
          v-model="searchQuery"
          placeholder="Search reports..."
          @search="handleSearch"
        />
        <hermes-button
          variant="secondary"
          size="small"
          @click="rescan"
          :disabled="scanning"
        >
          <hermes-icon name="refresh" />
          {{ scanning ? 'Scanning...' : 'Refresh' }}
        </hermes-button>
      </div>

      <!-- Tab navigation -->
      <hermes-tabs
        v-model="activeTab"
        :tabs="tabs"
        @tab-change="handleTabChange"
      />

      <!-- Report content -->
      <div class="company-dashboard__report" v-if="activeTab">
        <!-- Table of Contents sidebar -->
        <aside
          v-if="toc.length > 1"
          class="company-dashboard__toc"
        >
          <h4>On this page</h4>
          <nav>
            <a
              v-for="item in toc"
              :key="item.anchor"
              :href="'#' + item.anchor"
              :class="'toc-level-' + item.level"
              @click.prevent="scrollToAnchor(item.anchor)"
            >
              {{ item.text }}
            </a>
          </nav>
        </aside>

        <!-- Main report body -->
        <main class="company-dashboard__body">
          <!-- Metrics row -->
          <div
            v-if="reportContent.metrics && reportContent.metrics.length > 0"
            class="company-dashboard__metrics"
          >
            <hermes-metric-card
              v-for="(metric, idx) in reportContent.metrics"
              :key="'metric-' + idx"
              :label="metric.label"
              :value="metric.value"
            />
          </div>

          <!-- Render sections -->
          <template v-for="(section, idx) in reportContent.sections">
            <!-- Section heading -->
            <hermes-section-heading
              v-if="section.heading"
              :key="'heading-' + idx"
              :level="section.level || 2"
              :anchor="section.anchor"
            >
              {{ section.heading }}
            </hermes-section-heading>

            <!-- Render enhanced elements -->
            <template v-for="(elem, eidx) in section.elements">
              <!-- Metric cards -->
              <hermes-metric-card
                v-if="elem.type === 'metric'"
                :key="'elem-' + idx + '-' + eidx"
                :label="elem.label"
                :value="elem.value"
              />

              <!-- Status badges -->
              <hermes-badge
                v-else-if="elem.type === 'status'"
                :key="'elem-' + idx + '-' + eidx"
                :variant="elem.value"
              >
                {{ elem.text }}
              </hermes-badge>

              <!-- Callout alerts -->
              <hermes-callout
                v-else-if="elem.type === 'callout'"
                :key="'elem-' + idx + '-' + eidx"
                :variant="elem.variant"
              >
                <hermes-text>{{ elem.text }}</hermes-text>
              </hermes-callout>

              <!-- List items -->
              <hermes-list
                v-else-if="elem.type === 'list_items'"
                :key="'elem-' + idx + '-' + eidx"
              >
                <hermes-list-item
                  v-for="(item, iidx) in elem.items"
                  :key="'item-' + iidx"
                >
                  <hermes-text v-html="item.html || item.text" />
                </hermes-list-item>
              </hermes-list>

              <!-- Text blocks -->
              <hermes-text-block
                v-else-if="elem.type === 'text'"
                :key="'elem-' + idx + '-' + eidx"
                v-html="elem.html || elem.text"
              />
            </template>

            <!-- Fallback: raw HTML if no elements parsed -->
            <hermes-html
              v-if="(!section.elements || section.elements.length === 0) && section.fallback_html"
              :key="'fallback-' + idx"
              :content="section.fallback_html"
            />
          </template>

          <!-- Fallback: raw HTML if no sections -->
          <hermes-html
            v-if="(!reportContent.sections || reportContent.sections.length === 0) && reportContent.raw_html"
            :content="reportContent.raw_html"
          />
        </main>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';

export default {
  name: 'CompanyDashboard',
  props: {
    initialTab: {
      type: String,
      default: null,
    },
  },
  setup(props) {
    const loading = ref(true);
    const error = ref(false);
    const errorTitle = ref('');
    const errorMessage = ref('');
    const showRetry = ref(false);
    const scanning = ref(false);
    const searchQuery = ref('');
    const activeTab = ref(props.initialTab);
    const tabs = ref([]);
    const reportContent = ref({});
    const toc = ref([]);

    // Fetch the list of tabs from the API
    async function fetchTabs() {
      try {
        const response = await fetch(
          '/api/plugins/company-dashboard/tabs'
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        tabs.value = (data.tabs || []).map((t) => ({
          id: t.id,
          label: t.name,
          route: t.url,
        }));

        // Auto-select first tab if none selected
        if (tabs.value.length > 0 && !activeTab.value) {
          activeTab.value = tabs.value[0].id;
        }

        loading.value = false;
      } catch (err) {
        loading.value = false;
        error.value = true;
        errorTitle.value = 'Failed to load reports';
        errorMessage.value = err.message || 'Unknown error';
      }
    }

    // Fetch the content for a specific tab
    async function fetchReport(tabId) {
      if (!tabId) return;
      try {
        const response = await fetch(
          `/api/plugins/company-dashboard/report/${tabId}`
        );
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(
            data.message || `HTTP ${response.status}`
          );
        }
        const data = await response.json();
        reportContent.value = data.content || {};

        // Determine if it's an error response
        if (data.error) {
          error.value = true;
          errorTitle.value = 'Error loading report';
          errorMessage.value = data.message || 'Unknown error';
          showRetry.value = data.retry || false;
        } else {
          error.value = false;
          showRetry.value = false;
        }

        // Fetch TOC
        fetchTOC(tabId);
      } catch (err) {
        error.value = true;
        errorTitle.value = 'Failed to load report';
        errorMessage.value = err.message || 'Unknown error';
        showRetry.value = true;
      }
    }

    // Fetch table of contents for a tab
    async function fetchTOC(tabId) {
      try {
        const response = await fetch(
          `/api/plugins/company-dashboard/toc/${tabId}`
        );
        if (response.ok) {
          const data = await response.json();
          toc.value = data.headings || [];
        }
      } catch (err) {
        toc.value = [];
      }
    }

    // Rescan the reports directory
    async function rescan() {
      scanning.value = true;
      try {
        await fetch('/api/plugins/company-dashboard/scan', {
          method: 'POST',
        });
        await fetchTabs();
        if (activeTab.value) {
          await fetchReport(activeTab.value);
        }
      } catch (err) {
        console.error('Rescan failed:', err);
      } finally {
        scanning.value = false;
      }
    }

    // Handle tab change
    async function handleTabChange(tabId) {
      activeTab.value = tabId;
      await fetchReport(tabId);
    }

    // Handle search across reports
    function handleSearch(query) {
      searchQuery.value = query;
      if (!query) {
        return;
      }
      // Filter tabs by name match
      const lower = query.toLowerCase();
      const filtered = tabs.value.filter((t) =>
        t.label.toLowerCase().includes(lower)
      );
      if (filtered.length > 0) {
        handleTabChange(filtered[0].id);
      }
    }

    // Scroll to anchor heading
    function scrollToAnchor(anchor) {
      const el = document.getElementById(anchor);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    // Watch for route changes (deep linking)
    watch(
      () => props.initialTab,
      (newTab) => {
        if (newTab && newTab !== activeTab.value) {
          activeTab.value = newTab;
          fetchReport(newTab);
        }
      }
    );

    onMounted(() => {
      fetchTabs();
    });

    return {
      loading,
      error,
      errorTitle,
      errorMessage,
      showRetry,
      scanning,
      searchQuery,
      activeTab,
      tabs,
      reportContent,
      toc,
      rescan,
      handleTabChange,
      handleSearch,
      scrollToAnchor,
      fetchReport,
    };
  },
};
</script>

<style scoped>
.company-dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.company-dashboard__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
  color: var(--hermes-text-secondary);
}

.company-dashboard__toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--hermes-border);
}

.company-dashboard__toolbar > hermes-search {
  flex: 1;
}

.company-dashboard__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.company-dashboard__report {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.company-dashboard__toc {
  width: 220px;
  flex-shrink: 0;
  padding: 1rem;
  border-right: 1px solid var(--hermes-border);
  overflow-y: auto;
  display: none;
}

@media (min-width: 1024px) {
  .company-dashboard__toc {
    display: block;
  }
}

.company-dashboard__toc h4 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--hermes-text-secondary);
  margin: 0 0 0.75rem 0;
}

.company-dashboard__toc nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.company-dashboard__toc nav a {
  color: var(--hermes-text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  padding: 0.25rem 0;
  border-left: 2px solid transparent;
  padding-left: 0.75rem;
  transition: color 0.15s, border-color 0.15s;
}

.company-dashboard__toc nav a:hover {
  color: var(--hermes-text-primary);
  border-left-color: var(--hermes-accent);
}

.company-dashboard__toc nav a.toc-level-3 {
  padding-left: 1.5rem;
}

.company-dashboard__toc nav a.toc-level-4 {
  padding-left: 2.25rem;
}

.company-dashboard__body {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.company-dashboard__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.company-dashboard__metrics > * {
  flex: 1;
  min-width: 180px;
}
</style>