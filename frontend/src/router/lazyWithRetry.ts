import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

const RETRY_KEY = 'mason:route-chunk-retry';

function isDynamicImportError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }

  const message = error.message.toLowerCase();
  return (
    message.includes('failed to fetch dynamically imported module') ||
    message.includes('importing a module script failed') ||
    message.includes('error loading dynamically imported module')
  );
}

export function lazyWithRetry<T extends ComponentType<any>>(
  importer: () => Promise<{ default: T }>,
): LazyExoticComponent<T> {
  return lazy(async () => {
    try {
      const module = await importer();
      if (typeof window !== 'undefined') {
        window.sessionStorage.removeItem(RETRY_KEY);
      }
      return module;
    } catch (error) {
      if (typeof window !== 'undefined' && isDynamicImportError(error)) {
        const retryMarker = window.sessionStorage.getItem(RETRY_KEY);
        const currentUrl = window.location.href;

        if (retryMarker !== currentUrl) {
          window.sessionStorage.setItem(RETRY_KEY, currentUrl);
          window.location.reload();
          return new Promise<never>(() => undefined);
        }

        window.sessionStorage.removeItem(RETRY_KEY);
      }

      throw error;
    }
  });
}
