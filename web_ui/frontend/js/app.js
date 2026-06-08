// Browser entrypoint for the static control center.
// It wires shared helpers, page controllers, navigation, and periodic polling.
import { createApiClient } from './api.js';
import { state, setActivePage } from './state.js';
import * as ui from './ui.js';
import { initDashboardPage } from './pages/dashboard.js';
import { initRuntimePage } from './pages/runtime.js';
import { initProvidersPage } from './pages/providers.js';
import { initProfilesPage } from './pages/profiles.js';
import { initDatasetsPage } from './pages/datasets.js';
import { initBenchmarkPage } from './pages/benchmark.js';
import { initResultsPage } from './pages/results.js';
import { initLogsPage } from './pages/logs.js';
import { initSecretsPage } from './pages/secrets.js';

const api = createApiClient();
const pages = document.querySelectorAll('.page');
const navButtons = document.querySelectorAll('#mainNav button[data-page]');

function showPage(pageId) {
  // Navigation in this app is section-based rather than route-based: one HTML
  // shell, many page controllers that know how to refresh themselves.
  setActivePage(pageId);

  navButtons.forEach((button) => {
    const active = button.dataset.page === pageId;
    button.classList.toggle('active', active);
  });

  pages.forEach((page) => {
    page.classList.toggle('visible', page.id === pageId);
  });

  const controller = controllers[pageId];
  if (controller?.refresh) {
    controller.refresh().catch((error) => {
      ui.toast(`Failed to refresh ${pageId}: ${error.message}`, 'error');
    });
  }
}

const baseContext = {
  api,
  ui,
  state,
  navigate: showPage,
};

// Each page module owns one vertical slice of UI behavior but shares the same
// API client, global state object, and utility helpers.
const controllers = {
  dashboard: initDashboardPage(baseContext),
  runtime: initRuntimePage(baseContext),
  providers: initProvidersPage(baseContext),
  profiles: initProfilesPage(baseContext),
  datasets: initDatasetsPage(baseContext),
  benchmark: initBenchmarkPage(baseContext),
  results: initResultsPage(baseContext),
  logs: initLogsPage(baseContext),
  secrets: initSecretsPage(baseContext),
};

navButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const pageId = button.dataset.page;
    if (!pageId) {
      return;
    }
    showPage(pageId);
  });
});

async function bootstrap() {
  try {
    await api.health();
    ui.patchPulse('gatewayPulse', 'Gateway: online', 'ok');
  } catch (error) {
    ui.patchPulse('gatewayPulse', `Gateway: error`, 'error');
    ui.toast(`Gateway health failed: ${error.message}`, 'error', 5000);
  }

  showPage('dashboard');

  // Poll only the active page to keep the UI fresh without hammering every
  // endpoint at once.
  window.setInterval(async () => {
    try {
      const activeController = controllers[state.activePage];
      if (activeController?.poll) {
        await activeController.poll();
      }
    } catch (error) {
      // Keep polling resilient and avoid spamming toasts every cycle.
      console.warn('Polling error:', error);
    }
  }, 3500);
}

bootstrap().catch((error) => {
  ui.toast(`App initialization failed: ${error.message}`, 'error', 6000);
});
