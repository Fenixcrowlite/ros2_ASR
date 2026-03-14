export const state = {
  activePage: 'dashboard',
  runtime: {
    status: null,
    live: null,
    lastRunId: '',
  },
  benchmark: {
    activeRunId: '',
    history: [],
  },
  profiles: {
    currentType: 'runtime',
    currentId: '',
    currentPayload: null,
  },
  results: {
    lastComparison: null,
  },
};

export function setActivePage(pageId) {
  state.activePage = pageId;
}
