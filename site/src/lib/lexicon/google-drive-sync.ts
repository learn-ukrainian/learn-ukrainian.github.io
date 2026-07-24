/**
 * Zero-Backend Google Drive AppData Sync Engine.
 * Fetch-only API client against Google Drive API v3 (drive.appdata scope).
 * Zero bundled JS libraries — 0 KB bundle impact. See ADR-015 for design.
 */

import { type CustomSet, readLocalCustomSets, saveLocalCustomSet } from './custom-decks';

export const DRIVE_APPDATA_SCOPE = 'https://www.googleapis.com/auth/drive.appdata';
const DRIVE_FILES_URL = 'https://www.googleapis.com/drive/v3/files';
const DRIVE_UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files';

let _inMemoryAccessToken: string | null = null;

export function setInMemoryAccessToken(token: string | null): void {
  _inMemoryAccessToken = token;
}

export function getInMemoryAccessToken(): string | null {
  return _inMemoryAccessToken;
}

/**
 * Load Google Identity Services SDK script dynamically if not already present.
 */
export function loadGoogleIdentitySdk(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') return resolve();
    if ((window as any).google?.accounts?.oauth2) return resolve();

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Identity Services SDK'));
    document.head.appendChild(script);
  });
}

export function getGoogleClientId(): string | null {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('learn_uk_google_client_id');
    if (stored) return stored;
  }
  if (typeof import.meta !== 'undefined' && import.meta.env?.PUBLIC_GOOGLE_CLIENT_ID) {
    return import.meta.env.PUBLIC_GOOGLE_CLIENT_ID;
  }
  return null;
}

export function setGoogleClientId(clientId: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('learn_uk_google_client_id', clientId.trim());
  }
}

/**
 * Launch official Google Identity Services Token Client OAuth Popup for drive.appdata.
 * Zero manual token prompt — 100% browser popup authentication handled by Google.
 */
export async function requestGoogleAccessToken(
  customClientId?: string
): Promise<string> {
  await loadGoogleIdentitySdk();

  let clientId = customClientId || getGoogleClientId();

  if (!clientId) {
    clientId = prompt(
      'Введіть ваш Google Cloud OAuth Client ID (напр. XXXXX.apps.googleusercontent.com):\n\n' +
      'Для створення безкоштовного Client ID:\n' +
      '1. Перейдіть на https://console.cloud.google.com/apis/credentials\n' +
      '2. Створіть OAuth 2.0 Client ID (Web Application) з походженням http://127.0.0.1:4321'
    );
    if (!clientId) {
      throw new Error('Google OAuth Client ID не вказано');
    }
    setGoogleClientId(clientId);
  }

  return new Promise((resolve, reject) => {
    try {
      const tokenClient = (window as any).google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: DRIVE_APPDATA_SCOPE,
        callback: (response: any) => {
          if (response.error) {
            if (response.error === 'invalid_client') {
              localStorage.removeItem('learn_uk_google_client_id');
            }
            reject(new Error(`Google Auth Error (${response.error}): Перевірте ваш Google OAuth Client ID`));
          } else if (response.access_token) {
            setInMemoryAccessToken(response.access_token);
            resolve(response.access_token);
          } else {
            reject(new Error('No access token returned by Google'));
          }
        },
      });

      tokenClient.requestAccessToken({ prompt: 'consent' });
    } catch (err: any) {
      reject(err);
    }
  });
}

export interface SyncResult {
  success: boolean;
  message: string;
  customSetsSynced: number;
}

/**
 * Perform client-initiated 3-way tombstone merge sync of Custom Decks to Google Drive AppData.
 */
export async function syncCustomSetsToDrive(accessToken: string): Promise<SyncResult> {
  try {
    const headers = { Authorization: `Bearer ${accessToken}` };

    // 1. Search for existing custom_sets.json in appDataFolder
    const searchRes = await fetch(
      `${DRIVE_FILES_URL}?spaces=appDataFolder&q=name%3D%27custom_sets.json%27+and+trashed%3Dfalse`,
      { headers }
    );
    if (!searchRes.ok) {
      throw new Error(`Drive search failed: ${searchRes.status} ${searchRes.statusText}`);
    }

    const searchData = await searchRes.json();
    const existingFile = searchData.files && searchData.files[0];

    let remoteSets: CustomSet[] = [];
    if (existingFile) {
      // Download remote content
      const fileRes = await fetch(`${DRIVE_FILES_URL}/${existingFile.id}?alt=media`, { headers });
      if (fileRes.ok) {
        remoteSets = await fileRes.json();
      }
    }

    // 2. Perform 3-way tombstone merge
    const localSets = readLocalCustomSets();
    const mergedSets = mergeCustomSets3Way(localSets, remoteSets);

    // Save merged sets back to local storage
    for (const set of mergedSets) {
      if (!set.deleted_at) {
        saveLocalCustomSet(set);
      }
    }

    // 3. Upload merged content to Drive appDataFolder
    const contentStr = JSON.stringify(mergedSets, null, 2);
    if (existingFile) {
      // Update file
      await fetch(`${DRIVE_UPLOAD_URL}/${existingFile.id}?uploadType=media`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: contentStr,
      });
    } else {
      // Create new file metadata + media multipart
      const metadata = {
        name: 'custom_sets.json',
        parents: ['appDataFolder'],
      };
      const form = new FormData();
      form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
      form.append('file', new Blob([contentStr], { type: 'application/json' }));

      await fetch(`${DRIVE_UPLOAD_URL}?uploadType=multipart`, {
        method: 'POST',
        headers,
        body: form,
      });
    }

    return {
      success: true,
      message: 'Successfully synced custom decks with Google Drive!',
      customSetsSynced: mergedSets.filter((s) => !s.deleted_at).length,
    };
  } catch (err: any) {
    console.error('Google Drive Sync error:', err);
    return {
      success: false,
      message: err?.message || 'Failed to sync with Google Drive',
      customSetsSynced: 0,
    };
  }
}

/**
 * 3-Way Tombstone Merge for Custom Sets across devices.
 * Uses revision, updated_at timestamps, and deleted_at tombstones.
 */

export function mergeCustomSets3Way(local: CustomSet[], remote: CustomSet[]): CustomSet[] {
  const map = new Map<string, CustomSet>();

  for (const item of [...local, ...remote]) {
    const existing = map.get(item.id);
    if (!existing) {
      map.set(item.id, item);
    } else {
      // Resolve conflict by revision and updated_at
      if ((item.revision || 0) > (existing.revision || 0)) {
        map.set(item.id, item);
      } else if (new Date(item.updated_at).getTime() > new Date(existing.updated_at).getTime()) {
        map.set(item.id, item);
      }
    }
  }

  return Array.from(map.values());
}
