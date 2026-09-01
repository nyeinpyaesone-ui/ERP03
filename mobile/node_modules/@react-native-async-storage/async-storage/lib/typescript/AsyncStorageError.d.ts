declare enum AsyncStorageErrorType {
    /**
     * Related to RN Native module itself, ex. not initialized or null at app boot
     */
    NativeModuleError = "NativeModuleError",
    /**
     * Related to web storage (indexedDB)
     * https://developer.mozilla.org/en-US/docs/Web/API/IDBRequest/error
     */
    WebStorageError = "WebStorageError",
    /**
     * Error thrown from Sqlite itself
     * https://www.sqlite.org/rescode.html
     */
    SqliteStorageError = "SqliteStorageError",
    /**
     * Other errors related to Native Shared Storage or Legacy Storage exception.
     * ex. Storage could not be initialized or wrongly formatted output is generated
     */
    OtherStorageError = "OtherStorageError",
    /**
     * Catch-all case, where we can't really tell what went wrong
     */
    UnknownError = "UnknownError"
}
export declare class AsyncStorageError extends Error {
    errorMessage: string;
    type: AsyncStorageErrorType;
    private constructor();
    static nativeError(e: unknown): AsyncStorageError;
    static jsError(error: string, type: AsyncStorageErrorType): AsyncStorageError;
    static Type: typeof AsyncStorageErrorType;
}
export {};
//# sourceMappingURL=AsyncStorageError.d.ts.map