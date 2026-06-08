// Shared in-browser application state container.
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
    selectedRunId: '',
    lastDetail: null,
    selectedInspector: null,
    explorer: {
      page: 1,
      page_size: 25,
      provider: '',
      preset: '',
      noise: '',
      success: '',
      search: '',
      sort: 'sample_id',
      direction: 'asc',
    },
  },
};

export function setActivePage(pageId) {
  state.activePage = pageId;
}
