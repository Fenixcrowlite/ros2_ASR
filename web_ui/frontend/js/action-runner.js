// Shared async action runner for browser-side API actions.
export function errorMessage(error) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return String(error || 'Unknown error');
}

export function createActionRunner({
  ui,
  isBusy = () => false,
  setBusy = () => {},
} = {}) {
  return async function runAction(task, { feedbackId = '', errorPrefix = '', onFinally = null } = {}) {
    if (isBusy()) {
      return null;
    }
    setBusy(true);
    try {
      return await task();
    } catch (error) {
      const message = errorMessage(error);
      if (feedbackId) {
        ui.setFeedback(feedbackId, message, 'error');
      }
      if (errorPrefix) {
        ui.toast(`${errorPrefix}: ${message}`, 'error');
      }
      return null;
    } finally {
      if (typeof onFinally === 'function') {
        onFinally();
      }
      setBusy(false);
    }
  };
}
