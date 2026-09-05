/**
 * IndexedDB durable store for the §10.1 ReviewEvent log.
 *
 * Spec §1 / §10.1: move off localStorage when the log can exceed a few MB.
 * Vanilla IDB only — no auth, host, or vendor SDK. Overflow / trim policy lives
 * in `review-events.ts` so this module stays free of a circular import.
 */

export const REVIEW_EVENTS_IDB_NAME = 'lu-practice-review-events';
export const REVIEW_EVENTS_IDB_VERSION = 1;
export const REVIEW_EVENTS_IDB_STORE = 'log';
export const REVIEW_EVENTS_IDB_RECORD_KEY = 'current';

/** Soft cap: keep the newest N events when trimming for overflow. */
export const REVIEW_EVENTS_MAX_RETAINED = 20_000;
/** Floor while binary-shrinking on repeated quota failures. */
export const REVIEW_EVENTS_MIN_RETAINED = 100;

export interface ReviewEventIdbDriver {
  getRaw(): Promise<unknown | null>;
  setRaw(value: unknown): Promise<void>;
  clear(): Promise<void>;
}

export function isReviewEventQuotaError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const candidate = error as { name?: unknown; code?: unknown; message?: unknown };
  const name = typeof candidate.name === 'string' ? candidate.name : '';
  if (
    name === 'QuotaExceededError' ||
    name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
    name === 'AbortError'
  ) {
    return true;
  }
  if (candidate.code === 22 || candidate.code === 1014) return true;
  const message = typeof candidate.message === 'string' ? candidate.message.toLowerCase() : '';
  return message.includes('quota') || message.includes('exceeded');
}

export function idbAvailable(): boolean {
  try {
    return typeof indexedDB !== 'undefined' && indexedDB !== null;
  } catch {
    return false;
  }
}

function openDatabase(name: string = REVIEW_EVENTS_IDB_NAME): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, REVIEW_EVENTS_IDB_VERSION);
    request.onerror = () => reject(request.error ?? new Error('indexedDB open failed'));
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(REVIEW_EVENTS_IDB_STORE)) {
        db.createObjectStore(REVIEW_EVENTS_IDB_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
  });
}

function idbRequestToPromise<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('indexedDB request failed'));
  });
}

function transactionDone(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(tx.error ?? new DOMException('Aborted', 'AbortError'));
    tx.onerror = () => reject(tx.error ?? new Error('indexedDB transaction failed'));
  });
}

/** Production IndexedDB driver (vanilla IDB — no vendor SDK). */
export function createBrowserReviewEventIdbDriver(
  dbName: string = REVIEW_EVENTS_IDB_NAME,
): ReviewEventIdbDriver {
  return {
    async getRaw(): Promise<unknown | null> {
      const db = await openDatabase(dbName);
      try {
        const tx = db.transaction(REVIEW_EVENTS_IDB_STORE, 'readonly');
        const store = tx.objectStore(REVIEW_EVENTS_IDB_STORE);
        const raw = await idbRequestToPromise(store.get(REVIEW_EVENTS_IDB_RECORD_KEY));
        await transactionDone(tx);
        return raw ?? null;
      } finally {
        db.close();
      }
    },

    async setRaw(value: unknown): Promise<void> {
      const db = await openDatabase(dbName);
      try {
        const tx = db.transaction(REVIEW_EVENTS_IDB_STORE, 'readwrite');
        const store = tx.objectStore(REVIEW_EVENTS_IDB_STORE);
        store.put(value, REVIEW_EVENTS_IDB_RECORD_KEY);
        await transactionDone(tx);
      } finally {
        db.close();
      }
    },

    async clear(): Promise<void> {
      const db = await openDatabase(dbName);
      try {
        const tx = db.transaction(REVIEW_EVENTS_IDB_STORE, 'readwrite');
        const store = tx.objectStore(REVIEW_EVENTS_IDB_STORE);
        store.delete(REVIEW_EVENTS_IDB_RECORD_KEY);
        await transactionDone(tx);
      } finally {
        db.close();
      }
    },
  };
}

/** In-memory driver for unit tests (happy-dom has no IndexedDB). */
export function createMemoryReviewEventIdbDriver(): ReviewEventIdbDriver & {
  failNextWrites: number;
  failError: Error;
  writes: number;
  raw: unknown | null;
  /** When set, the next `setRaw` waits until `releaseWrite()` before continuing. */
  holdNextWrite(): Promise<void>;
  releaseWrite(): void;
} {
  let holdGate: Promise<void> | null = null;
  let releaseHold: (() => void) | null = null;
  let signalEntered: (() => void) | null = null;

  const driver = {
    failNextWrites: 0,
    failError: new DOMException('The quota has been exceeded.', 'QuotaExceededError'),
    writes: 0,
    raw: null as unknown | null,
    holdNextWrite(): Promise<void> {
      holdGate = new Promise<void>((resolve) => {
        releaseHold = resolve;
      });
      return new Promise<void>((resolve) => {
        signalEntered = resolve;
      });
    },
    releaseWrite(): void {
      const release = releaseHold;
      releaseHold = null;
      holdGate = null;
      release?.();
    },
    async getRaw(): Promise<unknown | null> {
      return driver.raw === null ? null : structuredClone(driver.raw);
    },
    async setRaw(value: unknown): Promise<void> {
      driver.writes += 1;
      const gate = holdGate;
      if (gate) {
        holdGate = null;
        signalEntered?.();
        signalEntered = null;
        await gate;
      }
      if (driver.failNextWrites > 0) {
        driver.failNextWrites -= 1;
        throw driver.failError;
      }
      driver.raw = structuredClone(value);
    },
    async clear(): Promise<void> {
      driver.raw = null;
    },
  };
  return driver;
}
