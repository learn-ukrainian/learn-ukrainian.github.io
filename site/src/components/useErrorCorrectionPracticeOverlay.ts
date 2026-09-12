import { useEffect, useState } from 'react';
import type { ErrorCorrectionDrill } from './ErrorCorrectionPractice';

export async function loadErrorCorrectionDeck(): Promise<ErrorCorrectionDrill[]> {
  const mod = await import('../data/practice-error-corrections.json');
  return mod.default.drills as ErrorCorrectionDrill[];
}

export function useErrorCorrectionPracticeOverlay() {
  const [activeCulturePractice, setActiveCulturePractice] = useState(false);
  const [cultureDrills, setCultureDrills] = useState<ErrorCorrectionDrill[] | null>(null);
  const [cultureLoading, setCultureLoading] = useState(false);
  const [cultureError, setCultureError] = useState(false);
  const [retryToken, setRetryToken] = useState(0);

  useEffect(() => {
    if (!activeCulturePractice) {
      return;
    }
    if (cultureDrills && cultureDrills.length > 0) {
      return;
    }
    let cancelled = false;
    setCultureLoading(true);
    setCultureError(false);
    loadErrorCorrectionDeck()
      .then((drills) => {
        if (!cancelled) {
          setCultureDrills(drills);
          setCultureLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          console.error('[practice] failed to load error-correction drills', err);
          setCultureError(true);
          setCultureLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [activeCulturePractice, retryToken, cultureDrills]);

  return {
    activeCulturePractice,
    setActiveCulturePractice,
    cultureDrills,
    cultureLoading,
    cultureError,
    retryCulturePractice: () => setRetryToken((n) => n + 1),
  };
}
