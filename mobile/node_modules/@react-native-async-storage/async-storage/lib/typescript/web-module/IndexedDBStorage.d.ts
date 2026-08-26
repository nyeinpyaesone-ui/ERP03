declare class IndexedDBStorage {
    private dbName;
    constructor(dbName: string);
    getValues: (keys: string[]) => Promise<{
        key: string;
        value: string | null;
    }[]>;
    setValues: (values: {
        key: string;
        value: string | null;
    }[]) => Promise<{
        key: string;
        value: string | null;
    }[]>;
    removeValues: (keys: string[]) => Promise<void>;
    clearStorage: () => Promise<void>;
    getKeys: () => Promise<string[]>;
    private db;
    private createError;
}
export default IndexedDBStorage;
//# sourceMappingURL=IndexedDBStorage.d.ts.map