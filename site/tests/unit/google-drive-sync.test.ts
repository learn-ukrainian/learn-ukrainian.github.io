import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  getGoogleClientId,
  isGoogleSyncConfigured,
  requestGoogleAccessToken,
  setGoogleClientId,
  setInMemoryAccessToken,
  getInMemoryAccessToken,
} from '../../src/lib/lexicon/google-drive-sync';

describe('google-drive-sync security and configuration', () => {
  beforeEach(() => {
    localStorage.clear();
    setInMemoryAccessToken(null);
  });

  test('isGoogleSyncConfigured returns false when no client ID is present', () => {
    expect(getGoogleClientId()).toBeNull();
    expect(isGoogleSyncConfigured()).toBe(false);
  });

  test('isGoogleSyncConfigured returns true when client ID is configured', () => {
    setGoogleClientId('test-client-id.apps.googleusercontent.com');
    expect(getGoogleClientId()).toBe('test-client-id.apps.googleusercontent.com');
    expect(isGoogleSyncConfigured()).toBe(true);
  });

  test('requestGoogleAccessToken throws without window.prompt when unconfigured', async () => {
    (window as any).prompt = vi.fn();
    await expect(requestGoogleAccessToken()).rejects.toThrow(
      'Google OAuth Client ID не налаштовано для хмарної синхронізації',
    );
    expect((window as any).prompt).not.toHaveBeenCalled();
  });

  test('manages in-memory access token safely', () => {
    expect(getInMemoryAccessToken()).toBeNull();
    setInMemoryAccessToken('mock-access-token');
    expect(getInMemoryAccessToken()).toBe('mock-access-token');
    setInMemoryAccessToken(null);
    expect(getInMemoryAccessToken()).toBeNull();
  });

  test('gracefully handles localStorage denial and security exceptions', () => {
    const denied = vi.fn(() => {
      throw new Error('SecurityError: The operation is insecure.');
    });
    vi.stubGlobal('localStorage', {
      getItem: denied,
      setItem: denied,
      clear: vi.fn(),
      removeItem: denied,
      key: vi.fn(),
      length: 0,
    });
    try {
      expect(() => isGoogleSyncConfigured()).not.toThrow();
      expect(isGoogleSyncConfigured()).toBe(false);
      expect(() => setGoogleClientId('test-id')).not.toThrow();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
