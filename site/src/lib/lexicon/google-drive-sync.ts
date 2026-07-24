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
