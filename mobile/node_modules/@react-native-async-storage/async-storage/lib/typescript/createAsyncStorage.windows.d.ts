import type { AsyncStorage } from "./AsyncStorage";
/**
 * Creates an AsyncStorage instance.
 * On Windows, always falls back to legacy storage.
 */
export declare function createAsyncStorage(_: string): AsyncStorage;
/** Returns a singleton instance of the legacy (v2) AsyncStorage implementation. */
export declare function getLegacyStorage(): AsyncStorage;
//# sourceMappingURL=createAsyncStorage.windows.d.ts.map