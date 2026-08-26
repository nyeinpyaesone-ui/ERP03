import type { AsyncStorage } from "./AsyncStorage";
/**
 * Creates a new AsyncStorage instance bound to a given database name.
 * @param databaseName - The name of the database to open or create.
 */
export declare function createAsyncStorage(databaseName: string): AsyncStorage;
/**
 * Returns a singleton instance of the legacy (v2) web AsyncStorage implementation.
 *
 * ⚠️ Usage is discouraged. This is provided only as a migration path to v3.
 */
export declare function getLegacyStorage(): AsyncStorage;
//# sourceMappingURL=createAsyncStorage.d.ts.map