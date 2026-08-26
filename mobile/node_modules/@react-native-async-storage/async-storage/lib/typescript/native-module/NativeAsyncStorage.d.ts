import type { TurboModule } from "react-native";
export interface Spec extends TurboModule {
    getValues: (dbName: string, keys: string[]) => Promise<{
        key: string;
        value: string | null;
    }[]>;
    setValues: (dbName: string, values: {
        key: string;
        value: string | null;
    }[]) => Promise<{
        key: string;
        value: string | null;
    }[]>;
    removeValues: (dbName: string, keys: string[]) => Promise<void>;
    getKeys: (dbName: string) => Promise<string[]>;
    clearStorage: (dbName: string) => Promise<void>;
    /**
     * As part of migration to new storage, old implementation is available.
     * But the callback approach is replaced with promises.
     */
    legacy_multiGet: (keys: string[]) => Promise<[string, string][]>;
    legacy_multiSet: (kvPairs: [string, string][]) => Promise<void>;
    legacy_multiRemove: (keys: readonly string[]) => Promise<void>;
    legacy_multiMerge: (kvPairs: [string, string][]) => Promise<void>;
    legacy_getAllKeys: () => Promise<string[]>;
    legacy_clear: () => Promise<void>;
}
declare const _default: Spec | null;
export default _default;
//# sourceMappingURL=NativeAsyncStorage.d.ts.map