const BUILD_META_URL = '/build-meta.json';
const BUILD_SYNC_KEY = 'mason:last-build-sync';

async function fetchBuildId(): Promise<string | null> {
  const response = await fetch(`${BUILD_META_URL}?t=${Date.now()}`, {
    cache: 'no-store',
    headers: {
      'Cache-Control': 'no-store',
    },
  });

  if (!response.ok) {
    return null;
  }

  const payload = (await response.json()) as { buildId?: string };
  return payload.buildId ?? null;
}

export function startBuildSync(currentBuildId: string): () => void {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  let stopped = false;

  const syncBuild = async () => {
    if (stopped) {
      return;
    }

    try {
      const latestBuildId = await fetchBuildId();
      if (!latestBuildId || latestBuildId === currentBuildId) {
        return;
      }

      const lastSynced = window.sessionStorage.getItem(BUILD_SYNC_KEY);
      if (lastSynced === latestBuildId) {
        return;
      }

      window.sessionStorage.setItem(BUILD_SYNC_KEY, latestBuildId);
      window.location.reload();
    } catch {
      // Ignore background sync errors and keep the current session usable.
    }
  };

  const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      void syncBuild();
    }
  };

  void syncBuild();
  window.addEventListener('focus', syncBuild);
  document.addEventListener('visibilitychange', handleVisibilityChange);

  return () => {
    stopped = true;
    window.removeEventListener('focus', syncBuild);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
}
