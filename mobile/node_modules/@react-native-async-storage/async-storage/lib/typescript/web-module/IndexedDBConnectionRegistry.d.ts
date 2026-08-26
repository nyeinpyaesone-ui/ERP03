import type { DBSchema, IDBPDatabase } from "idb";
declare const WebStorageTableName: "entries";
export interface AsyncStorageWeb extends DBSchema {
    [WebStorageTableName]: {
        key: string;
        value: string | null;
    };
}
/**
 * Registry to keep one IndexedDB connection per database name.
 */
declare class IndexedDBConnectionRegistry {
    private registry;
    TableName: "entries";
    getOrCreate(dbName: string): Promise<IDBPDatabase<AsyncStorageWeb>>;
}
declare const _default: IndexedDBConnectionRegistry;
export default _default;
//# sourceMappingURL=IndexedDBConnectionRegistry.d.ts.map