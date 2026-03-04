import { invoke } from '@tauri-apps/api/core';

// Union of macOS permission status values returned by the backend checks.
export type PermissionStatusCode =
    | 'granted'
    | 'not_determined'
    | 'denied'
    | 'restricted'
    | 'not_found'
    | 'error'
    | 'unknown';

// Serializable per-permission state returned by Rust.
export interface PermissionState {
    granted: boolean;
    canRequest: boolean;
    status: PermissionStatusCode;
    detail?: string;
}

// Combined status payload consumed by the permissions gate and splash page.
export interface PermissionStatus {
    contacts: PermissionState;
    fullDiskAccess: PermissionState;
    allGranted: boolean;
}

// Reactive in-memory cache of the most recent permission status response.
export const permissionStatus = $state<{ value: PermissionStatus | null }>({ value: null });

// Reactive loading flag used by the splash and layout gate while querying permissions.
export const isPermissionStatusLoading = $state<{ value: boolean }>({ value: false });

// Returns whether either required permission is currently missing.
export function hasMissingRequiredPermissions(status: PermissionStatus | null | undefined): boolean {
    if (!status) {
        return true;
    }
    return !status.contacts.granted || !status.fullDiskAccess.granted;
}

// Refreshes required permission status from the native backend and updates shared state.
export async function refreshPermissionStatus(): Promise<PermissionStatus> {
    isPermissionStatusLoading.value = true;
    try {
        const status = await invoke<PermissionStatus>('get_permissions_status');
        permissionStatus.value = status;
        return status;
    } finally {
        isPermissionStatusLoading.value = false;
    }
}

// Requests Contacts permission through the native backend and stores updated status.
export async function requestContactsPermission(): Promise<PermissionStatus> {
    isPermissionStatusLoading.value = true;
    try {
        const status = await invoke<PermissionStatus>('request_contacts_permission');
        permissionStatus.value = status;
        return status;
    } finally {
        isPermissionStatusLoading.value = false;
    }
}

// Opens macOS System Settings at the selected permission pane.
export async function openPermissionSettings(permission: 'contacts' | 'full-disk-access') {
    await invoke('open_permissions_settings', { permission });
}
